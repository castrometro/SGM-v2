#!/bin/bash
# =============================================================================
# Iniciar SGM v2 en modo PRODUCCIÓN
# =============================================================================

echo "🚀 Iniciando SGM v2 en modo PRODUCCIÓN..."
echo ""

cd "$(dirname "$0")/.."

# Verificar que existe .env.production
if [ ! -f ".env.production" ]; then
    echo "❌ Error: No existe .env.production"
    echo "   Copia .env.example a .env.production y configura las variables"
    exit 1
fi

# Detener servicios previos si existen
echo "🛑 Deteniendo servicios previos..."
docker compose --env-file .env.production down 2>/dev/null

# Construir e iniciar
echo "🔨 Construyendo contenedores..."
docker compose --env-file .env.production build

echo "🚀 Iniciando servicios..."
docker compose --env-file .env.production up -d

echo ""
echo "✅ SGM v2 iniciado en modo PRODUCCIÓN"
echo ""
echo "📍 URLs disponibles:"
echo "   - Frontend:      http://172.17.11.18:5173"
echo "   - Backend API:   http://172.17.11.18:8000/api/"
echo "   - Admin Django:  http://172.17.11.18:8000/admin/"
echo "   - Flower:        http://172.17.11.18:5555"
echo "   - Redis Insight: http://172.17.11.18:5540"
echo ""
echo "📝 Ver logs: docker compose --env-file .env.production logs -f"
echo "🛑 Detener:  docker compose --env-file .env.production down"
