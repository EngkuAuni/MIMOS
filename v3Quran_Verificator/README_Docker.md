# 🐳 Quran Verification Engine - Docker Setup

This Docker setup provides a complete, isolated environment for the Quran Verification Engine with proper PyTorch support and all dependencies.

## 🚀 Quick Start

### Option 1: Using the provided script (Recommended)
```bash
./run_docker.sh
```

### Option 2: Manual Docker commands
```bash
# Build the image
docker build -t quran-verifier .

# Run the container
docker-compose up -d
```

## 🌐 Access the Application

Once running, open your browser and go to:
- **Local URL**: http://localhost:8501
- **Network URL**: http://0.0.0.0:8501

## 📁 File Structure

The Docker container mounts the following directories:
- `./database` → `/app/database` (Database files)
- `./models` → `/app/models` (OCR models)
- `./QariOCR_Finetuning` → `/app/QariOCR_Finetuning` (Training data)
- `./uploads` → `/app/uploads` (Upload directory)

## 🔧 Docker Features

### ✅ What's Included
- **Python 3.9** with full PyTorch support
- **QariOCR model** with proper dependencies
- **Tesseract OCR** with Arabic language support
- **All required libraries** pre-installed
- **Consistent environment** across different systems
- **Automatic health checks**

### 🎯 Benefits Over Local Setup
1. **No PyTorch installation issues** - Everything pre-configured
2. **Consistent Python version** - No version conflicts
3. **Proper Arabic OCR** - Tesseract with Arabic language pack
4. **Isolated environment** - No conflicts with system packages
5. **Easy deployment** - Works on any system with Docker

## 🛠️ Management Commands

```bash
# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Rebuild after code changes
docker-compose up --build -d

# Access container shell
docker-compose exec quran-verifier bash
```

## 📊 Performance

- **Memory**: ~2-4GB RAM recommended
- **CPU**: Multi-core recommended for faster OCR processing
- **Storage**: ~5GB for the Docker image + models
- **Startup time**: ~30-60 seconds for first run

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker rmi quran-verifier
docker-compose up --build -d
```

### OCR not working
```bash
# Check if models are loaded
docker-compose exec quran-verifier python -c "from models.qari_ocr import QariOCR; print('OCR loaded successfully')"
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8502:8501"  # Use port 8502 instead
```

## 🎉 Expected Results

With Docker, you should get:
- **Real Arabic text extraction** from Quran page images
- **Proper verse segmentation** (not just numbers)
- **High accuracy OCR** using the QariOCR model
- **Beautiful UI** matching your original screenshot
- **Stable performance** without dependency issues

## 📝 Notes

- The first run will take longer as it downloads and builds everything
- Models are cached, so subsequent runs are much faster
- Upload your Quran page images through the web interface
- All processing happens inside the container for consistency
