import os
import re
import asyncio
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

import memory
import brain
import voice
import system_manager
import mc_manager

try:
    from discord.ext import voice_recv
except ImportError:
    voice_recv = None

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID') # ID del dueño (opcional, para proteger la terminal)
TERMINAL_CHANNEL = os.getenv('TERMINAL_CHANNEL', 'consola-kai') # Nombre o ID del canal de terminal
BOT_NAME = os.getenv('BOT_NAME', 'Kai')

CANAL_BIENVENIDAS_ID = int(os.getenv('CANAL_BIENVENIDAS_ID', '1503248831603675147'))
CANAL_STAFF_ID = int(os.getenv('CANAL_STAFF_ID', '0'))

# Configurar intents para leer mensajes y escuchar miembros
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await memory.init_db()
    print(f"========================================")
    print(f"  [HUMAN BOT] Conectado como: {bot.user.name}")
    print(f"  [ESTADO] Staff furry de 19 años listo")
    print(f"========================================")

@bot.event
async def on_member_join(member):
    if member.bot: return
    canal = bot.get_channel(CANAL_BIENVENIDAS_ID)
    if not canal: return

    async with canal.typing():
        prompt = f"Actúa como staff furry de 19 años. Saluda brevemente en una línea a: {member.display_name}"
        try:
            res = await brain.generate_human_response(prompt=prompt, author_name=member.display_name, history=[], learned_slang=[])
        except Exception:
            res = f"wenaas {member.mention} bienvenido al server!"
    await canal.send(res.replace(member.display_name, member.mention))

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

    # Soporte STT para notas de voz o audios subidos en Discord
    audio_transcription = ""
    if message.attachments:
        for att in message.attachments:
            if att.content_type and any(t in att.content_type for t in ["audio", "ogg", "mp3", "wav", "m4a"]):
                print(f"[STT] Audio/Nota de voz recibida de {message.author.display_name}")
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_audio:
                        await att.save(tmp_audio.name)
                        audio_transcription = voice.speech_to_text(tmp_audio.name)
                        if os.path.exists(tmp_audio.name):
                            os.remove(tmp_audio.name)
                    if audio_transcription:
                        print(f"[STT RESULTADO] '{audio_transcription}'")
                        message.content = f"(audio de voz diciendo: {audio_transcription}) {message.content}".strip()
                except Exception as e:
                    print(f"[STT ERROR] {e}")

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
            
            # Conexión instantánea a voz con soporte de recepción (STT) si voice_recv está instalado
            cls = voice_recv.VoiceRecvClient if voice_recv else discord.VoiceClient
            if message.guild.voice_client:
                if message.guild.voice_client.channel != target_channel:
                    await message.guild.voice_client.move_to(target_channel)
                vc = message.guild.voice_client
            else:
                vc = await target_channel.connect(cls=cls)

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

    # 1. Sistema de Rendimiento (CPU, RAM, Uptime)
    perf_triggers = ["rendimiento", "estado del sistema", "como vas de ram", "que tal vas", "stats", "recursos"]
    if (is_mentioned or name_mentioned) and any(t in content_lower for t in perf_triggers):
        metrics = system_manager.get_system_metrics()
        reply_msg = (
            f"todo bien por acá ando activo desde hace **{metrics['uptime']}**\n"
            f"Uso de RAM: **{metrics['ram_mb']} MB** | CPU: **{metrics['cpu_percent']}%**"
        )
        await message.reply(reply_msg)
        return

    # 2. Sistema de Actualización OTA (Over-The-Air vía GitHub)
    ota_update_triggers = ["actualizate", "actualízate", "update ota", "baja la nueva version", "descarga cambios"]
    ota_check_triggers = ["hay updates", "hay actualización", "hay actualizacion", "checa updates", "revisa updates"]

    if (is_mentioned or name_mentioned) and any(t in content_lower for t in ota_check_triggers):
        info = await system_manager.check_for_updates()
        if info.get("has_update"):
            await message.reply(f"sí bro, hay **{info['commits_behind']}** cambios nuevos en GitHub. Dime `Kai actualízate` si quieres que los aplique.")
        else:
            await message.reply("todo al tiro, ya tengo la última versión de GitHub instalada.")
        return

    if (is_mentioned or name_mentioned) and any(t in content_lower for t in ota_update_triggers):
        await message.reply("va, aplicando actualización OTA desde GitHub, dame un momento...")
        res = await system_manager.apply_ota_update()
        await message.channel.send(res)
        return

    # 3. Consola Remota de Linux (Terminal en Discord)
    # Se activa si el canal se llama 'consola-kai' (o el configurado en TERMINAL_CHANNEL), o si empieza con $sh / $bash / $cmd
    is_terminal_channel = (
        (hasattr(message.channel, 'name') and message.channel.name == TERMINAL_CHANNEL)
        or (str(message.channel.id) == str(TERMINAL_CHANNEL))
    )
    is_cmd_prefix = message.content.startswith("$sh ") or message.content.startswith("$bash ") or message.content.startswith("$ ")

    if is_terminal_channel or is_cmd_prefix:
        # Si está configurado ADMIN_USER_ID, proteger para que solo tú puedas ejecutar comandos
        if ADMIN_USER_ID and str(message.author.id) != str(ADMIN_USER_ID):
            await message.reply("🔒 No tienes permisos de administrador para usar la consola.")
            return

        cmd = message.content
        for prefix in ["$sh ", "$bash ", "$ "]:
            if cmd.startswith(prefix):
                cmd = cmd[len(prefix):]
                break

        cmd = cmd.strip()
        if cmd:
            async with message.channel.typing():
                try:
                    # Forzar salida plana sin códigos ANSI/paginadores interactivos
                    env = os.environ.copy()
                    env["PAGER"] = "cat"
                    env["TERM"] = "dumb"

                    proc = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180.0)
                    raw_out = (stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')).strip()
                    
                    # Limpiar secuencias de escape ANSI tipo [?2004h, etc.
                    output = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\([a-zA-Z]', '', raw_out).strip()
                    
                    if not output:
                        output = "[Comando ejecutado sin salida (código 0)]"
                    
                    # Discord tiene un límite de 2000 caracteres por mensaje
                    if len(output) > 1900:
                        output = output[:1850] + "\n... [Salida truncada por límite de Discord]"

                    await message.reply(f"```bash\n{output}\n```")
                except asyncio.TimeoutError:
                    await message.reply("⏱️ El comando tardó más de 3 minutos y se detuvo por seguridad.")
                except Exception as e:
                    await message.reply(f"❌ Error al ejecutar comando: `{e}`")
            return

    # 4. Módulo de Videojuegos - MINECRAFT (LAN, Mundos Locales y Servidores Oficiales de Microsoft)
    mc_join_triggers = ["entra a minecraft", "metete a minecraft", "caile a minecraft", "juega minecraft", "conéctate a minecraft", "conectate a minecraft"]
    mc_leave_triggers = ["salte de minecraft", "vete de minecraft", "cierra minecraft", "desconéctate de minecraft", "desconectate de minecraft"]

    if (is_mentioned or name_mentioned) and any(t in content_lower for t in mc_leave_triggers):
        res = mc_manager.stop_minecraft_bot()
        await message.reply(res)
        return

    if (is_mentioned or name_mentioned) and any(t in content_lower for t in mc_join_triggers):
        # Extraer IP y puerto si el usuario los escribió en el mensaje
        # Formatos aceptados: 'entra a minecraft en 192.168.1.100', 'entra a minecraft en aternos.me:12345'
        words = content_lower.split()
        target_host = "127.0.0.1"
        target_port = 25565
        auth_mode = "offline" # Por defecto offline (para mundos locales / LAN / Aternos)

        if "microsoft" in content_lower or "premium" in content_lower:
            auth_mode = "microsoft"

        for w in words:
            if "." in w and not w.startswith("<") and not w.startswith("@"):
                if ":" in w:
                    parts = w.split(":")
                    target_host = parts[0]
                    try:
                        target_port = int(parts[1])
                    except ValueError:
                        pass
                else:
                    target_host = w

        resp_msg = await mc_manager.start_minecraft_bot(
            host=target_host,
            port=target_port,
            username="Kai",
            auth=auth_mode
        )
        await message.reply(resp_msg)
        return

    # Si le están hablando directamente
    if is_mentioned or is_reply_to_bot or name_mentioned or isinstance(message.channel, discord.DMChannel):
        guild_id = message.guild.id if message.guild else 0
        slang = await memory.get_learned_slang()
        history = await memory.get_recent_chat_history(guild_id=guild_id, limit=8)

        # Generar respuesta con la IA (incluyendo sistema emocional y crush)
        clean_content = message.clean_content.replace(f"@{bot.user.name}", "").strip()
        response_text = await brain.generate_human_response(
            prompt=clean_content,
            author_name=message.author.display_name,
            history=history,
            learned_slang=slang,
            author_id=str(message.author.id)
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
