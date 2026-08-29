@echo off
echo =======================================================
echo   Levantando Discord Human Bot con Docker Compose
echo =======================================================

if not exist .env (
    echo [ERROR] No se encontro el archivo .env
    echo Copia .env.example a .env y coloca tus credenciales.
    pause
    exit /b 1
)

docker compose up --build -d
if %errorlevel% equ 0 (
    echo [EXITO] El bot esta corriendo en Docker en segundo plano.
    echo Para ver los logs en vivo, ejecuta: docker compose logs -f
) else (
    echo [ERROR] Hubo un problema al iniciar el contenedor.
)
pause
