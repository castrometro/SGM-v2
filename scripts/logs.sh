#!/bin/bash
# =============================================================================
# Ver logs de SGM v2
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

SERVICE=${2:-""}

if [ -n "$SERVICE" ]; then
    docker compose --env-file $ENV_FILE logs -f $SERVICE
else
    docker compose --env-file $ENV_FILE logs -f
fi
