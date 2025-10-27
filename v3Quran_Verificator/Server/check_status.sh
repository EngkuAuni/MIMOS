#!/bin/bash
# Quick status check for Mac Studio Quran Verificator

echo "╔════════════════════════════════════════════════╗"
echo "║   Quran Verificator - Status Check            ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Docker status
if docker info > /dev/null 2>&1; then
    echo "✅ Docker:        Running"
else
    echo "❌ Docker:        Not Running"
    echo "   Run: open -a Docker"
    exit 1
fi

# Container status
CONTAINER_STATUS=$(docker ps --filter "name=quran-verifier-mac-studio-dev" --format "{{.Status}}" 2>/dev/null)
if [ -n "$CONTAINER_STATUS" ]; then
    echo "✅ Container:     $CONTAINER_STATUS"
else
    echo "❌ Container:     Not Running"
    echo "   Run: cd /Users/Engku/Downloads/v3quran_verificator/Server && docker-compose -f docker-compose-mac-studio-dev.yml up -d"
    exit 1
fi

# MPS check
MPS_AVAILABLE=$(docker exec quran-verifier-mac-studio-dev python -c "import torch; print(torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False)" 2>/dev/null)
if [ "$MPS_AVAILABLE" == "True" ]; then
    echo "✅ GPU (MPS):     Enabled (Fast mode)"
else
    echo "⚠️  GPU (MPS):     Disabled (CPU mode)"
fi

echo ""
echo "🌐 Access URLs:"
echo "   Local:     http://localhost:8501"
echo "   Network:   http://$(hostname):8501"
echo ""
echo "📊 Quick Actions:"
echo "   Logs:      docker logs quran-verifier-mac-studio-dev -f"
echo "   Restart:   cd Server && docker-compose -f docker-compose-mac-studio-dev.yml restart"
echo "   Stop:      cd Server && docker-compose -f docker-compose-mac-studio-dev.yml down"
echo ""
