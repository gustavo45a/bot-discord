#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "==================================================="
echo "  Instalando binarios precompilados para Termux"
echo "==================================================="

# 1. Instalar paquetes de sistema y binarios ya compilados (evita compilar Rust/C)
pkg update -y
pkg install -y python python-cryptography python-numpy libsodium ffmpeg git

# 2. Instalar PyNaCl usando la libreria de C del sistema sin aislar entorno
SODIUM_INSTALL=system pip install --no-build-isolation pynacl

# 3. Instalar librerias puras de Python
pip install aiosqlite python-dotenv edge-tts "discord.py[voice]" google-genai openai

echo "==================================================="
echo "  Instalacion completada sin compilar Rust/Maturin!"
echo "==================================================="
