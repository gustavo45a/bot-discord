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
    """Transcribe un archivo de audio a texto."""
    model = get_whisper_model()
    if not model:
        return ""
    segments, info = model.transcribe(audio_path, language='es', beam_size=1)
    transcription = " ".join([s.text for s in segments]).strip()
    return transcription
