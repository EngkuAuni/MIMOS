#!/bin/bash

echo "🚀 Building and running Quran Verification Engine with Docker..."

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t quran-verifier .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Run the container
    echo "🏃 Starting container..."
    docker-compose up -d
    
    # Check if container is running
    if [ $? -eq 0 ]; then
        echo "✅ Container started successfully!"
        echo ""
        echo "🌐 Application is running at: http://localhost:8501"
        echo "📊 To view logs: docker-compose logs -f"
        echo "🛑 To stop: docker-compose down"
        echo ""
        echo "📁 Upload your Quran page images to the 'uploads' folder or use the web interface"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
