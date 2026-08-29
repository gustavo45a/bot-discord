#!/data/data/com.termux/files/usr/bin/bash

echo "Iniciando bot en segundo plano con protección contra suspensión de Android..."
# Evitar que Android suspenda la CPU mientras la pantalla está apagada
termux-wake-lock 2>/dev/null || true

python main.py
