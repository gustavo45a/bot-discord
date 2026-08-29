#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "==================================================="
echo "  Configurando Discord Human Bot en Termux (Android)"
echo "==================================================="

# 1. Actualizar repositorios e instalar paquetes base del sistema
pkg update -y
pkg install -y python ffmpeg libffi openssl clang make pkg-config libsodium git

# 2. Actualizar pip y wheel
pip install --upgrade pip setuptools wheel

# 3. Instalar PyNaCl y librerias nativas compatibles con Android ARM64
SODIUM_INSTALL=system pip install pynacl

# 4. Instalar dependencias del bot
pip install -r requirements-termux.txt

echo "==================================================="
echo "  Instalación completada con éxito en Termux!"
echo "  Ejecuta './start-termux.sh' para iniciar el bot."
echo "==================================================="
