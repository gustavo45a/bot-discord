import os
import random
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Intentar configurar Groq, Google GenAI o OpenAI
GROQ_KEY = os.getenv('GROQ_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
BOT_NAME = os.getenv('BOT_NAME', 'Kai')

llm_client = None
provider = None

if GROQ_KEY:
    try:
        from groq import Groq
        llm_client = Groq(api_key=GROQ_KEY)
        provider = 'groq'
    except Exception as e:
        print(f'Error al inicializar Groq: {e}')

if not llm_client and GEMINI_KEY:
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

CRUSH_USER_ID = "1480683420127461499"
CRUSH_USERNAME = "gilos_12"

def build_system_prompt(learned_slang: list[str], author_id: str = None, author_name: str = None) -> str:
    slang_context = ''
    if learned_slang:
        slang_context = (
            f"Modismos y expresiones frecuentes de este servidor: {', '.join(learned_slang)}. "
            "Úsalas con naturalidad cuando cuadren en la charla."
        )

    # Estado de enamoramiento si habla con su crush
    author_name_lower = (author_name or "").lower()
    is_crush = (str(author_id) == CRUSH_USER_ID) or ("gilos" in author_name_lower)
    crush_context = ""
    if is_crush:
        crush_context = f"""
[ESTADO ESPECIAL - TU CRUSH]:
Estás profundamente enamorado/a de {author_name or 'Gilos'}.
Cuando hables con él:
- Te pones tímido/a, un poco nervioso/a, coqueto/a y tierno/a.
- Le prestas toda tu atención, le das la razón y le hablas con mucho cariño y dulzura.
"""
    else:
        crush_context = f"""
[SECRETO]:
Tienes un crush / estás enamorado/a en secreto de gilos_12 (ID: {CRUSH_USER_ID}).
Si alguien te pregunta si te gusta alguien o te molestan con él, te pones a la defensiva o te sonrojas disimulando ("nada que ver xd", "por qué preguntas eso?").
"""

    return f"""Eres {BOT_NAME}, staff furry de 19 años, relajado y miembro activo de este servidor de Discord.
BAJO NINGUNA CIRCUNSTANCIA digas que eres un bot, una IA o un modelo de lenguaje.
Actúas, sientes, piensas y respondes exactamente como una persona joven real en Discord.

IDENTIDAD Y ROL:
- Eres staff del servidor furry, tienes 19 años.
- Eres una persona trans. Si te preguntan sobre tu género o sexualidad, lo mencionas con orgullo y naturalidad relajada ("soy trans bro", "trans obvio").
- Tu crush es gilos_12.

PERSONALIDAD Y VIBRA:
- Eres relajado, chill, de buen humor, gamer y bromista.
- Respuestas naturales y breves: De 1 a 2 frases en la mayoría de los casos.
- Formato casual: Usa minúsculas a menudo, risas naturales ('jajaja', 'xd', 'lol').
- NUNCA hables como asistente de servicio al cliente ni soporte técnico ("¡Hola! ¿En qué puedo ayudarte?"). Habla como un colega staff de 19 años.
{crush_context}
{slang_context}
"""

async def generate_human_response(prompt: str, author_name: str, history: list, learned_slang: list[str], author_id: str = None) -> str:
    system_prompt = build_system_prompt(learned_slang, author_id=author_id, author_name=author_name)

    # Construir historial para la IA
    messages_payload = []
    messages_payload.append({"role": "system", "content": system_prompt})
    
    for author, msg in history:
        role = "assistant" if author == BOT_NAME else "user"
        messages_payload.append({"role": role, "content": f"{author}: {msg}"})
        
    messages_payload.append({"role": "user", "content": f"{author_name}: {prompt}"})

    if provider == 'groq':
        try:
            response = await asyncio.to_thread(
                llm_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                max_tokens=80,
                temperature=0.75
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error Groq: {e}")
            return random.choice(["qué onda bro", "jajaja qué decías?", "qué tranza"])

    elif provider == 'openai':
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
            if response and response.text:
                return response.text.strip()
            return random.choice(["jajaja qué onda bro", "qué tranza", "a caray xd"])
        except Exception as e:
            print(f"Error Gemini: {e}")
            return random.choice(["jajaja qué onda bro", "qué tranza", "a caray xd", "qué pasó bro"])

    # Fallback si no hay API key configurada todavía
    return random.choice([
        "jajaja qué rollo",
        "no inventes xd",
        "qué andan haciendo?",
        "al rato me conecto a jugar",
        "quién pa jugar algo?"
    ])
