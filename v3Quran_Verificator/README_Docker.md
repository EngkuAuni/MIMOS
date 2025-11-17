# Quran Verification Engine - Docker Setup

## Quick Start

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

## Application Access

Once running, open your browser and go to:
- **Local URL**: http://localhost:8501
- **Network URL**: http://0.0.0.0:8501

## Docker Configuration

### Dockerfile
- Base: Python 3.9-slim
- System packages: Tesseract OCR, OpenCV dependencies, curl
- Python packages: All requirements from `requirements-docker.txt`
- PyTorch: CPU version for cross-platform compatibility

### docker-compose.yml
- Port mapping: 8501:8501
- Auto-restart: unless-stopped
- Health checks: Every 30s

## Data Persistence (Docker Volumes)

Your Docker setup includes **persistent data storage** using Docker named volumes. All your data will be preserved even when you stop or restart the container.

### What's Persistent

| Volume | Purpose | Content |
|--------|---------|---------|
| `quran_database` | Uthmani Quran database | SQLite DB, KDN compliance files, reference images |
| `quran_models` | AI Models | Fine-tuned QariOCR models (e.g., FT1_QariOCR) |
| `quran_finetuning` | Training Data | QariOCR training datasets, scripts, configs |
| `quran_uploads` | User Uploads | Uploaded Quran page images for verification |
| `quran_reports` | Verification Reports | Generated PDF/JSON reports |

### Volume Manager Tool

Use the included **Volume Manager** tool: `docker_volume_manager.sh`

#### Common Operations

```bash
# List all volumes and their sizes
./docker_volume_manager.sh list

# Backup all data
./docker_volume_manager.sh backup

# Export a volume to local directory
./docker_volume_manager.sh export models

# Import from local directory
./docker_volume_manager.sh import database

# Browse volume contents
./docker_volume_manager.sh browse uploads

# Restore from backup
./docker_volume_manager.sh restore
```

## Management Commands

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

## Performance

- **Memory**: ~2-4GB RAM recommended
- **CPU**: Multi-core recommended for faster OCR processing
- **Storage**: ~5GB for the Docker image + models
- **Startup time**: ~30-60 seconds for first run

## Troubleshooting

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

### Data Not Persisting
```bash
# Verify volumes are mounted
docker inspect v3quran_verificator-quran-verifier-1 | grep -A 10 "Mounts"

# Check docker-compose.yml has volume definitions
cat docker-compose.yml | grep -A 5 "volumes:"
```

### Out of Disk Space
```bash
# Check volume sizes
docker system df -v

# Remove old backups
rm -rf ./docker_backups/old_backup_folder

# Clean Docker system (careful!)
docker system prune -a
```

## Notes

- The first run will take longer as it downloads and builds everything
- Models are cached, so subsequent runs are much faster
- Upload your Quran page images through the web interface
- All processing happens inside the container for consistency
- Use Docker volumes for better I/O performance
- Models are cached in container, no re-download needed

## Data Lifecycle

### What Happens When You...

#### Stop the Container
```bash
docker-compose down
```
- ✅ All data is preserved in volumes
- ✅ Container removed but volumes remain
- ✅ Next `docker-compose up` uses same data

#### Rebuild the Image
```bash
docker-compose build
docker-compose up -d
```
- ✅ All data is preserved
- ✅ Only code changes applied
- ✅ Models and uploads unchanged

#### Remove Volumes (⚠️ Data Loss!)
```bash
docker-compose down -v
```
- ❌ Data is permanently deleted
- ⚠️ Cannot be recovered without backup

---

**Summary:** Your data is safely stored in Docker named volumes and will persist across container restarts. Use the `docker_volume_manager.sh` tool to backup, restore, and manage your data easily.

**Last Updated:** October 23, 2025