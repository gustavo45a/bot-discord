import os
import asyncio
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

import memory
import brain
import voice

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME = os.getenv('BOT_NAME', 'Carlos')

# Configurar intents para leer mensajes y escuchar miembros
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await memory.init_db()
    print(f"========================================")
    print(f"  [HUMAN BOT] Conectado como: {bot.user.name}")
    print(f"  [ESTADO] Listo para actuar como usuario real")
    print(f"========================================")

async def simulate_human_typing(channel, text: str):
    """Simula el tiempo que tardaría una persona real en escribir un mensaje."""
    # Velocidad promedio: ~30-40 caracteres por segundo + pausa de pensamiento
    words_count = len(text.split())
    # Tiempo base de lectura/pensamiento (1 a 2 segundos)
    think_delay = random.uniform(0.8, 1.8)
    await asyncio.sleep(think_delay)

    # Tiempo de tecleo (entre 1.5s y 4.5s según largo)
    type_duration = min(max(words_count * 0.25, 1.2), 5.0)
    async with channel.typing():
        await asyncio.sleep(type_duration)

@bot.event
async def on_message(message: discord.Message):
    # Ignorar mensajes de bots (incluyendo a sí mismo)
    if message.author.bot:
        return

    # 1. Aprender jerga y guardar en memoria
    if message.guild:
        await memory.record_user_message(
            guild_id=message.guild.id,
            user_id=message.author.id,
            author_name=message.author.display_name,
            content=message.content
        )

    # Detectar si el mensaje es para el bot:
    # - Si lo mencionan directamente (@Bot)
    # - Si responden a un mensaje del bot
    # - Si dicen su nombre
    # - O en canales de voz / privados
    is_mentioned = bot.user in message.mentions
    is_reply_to_bot = (
        message.reference 
        and message.reference.resolved 
        and message.reference.resolved.author.id == bot.user.id
    )
    name_mentioned = BOT_NAME.lower() in message.content.lower()

    # Comandos y frases naturales para canales de voz
    content_lower = message.content.lower().strip()
    print(f"[CHAT] Mensaje recibido de {message.author.name}: '{message.content}'")

    join_voice_triggers = [
        "call", "vc", "llamada", "canal", "voz", "voice",
        "vente", "entra", "unete", "únete", "ven", "metete", "caile", "caele"
    ]
    leave_voice_triggers = [
        "salte", "vete", "desconectate", "desconéctate", "salir"
    ]

    # Detectar si pide unirse (si menciona al bot o su nombre y contiene palabras de llamada/vc/call)
    has_join_intent = any(t in content_lower for t in ["call", "vc", "llamada", "voz", "voice"]) and any(t in content_lower for t in ["entra", "ven", "vente", "metete", "caile", "caele", "unete", "únete", "al", "a la"])
    # O si simplemente dice "vente a llamada", "entra a la call", etc.
    direct_join = any(phrase in content_lower for phrase in ["vente a llamada", "entra a la call", "entra a llamada", "ven a la call", "entra al vc", "ven al vc", "caile a la call"])
    
    is_join_req = has_join_intent or direct_join
    is_leave_req = any(t in content_lower for t in leave_voice_triggers) and any(t in content_lower for t in ["call", "vc", "llamada", "canal", "voz"])

    if (is_mentioned or name_mentioned or is_join_req) and is_join_req:
        print(f"[VOICE] Solicitud para entrar a llamada activada por: {message.author.name}")
        if message.author.voice and message.author.voice.channel:
            target_channel = message.author.voice.channel
            print(f"[VOICE] Conectando instantáneamente a: {target_channel.name} ({target_channel.id})")
            
            # Conexión instantánea sin esperar
            if message.guild.voice_client:
                if message.guild.voice_client.channel != target_channel:
                    await message.guild.voice_client.move_to(target_channel)
                vc = message.guild.voice_client
            else:
                vc = await target_channel.connect()

            # Avisar rápido por texto y saludar por voz sin demoras
            await message.channel.send("ya caí al canal")
            try:
                audio_path = await voice.text_to_speech(f"hola qué onda {message.author.display_name}, qué cuentan?")
                vc.play(discord.FFmpegPCMAudio(audio_path), after=lambda e: os.remove(audio_path) if os.path.exists(audio_path) else None)
            except Exception as e:
                print(f"[VOICE ERROR] Error al reproducir audio de bienvenida: {e}")
            return
        else:
            await message.reply("metete primero a un canal de voz y jalo")
            return

    if (is_mentioned or name_mentioned) and is_leave_req:
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await message.reply("sale bro, al rato")
            return

    # Si le están hablando directamente
    if is_mentioned or is_reply_to_bot or name_mentioned or isinstance(message.channel, discord.DMChannel):
        guild_id = message.guild.id if message.guild else 0
        slang = await memory.get_learned_slang()
        history = await memory.get_recent_chat_history(guild_id=guild_id, limit=8)

        # Generar respuesta con la IA
        clean_content = message.clean_content.replace(f"@{bot.user.name}", "").strip()
        response_text = await brain.generate_human_response(
            prompt=clean_content,
            author_name=message.author.display_name,
            history=history,
            learned_slang=slang
        )

        # Si el bot está en llamada de voz, reproducir la respuesta INMEDIATAMENTE en la llamada
        if message.guild and message.guild.voice_client and message.guild.voice_client.is_connected():
            vc = message.guild.voice_client
            try:
                audio_file = await voice.text_to_speech(response_text)
                if vc.is_playing():
                    vc.stop()
                vc.play(discord.FFmpegPCMAudio(audio_file), after=lambda e: os.remove(audio_file) if os.path.exists(audio_file) else None)
            except Exception as e:
                print(f"[VOICE PLAY ERROR] {e}")

        # Enviar también por texto
        if random.random() < 0.7:
            await message.reply(response_text, mention_author=False)
        else:
            await message.channel.send(response_text)

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("[AVISO] DISCORD_TOKEN no está configurado en el archivo .env")
        print("Copia .env.example a .env y coloca tus tokens para iniciar.")
    else:
        bot.run(DISCORD_TOKEN)
