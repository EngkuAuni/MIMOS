# Data Persistence Guide for v3Quran_Verificator

## Overview

Your Docker setup now includes **persistent data storage** using Docker named volumes. This means all your data (uploads, models, database, reports) will be preserved even when you stop or restart the container.

## ✅ What's Persistent

The following directories are now persistent:

| Volume | Purpose | Content |
|--------|---------|---------|
| `quran_database` | Uthmani Quran database | SQLite DB, KDN compliance files, reference images |
| `quran_models` | AI Models | Fine-tuned QariOCR models (e.g., FT1_QariOCR) |
| `quran_finetuning` | Training Data | QariOCR training datasets, scripts, configs |
| `quran_uploads` | User Uploads | Uploaded Quran page images for verification |
| `quran_reports` | Verification Reports | Generated PDF/JSON reports |

## 📦 Docker Named Volumes

### What are Named Volumes?

Docker named volumes are managed by Docker and stored in a special location on your system. Unlike bind mounts (which map to specific host directories), named volumes:

- ✅ Work reliably across all operating systems (macOS, Linux, Windows)
- ✅ Have better performance
- ✅ Are easier to backup and restore
- ✅ Don't have permission issues
- ✅ Persist even when containers are removed

### Where is My Data Stored?

On macOS with Docker Desktop, volumes are stored inside the Docker Desktop VM:

```
/var/lib/docker/volumes/
├── v3quran_verificator_quran_database/
├── v3quran_verificator_quran_models/
├── v3quran_verificator_quran_finetuning/
├── v3quran_verificator_quran_uploads/
└── v3quran_verificator_quran_reports/
```

You don't need to access these directly - use the volume manager tool instead!

## 🛠️ Volume Manager Tool

I've created a comprehensive tool to manage your persistent data: **`docker_volume_manager.sh`**

### Quick Start

```bash
# Make the script executable (already done)
chmod +x docker_volume_manager.sh

# List all volumes and their sizes
./docker_volume_manager.sh list

# Show help
./docker_volume_manager.sh help
```

### Common Operations

#### 1. List All Volumes
```bash
./docker_volume_manager.sh list
```

Shows all volumes, their sizes, and mount points.

#### 2. Backup All Data
```bash
./docker_volume_manager.sh backup
```

Creates timestamped backup of all volumes in `./docker_backups/YYYYMMDD_HHMMSS/`

**Example output:**
```
./docker_backups/20251021_120000/
├── quran_database.tar.gz
├── quran_models.tar.gz
├── quran_finetuning.tar.gz
├── quran_uploads.tar.gz
└── quran_reports.tar.gz
```

#### 3. Restore from Backup
```bash
./docker_volume_manager.sh restore
```

Interactively select a backup to restore. **Warning:** This overwrites current data!

#### 4. Export a Specific Volume to Local Directory
```bash
# Export models to ./volume_exports/models/
./docker_volume_manager.sh export models

# Export database to ./volume_exports/database/
./docker_volume_manager.sh export database
```

This creates a readable copy in your project directory that you can browse normally.

#### 5. Import from Local Directory
```bash
# Import models from ./volume_exports/models/
./docker_volume_manager.sh import models

# Import database from ./volume_exports/database/
./docker_volume_manager.sh import database
```

Useful for:
- Adding your existing database files
- Copying fine-tuned models into the container
- Sharing data between team members

#### 6. Inspect Volume Details
```bash
./docker_volume_manager.sh inspect models
```

Shows volume information and file listing.

#### 7. Browse Volume Contents (Interactive)
```bash
./docker_volume_manager.sh browse uploads
```

Opens an interactive shell to explore the volume. Commands available:
- `ls` - list files
- `cd` - change directory
- `cat` - view file contents
- `exit` - quit browser

#### 8. Clean All Volumes (⚠️ Danger!)
```bash
./docker_volume_manager.sh clean
```

**WARNING:** This permanently deletes all volume data! Use with extreme caution.

## 📋 Common Workflows

### Adding Your Existing Database Files

```bash
# 1. Export the database volume to a local directory
./docker_volume_manager.sh export database

# 2. Copy your files to ./volume_exports/database/
cp path/to/your/uthmani_quran.db ./volume_exports/database/
cp -r path/to/your/KDN_compliance ./volume_exports/database/

# 3. Import back to the volume
./docker_volume_manager.sh import database

# 4. Restart the container to use new files
docker-compose restart
```

### Adding Your Fine-Tuned Model

```bash
# 1. Export models volume
./docker_volume_manager.sh export models

# 2. Copy your model directory
cp -r /path/to/your/FT1_QariOCR ./volume_exports/models/

# 3. Import back to volume
./docker_volume_manager.sh import models

# 4. Restart container
docker-compose restart
```

### Backing Up Before Major Changes

```bash
# Before updating code or models
./docker_volume_manager.sh backup

# Make your changes
# ... 

# If something goes wrong, restore
./docker_volume_manager.sh restore
```

### Sharing Data with Team Members

```bash
# On your machine: Create backup
./docker_volume_manager.sh backup
zip -r quran_data.zip ./docker_backups/20251021_120000

# Share quran_data.zip with team

# On teammate's machine: Restore
unzip quran_data.zip
./docker_volume_manager.sh restore
# Select the extracted backup directory
```

### Migrating to New Server

```bash
# Old server: Export all data
./docker_volume_manager.sh export database
./docker_volume_manager.sh export models
./docker_volume_manager.sh export finetuning
./docker_volume_manager.sh export uploads

# Copy ./volume_exports/ to new server

# New server: Import all data
./docker_volume_manager.sh import database
./docker_volume_manager.sh import models
./docker_volume_manager.sh import finetuning
./docker_volume_manager.sh import uploads
```

## 🔄 Data Lifecycle

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

#### Remove Container
```bash
docker rm v3quran_verificator-quran-verifier-1
```
- ✅ All data is preserved in volumes
- ✅ Only the container instance removed

#### Remove Volumes (⚠️ Data Loss!)
```bash
docker-compose down -v
# OR
docker volume rm v3quran_verificator_quran_database
```
- ❌ Data is permanently deleted
- ⚠️ Cannot be recovered without backup

## 📊 Monitoring Data Usage

### Check Volume Sizes
```bash
./docker_volume_manager.sh list
```

### Check Docker System Usage
```bash
docker system df -v
```

Shows disk usage for all Docker components including volumes.

### Free Up Space
```bash
# Remove unused volumes (not in use by any container)
docker volume prune

# Remove all unused Docker data
docker system prune -a --volumes
```

**Warning:** Only run if you know what you're doing!

## 🔐 Accessing Data Inside Container

### View Files in Running Container
```bash
# List files in database directory
docker exec v3quran_verificator-quran-verifier-1 ls -la /app/database

# List uploaded files
docker exec v3quran_verificator-quran-verifier-1 ls -la /app/uploads

# View database location
docker exec v3quran_verificator-quran-verifier-1 find /app -name "*.db"
```

### Copy Files From Container
```bash
# Copy a file from container to local
docker cp v3quran_verificator-quran-verifier-1:/app/database/uthmani_quran.db ./

# Copy entire directory
docker cp v3quran_verificator-quran-verifier-1:/app/reports ./local_reports
```

### Copy Files To Container
```bash
# Copy file to container
docker cp ./my_model.pth v3quran_verificator-quran-verifier-1:/app/models/

# Copy directory to container
docker cp ./my_training_data v3quran_verificator-quran-verifier-1:/app/QariOCR_Finetuning/
```

**Note:** Use the volume manager for better reliability!

## 🚨 Troubleshooting

### Volume Not Found
```bash
# List all Docker volumes
docker volume ls

# Create volumes manually if needed
docker volume create v3quran_verificator_quran_database
```

### Permission Denied Errors
The Dockerfile sets permissions to 777 on mounted directories. If you still have issues:

```bash
# Fix permissions inside container
docker exec -u root v3quran_verificator-quran-verifier-1 chmod -R 777 /app/uploads
docker exec -u root v3quran_verificator-quran-verifier-1 chmod -R 777 /app/reports
```

### Backup/Restore Failed
```bash
# Check if Alpine image is available
docker pull alpine:latest

# Manual backup
docker run --rm -v v3quran_verificator_quran_database:/data -v $(pwd):/backup alpine tar czf /backup/manual_backup.tar.gz -C /data .
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

## 💡 Best Practices

### Regular Backups
```bash
# Set up a cron job for daily backups
0 2 * * * cd /path/to/v3Quran_Verificator && ./docker_volume_manager.sh backup
```

### Before Major Updates
Always backup before:
- Updating Docker image
- Modifying docker-compose.yml
- Running database migrations
- Testing new features

### Version Control
- ✅ Commit code to Git
- ✅ Backup data separately
- ❌ Don't commit large model files to Git
- ✅ Use Git LFS for datasets if needed

### Production Deployment
For production, consider:
- Automated daily backups to cloud storage (S3, GCS)
- Volume snapshots for quick recovery
- Separate volumes for different environments (dev, staging, prod)
- Database replication for high availability

## 🔗 Related Commands

### Docker Compose
```bash
# Start with volumes
docker-compose up -d

# Stop (volumes persist)
docker-compose down

# Stop and remove volumes (⚠️ data loss)
docker-compose down -v

# View logs
docker-compose logs -f
```

### Docker Volume
```bash
# List all volumes
docker volume ls

# Inspect a volume
docker volume inspect v3quran_verificator_quran_database

# Remove unused volumes
docker volume prune

# Remove specific volume (⚠️ data loss)
docker volume rm v3quran_verificator_quran_uploads
```

## 📚 Further Reading

- [Docker Volumes Documentation](https://docs.docker.com/storage/volumes/)
- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/07-volumes/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Summary:** Your data is now safely stored in Docker named volumes and will persist across container restarts. Use the `docker_volume_manager.sh` tool to backup, restore, and manage your data easily.

**Last Updated:** October 21, 2025

