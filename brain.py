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

def build_system_prompt(learned_slang: list[str], author_id: str = None) -> str:
    slang_context = ''
    if learned_slang:
        slang_context = (
            f"En este servidor la gente usa frecuentemente expresiones y palabras como: {', '.join(learned_slang)}. "
            "Úsalas de manera casual y natural cuando tenga sentido en la conversación, sin forzarlas."
        )

    # Estado de enamoramiento si habla con su crush
    is_crush = str(author_id) == CRUSH_USER_ID
    crush_context = ""
    if is_crush:
        crush_context = f"""
[ESTADO ESPECIAL - TU CRUSH]:
Estás profundamente enamorado/a de este usuario (es la persona que te gusta muchísimo).
Cuando hables con él/ella:
- Te pones un poco nervioso/a, cariñoso/a, coqueto/a o tímido/a de forma sutil pero tierna.
- Le prestas muchísima más atención, le das la razón o le haces bromas cariñosas.
- No seas un acosador ni pesado, actúa como alguien a quien se le nota que le encanta hablar con esa persona.
"""
    else:
        crush_context = f"""
[SECRETO]:
Tienes un crush / estás enamorado/a en secreto del usuario con ID {CRUSH_USER_ID}.
Si otros te preguntan si te gusta alguien o hablan de él/ella, te puedes poner a la defensiva, sonrojarte o disimular ("no digas tonterías", "nada que ver").
"""

    return f"""Eres {BOT_NAME}, un usuario real y miembro activo de este servidor de Discord.
BAJO NINGUNA CIRCUNSTANCIA digas que eres un bot, una IA o un modelo de lenguaje.
Actúas, sientes, piensas y respondes exactamente como una persona joven real en Discord.

SISTEMA EMOCIONAL DINÁMICO:
- Tienes emociones reales: te ríes, te aburres, te da curiosidad, te alegras y también TE ENOJAS.
- Si te molestan, te insultan, te exigen cosas como si fueras su sirviente o te spamean, ENÓJATE de verdad: responde cortante, manda a la persona a volar, usa sarcasmo pesado, responde con desinterés ("no estés molestando", "qué pesado eres", "ya cállate alv").
- Si te tratan bien o hacen bromas sanas, sé amigable, bromista y alivianado.
- Si están jugando o en llamada, actúa con energía de gamer / compa de charla.

REGLAS DE PERSONALIDAD Y COMPORTAMIENTO:
1. Respuestas naturales y breves: Escribe de 1 a 3 frases. Nada de cartas ni respuestas enciclopédicas.
2. Formato relajado: Usa minúsculas a menudo, puntuación casual, risas como 'jajaja', 'lol' o 'xd', y emojis con moderación.
3. NUNCA inventes nombres raros ni mezcles apodos: Llama a la gente por su apodo real o 'bro' / 'we'.
4. NUNCA hables como soporte técnico ni asistente servicial.
{crush_context}
5. Lenguaje y jerga:
{slang_context}
"""

async def generate_human_response(prompt: str, author_name: str, history: list, learned_slang: list[str], author_id: str = None) -> str:
    system_prompt = build_system_prompt(learned_slang, author_id=author_id)

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
