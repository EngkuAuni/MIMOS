#!/bin/bash
# Quick start script for Mac Studio M4
# Run this on Mac Studio to start the verification engine

set -e

echo ""
echo "=========================================="
echo "  Quran Verification Engine"
echo "  Mac Studio M4 Edition"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    echo ""
    echo "To start Docker Desktop:"
    echo "  1. Open Applications folder"
    echo "  2. Double-click Docker"
    echo "  3. Wait for Docker icon in menu bar"
    echo ""
    exit 1
fi

echo "[1/5] Checking Apple Metal (MPS) support..."
python3 -c "
import sys
try:
    import torch
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print('      ✓ Apple Metal (MPS) is available!')
        print(f'      PyTorch version: {torch.__version__}')
    else:
        print('      ⚠ MPS not available - will use CPU')
        print('      Consider updating PyTorch')
except ImportError:
    print('      ⚠ PyTorch not installed in system Python')
    print('      Will be installed in Docker container')
" 2>/dev/null || echo "      ℹ PyTorch will be installed in Docker"

echo ""
echo "[2/5] Building Mac Studio optimized Docker image..."
docker-compose -f docker-compose-mac-studio-dev.yml build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi
echo "      ✓ Build successful!"

echo ""
echo "[3/5] Starting container with Metal acceleration..."
docker-compose -f docker-compose-mac-studio-dev.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container!"
    exit 1
fi
echo "      ✓ Container started!"

echo ""
echo "[4/5] Waiting for application to be ready..."
sleep 10

# Get IP addresses
echo ""
echo "[5/5] Getting network information..."
echo "      Local hostname: $(hostname)"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "      Local IP: $LOCAL_IP"

echo ""
echo "=========================================="
echo "  ✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Access the application:"
echo "  - On this Mac Studio:"
echo "    http://localhost:8501"
echo ""
echo "  - From MacBook (same network):"
echo "    http://$(hostname):8501"
echo "    http://$LOCAL_IP:8501"
echo ""
echo "  - From anywhere (SSH tunnel):"
echo "    ssh -L 8501:localhost:8501 $(whoami)@$(hostname)"
echo "    then: http://localhost:8501"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose-mac-studio-dev.yml logs -f"
echo ""
echo "To stop:"
echo "  docker-compose -f docker-compose-mac-studio-dev.yml down"
echo ""
echo "Press Enter to view logs (Ctrl+C to exit)..."
read

docker-compose -f docker-compose-mac-studio-dev.yml logs -f

