#!/bin/bash
# =============================================================================
# Detener SGM v2
# =============================================================================

cd "$(dirname "$0")/.."

ENV_FILE=""
if [ -f ".env.local" ] && [ "$1" != "prod" ]; then
    ENV_FILE=".env.local"
elif [ -f ".env.production" ]; then
    ENV_FILE=".env.production"
else
    echo "❌ No se encontró archivo .env"
    exit 1
fi

echo "🛑 Deteniendo SGM v2..."
docker compose --env-file $ENV_FILE down

echo "✅ SGM v2 detenido"
