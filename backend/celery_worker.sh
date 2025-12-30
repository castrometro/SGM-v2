#!/bin/bash

echo "🚀 Iniciando sistema multi-worker de Celery SGM v2..."
echo "📊 Configuración:"
echo "   - Worker Validador: concurrencia 3 (validador_queue)"
echo "   - Worker General: concurrencia 1 (default, celery)"
echo ""

sleep 3

# Función para manejar la terminación limpia
cleanup() {
    echo "🛑 Deteniendo workers..."
    pkill -P $$
    exit 0
}

trap cleanup SIGTERM SIGINT

# Iniciar workers en background
echo "🔧 Iniciando Worker Validador (concurrencia: 3)..."
celery -A config worker -Q validador_queue -c 3 --loglevel=info --hostname=validador@%h &
VALIDADOR_PID=$!

echo "⚙️ Iniciando Worker General (concurrencia: 1)..."
celery -A config worker -Q default,celery -c 1 --loglevel=info --hostname=general@%h &
GENERAL_PID=$!

echo ""
echo "✅ Todos los workers iniciados!"
echo "📈 PIDs: Validador=$VALIDADOR_PID, General=$GENERAL_PID"
echo "🔍 Monitoreando workers... (Ctrl+C para detener)"

# Esperar a que terminen los procesos
wait
