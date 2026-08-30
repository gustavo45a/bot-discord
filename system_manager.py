import os
import sys
import asyncio
import subprocess
import time

try:
    import psutil
except ImportError:
    psutil = None

START_TIME = time.time()

def get_system_metrics() -> dict:
    """Obtiene métricas de uso de RAM, CPU y tiempo activo del bot."""
    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    ram_mb = 0.0
    cpu_percent = 0.0

    if psutil:
        try:
            process = psutil.Process(os.getpid())
            ram_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=None)
        except Exception:
            pass

    return {
        "uptime": uptime_str,
        "ram_mb": round(ram_mb, 1),
        "cpu_percent": round(cpu_percent, 1)
    }

async def check_for_updates() -> dict:
    """Comprueba si hay nuevos commits en GitHub sin aplicar cambios."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "fetch", "origin", "main",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        await proc.communicate()

        diff_proc = await asyncio.create_subprocess_exec(
            "git", "rev-list", "HEAD...origin/main", "--count",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = await diff_proc.communicate()
        count = int(stdout.decode().strip() or 0)

        return {"has_update": count > 0, "commits_behind": count}
    except Exception as e:
        return {"has_update": False, "error": str(e)}

async def apply_ota_update() -> str:
    """Ejecuta git pull y reinicia el proceso del bot de forma transparente."""
    try:
        pull_proc = await asyncio.create_subprocess_exec(
            "git", "pull", "origin", "main",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await pull_proc.communicate()
        output_msg = stdout.decode().strip()
        
        if pull_proc.returncode != 0:
            return f"Error al actualizar: {stderr.decode().strip()}"

        # Programar reinicio limpio del proceso
        asyncio.create_task(_delayed_restart())
        return f"Actualización completada:\n`{output_msg}`\nReiniciando a Kai en 2 segundos..."
    except Exception as e:
        return f"Error en OTA: {e}"

async def _delayed_restart():
    await asyncio.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)
