import os
import asyncio
import tempfile
import edge_tts
from dotenv import load_dotenv

load_dotenv()

# Voz por defecto: es-MX-JorgeNeural (muy humana y casual)
DEFAULT_VOICE = os.getenv('TTS_VOICE', 'es-MX-JorgeNeural')

# Cargar Faster-Whisper solo cuando se requiera para no saturar memoria
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            whisper_model = WhisperModel('base', device='cpu', compute_type='int8')
        except Exception as e:
            print(f"[WHISPER NOT LOADED] No disponible en este entorno: {e}")
            whisper_model = False
    return whisper_model

async def text_to_speech(text: str, voice: str = DEFAULT_VOICE) -> str:
    """Convierte texto a un archivo temporal de audio MP3 usando Edge-TTS."""
    # Limpiar un poco el texto para TTS (quitar enlaces o caracteres raros)
    clean_text = text.replace('xd', 'equis de').replace('lol', 'lol')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
        output_path = tmp_file.name

    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_path)
    return output_path

def speech_to_text(audio_path: str) -> str:
    """Transcribe audio a texto usando API de Gemini / OpenAI o fallback local."""
    gemini_key = os.getenv('GEMINI_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    # 1. Transcripción vía Gemini Audio API (Ultra rápida y precisa)
    if gemini_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type='audio/mp3'),
                    "Transcribe exactamente lo que dice el usuario en este audio en español. Devuelve SOLO el texto transcrito sin introducciones ni comentarios adicionales."
                ]
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[GEMINI STT API ERROR] {e}")

    # 2. Transcripción vía OpenAI Whisper API
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            if transcription and transcription.text:
                return transcription.text.strip()
        except Exception as e:
            print(f"[OPENAI WHISPER API ERROR] {e}")

    # 3. Fallback a Faster-Whisper local
    model = get_whisper_model()
    if model:
        try:
            segments, info = model.transcribe(audio_path, language='es', beam_size=1)
            return " ".join([s.text for s in segments]).strip()
        except Exception as e:
            print(f"[LOCAL WHISPER ERROR] {e}")

    return ""
