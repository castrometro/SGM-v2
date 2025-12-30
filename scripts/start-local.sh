#!/bin/bash
# =============================================================================
# Iniciar SGM v2 en modo LOCAL (desarrollo)
# =============================================================================

echo "🚀 Iniciando SGM v2 en modo LOCAL..."
echo ""

cd "$(dirname "$0")/.."

# Verificar que existe .env.local
if [ ! -f ".env.local" ]; then
    echo "❌ Error: No existe .env.local"
    echo "   Copia .env.example a .env.local y configura las variables"
    exit 1
fi

# Detener servicios previos si existen
echo "🛑 Deteniendo servicios previos..."
docker compose --env-file .env.local down 2>/dev/null

# Construir e iniciar
echo "🔨 Construyendo contenedores..."
docker compose --env-file .env.local build

echo "🚀 Iniciando servicios..."
docker compose --env-file .env.local up -d

echo ""
echo "✅ SGM v2 iniciado en modo LOCAL"
echo ""
echo "�� URLs disponibles:"
echo "   - Frontend:      http://localhost:5173"
echo "   - Backend API:   http://localhost:8000/api/"
echo "   - Admin Django:  http://localhost:8000/admin/"
echo "   - Flower:        http://localhost:5555"
echo "   - Redis Insight: http://localhost:5540"
echo ""
echo "📝 Ver logs: docker compose --env-file .env.local logs -f"
echo "🛑 Detener:  docker compose --env-file .env.local down"
