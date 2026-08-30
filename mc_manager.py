import os
import asyncio
import subprocess

mc_process = None

def is_minecraft_running() -> bool:
    global mc_process
    return mc_process is not None and mc_process.poll() is None

async def start_minecraft_bot(host: str, port: int = 25565, username: str = "Kai", auth: str = "offline") -> str:
    """Inicia el cliente de Minecraft en segundo plano conectado al servidor indicado."""
    global mc_process
    if is_minecraft_running():
        return "⚠️ Kai ya está conectado a un servidor de Minecraft actualmente. Dile que se salga primero con Kai salte de minecraft."

    env = os.environ.copy()
    env["MC_HOST"] = host
    env["MC_PORT"] = str(port)
    env["MC_USERNAME"] = username
    env["MC_AUTH"] = auth

    try:
        mc_process = subprocess.Popen(
            ["node", "mc_bot.js"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return f"🎮 Conectando a Kai al servidor **{host}:{port}** como {username} (Modo: {auth})...\nEn unos segundos spawneará en el mundo."
    except Exception as e:
        return f"❌ Error al arrancar el cliente de Minecraft: {e}"

def stop_minecraft_bot() -> str:
    """Detiene el bot de Minecraft."""
    global mc_process
    if not is_minecraft_running():
        return "Kai no está conectado a ningún servidor de Minecraft en este momento."

    try:
        mc_process.terminate()
        mc_process = None
        return "👋 Kai se ha desconectado del servidor de Minecraft."
    except Exception as e:
        return f"Error al desconectar: {e}"
