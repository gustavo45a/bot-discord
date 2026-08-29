@echo off
echo =======================================================
echo   Iniciando Discord Human Bot (Modo Local)
echo =======================================================

if not exist .venv (
    echo [INFO] Creando entorno virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if not exist .env (
    echo [AVISO] Falta archivo .env. Copiando desde .env.example...
    copy .env.example .env
    echo Por favor edita el archivo .env con tus credenciales y vuelve a ejecutar.
    pause
    exit /b 1
)

python main.py
pause
