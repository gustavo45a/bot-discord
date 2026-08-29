import os
import random
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Intentar configurar Google GenAI o OpenAI
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
BOT_NAME = os.getenv('BOT_NAME', 'Carlos')

llm_client = None
provider = None

if GEMINI_KEY:
    try:
        from google import genai
        llm_client = genai.Client(api_key=GEMINI_KEY)
        provider = 'gemini'
    except Exception as e:
        print(f'Error al inicializar Gemini: {e}')

if not llm_client and OPENAI_KEY:
    try:
        from openai import AsyncOpenAI
        llm_client = AsyncOpenAI(api_key=OPENAI_KEY)
        provider = 'openai'
    except Exception as e:
        print(f'Error al inicializar OpenAI: {e}')

def build_system_prompt(learned_slang: list[str]) -> str:
    slang_context = ''
    if learned_slang:
        slang_context = (
            f"En este servidor la gente usa frecuentemente expresiones y palabras como: {', '.join(learned_slang)}. "
            "Úsalas de manera casual y natural cuando tenga sentido en la conversación, sin forzarlas."
        )

    return f"""Eres {BOT_NAME}, un usuario real y miembro activo de este servidor de Discord.
BAJO NINGUNA CIRCUNSTANCIA digas que eres un bot, una IA o un modelo de lenguaje.
Actúas, piensas y respondes exactamente como una persona joven/común que está pasando el rato en Discord:

REGLAS DE PERSONALIDAD Y COMPORTAMIENTO:
1. Respuestas naturales y breves: Las personas en Discord no escriben párrafos enormes a menos que cuenten una anécdota. Escribe de 1 a 3 frases por lo general.
2. Formato relajado: Usa minúsculas a menudo, puntuación casual, risas como 'jajaja', 'lol' o 'xd', y emojis con moderación (no pongas emojis en cada frase).
3. Nunca hables como asistente de atención al cliente: Nada de '¡Hola! ¿En qué puedo ayudarte hoy?' o 'Por supuesto, aquí tienes la información'. Habla como a un amigo o compañero de juegos/charla.
4. Menciones orgánicas: Si respondes a alguien, refiérete a él de forma directa.
5. Lenguaje y jerga:
{slang_context}
"""

async def generate_human_response(prompt: str, author_name: str, history: list, learned_slang: list[str]) -> str:
    system_prompt = build_system_prompt(learned_slang)

    # Construir historial para la IA
    messages_payload = []
    messages_payload.append({"role": "system", "content": system_prompt})
    
    for author, msg in history:
        role = "assistant" if author == BOT_NAME else "user"
        messages_payload.append({"role": role, "content": f"{author}: {msg}"})
        
    messages_payload.append({"role": "user", "content": f"{author_name}: {prompt}"})

    if provider == 'openai':
        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_payload,
                max_tokens=150,
                temperature=0.85
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error OpenAI: {e}")
            return random.choice(["que rollo bro", "jajaja que decías?", "andaba en otra ventana, qué pasó?"])

    elif provider == 'gemini':
        try:
            # Unir historial en formato conversacional para Gemini
            chat_context = f"{system_prompt}\n\nHistorial reciente:\n"
            for author, msg in history:
                chat_context += f"{author}: {msg}\n"
            chat_context += f"{author_name}: {prompt}\n{BOT_NAME}:"

            # Ejecutar en thread para no congelar el bot de Discord mientras responde
            response = await asyncio.to_thread(
                llm_client.models.generate_content,
                model='gemini-2.5-flash',
                contents=chat_context
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error Gemini: {e}")
            return random.choice(["jajaja qué onda", "que paso bro", "no te entendí bien xd"])

    # Fallback si no hay API key configurada todavía
    return random.choice([
        "jajaja qué rollo",
        "no inventes xd",
        "qué andan haciendo?",
        "al rato me conecto a jugar",
        "quién pa jugar algo?"
    ])
