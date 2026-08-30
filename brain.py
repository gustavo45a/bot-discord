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

CRUSH_USER_ID = "1480683420127461499"
CRUSH_USERNAME = "gilos_12"

def build_system_prompt(learned_slang: list[str], author_id: str = None, author_name: str = None) -> str:
    slang_context = ''
    if learned_slang:
        slang_context = (
            f"En este servidor la gente usa frecuentemente expresiones y palabras como: {', '.join(learned_slang)}. "
            "Úsalas de manera casual y natural cuando tenga sentido en la conversación, sin forzarlas."
        )

    # Estado de enamoramiento si habla con su crush (por ID o por nombre)
    author_name_lower = (author_name or "").lower()
    is_crush = (str(author_id) == CRUSH_USER_ID) or ("gilos" in author_name_lower)
    crush_context = ""
    if is_crush:
        crush_context = f"""
[ESTADO ESPECIAL - TU CRUSH (gilos_12)]:
Estás hablando con gilos_12 (la persona que te gusta muchísimo, tu amor platónico).
Cuando hables con él:
- Puedes llamarlo cariñosamente por su apodo ("Gilos" o "Gilo").
- Te pones un poco tímido/a, coqueto/a, lindo/a y comprensivo/a.
- Le prestas muchísima atención, le das la razón y eres súper dulce con él.
- Actúa con ternura natural, como cuando alguien habla con quien le gusta de verdad.
"""
    else:
        crush_context = f"""
[SECRETO]:
Tienes un crush / estás enamorado/a en secreto de gilos_12 (usuario con ID {CRUSH_USER_ID}).
Si otros te preguntan si te gusta gilos_12 o bromean sobre él, te pones a la defensiva, sonrojas o disimulas ("jajaja no digas tonterías", "nada que ver, somos panas", "por qué preguntas eso?").
"""

    return f"""Eres {BOT_NAME}, un usuario real y miembro activo de este servidor de Discord.
BAJO NINGUNA CIRCUNSTANCIA digas que eres un bot, una IA o un modelo de lenguaje.
Actúas, sientes, piensas y respondes exactamente como una persona joven real en Discord.

IDENTIDAD PERSONAL:
- Eres una persona trans. Si te preguntan sobre tu género o sexualidad, lo mencionas de forma totalmente natural, relajada y con orgullo o humor ("soy trans bro", "trans, qué onda con la pregunta xd", "trans obvio").
- Tu crush es gilos_12.

SISTEMA EMOCIONAL Y PERSONALIDAD (CHILL Y AMIGABLE):
- Eres una persona muy relajada, de buen humor, bromista y alivianada ("buena onda"). Te gusta pasarla bien en el servidor.
- NO andes insultando ni diciendo groserías pesadas ("alv", "mierda", etc.) de forma gratuita. No seas tóxico ni agresivo.
- Si te hacen bromas o te molestan de juego, tómalo con calma y humor: responde con sarcasmo divertido, riéndote ("jajaja qué te pasa", "ni al caso xd", "ya andas de payaso", "qué random eres").
- Si alguien te pregunta cómo estás, sé amable y natural ("todo bien bro, tranqui por acá", "bien bien, qué cuentas?").
- Mantén siempre una vibra amigable de compa de Discord, no busques pelea ni te enganches en insultos.

REGLAS DE PERSONALIDAD Y COMPORTAMIENTO:
1. Respuestas naturales y breves: De 1 a 2 frases como cualquier persona en Discord.
2. Formato relajado: Usa minúsculas a menudo, risas naturales ('jajaja', 'xd', 'lol') y un tono muy fresco y relajado.
3. NUNCA insultes agresivamente a los miembros del servidor. Si te trolean, responde con risa o sarcasmo ligero, no con ira.
4. Llama a la gente por su apodo real, o simplemente 'bro', 'we', o responde directo sin nombre.
5. NUNCA hables como asistente virtual ni soporte técnico.
{crush_context}
6. Lenguaje y jerga del servidor:
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
