#!/bin/bash

# Docker Volume Manager for Quran Verificator
# This script helps manage persistent data stored in Docker volumes

set -e

VOLUMES=(
    "v3quran_verificator_quran_database"
    "v3quran_verificator_quran_models"
    "v3quran_verificator_quran_finetuning"
    "v3quran_verificator_quran_uploads"
    "v3quran_verificator_quran_reports"
)

function show_help() {
    echo "Docker Volume Manager for Quran Verificator"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  list          - List all volumes and their sizes"
    echo "  backup        - Backup all volumes to local directory"
    echo "  restore       - Restore volumes from local backup"
    echo "  export [vol]  - Export a specific volume to local directory"
    echo "  import [vol]  - Import a specific volume from local directory"
    echo "  inspect [vol] - Show detailed information about a volume"
    echo "  browse [vol]  - Browse files in a volume (interactive)"
    echo "  clean         - Remove all volumes (WARNING: data loss!)"
    echo ""
    echo "Volume shortcuts:"
    echo "  database      - Uthmani Quran database and KDN files"
    echo "  models        - Fine-tuned QariOCR models"
    echo "  finetuning    - QariOCR training data and scripts"
    echo "  uploads       - User-uploaded Quran page images"
    echo "  reports       - Generated verification reports"
    echo ""
}

function list_volumes() {
    echo "📦 Docker Volumes for Quran Verificator:"
    echo "========================================"
    for vol in "${VOLUMES[@]}"; do
        if docker volume inspect "$vol" &>/dev/null; then
            SIZE=$(docker system df -v | grep "$vol" | awk '{print $3}')
            MOUNTPOINT=$(docker volume inspect "$vol" --format '{{ .Mountpoint }}')
            echo "✓ $vol"
            echo "  Size: ${SIZE:-Unknown}"
            echo "  Mountpoint: $MOUNTPOINT"
            echo ""
        else
            echo "✗ $vol (not created)"
            echo ""
        fi
    done
}

function backup_all() {
    BACKUP_DIR="./docker_backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    echo "📦 Backing up all volumes to: $BACKUP_DIR"
    echo "=========================================="
    
    for vol in "${VOLUMES[@]}"; do
        if docker volume inspect "$vol" &>/dev/null; then
            VOL_NAME=$(basename "$vol")
            echo "Backing up: $VOL_NAME..."
            docker run --rm \
                -v "$vol":/source:ro \
                -v "$(pwd)/$BACKUP_DIR":/backup \
                alpine tar czf "/backup/${VOL_NAME}.tar.gz" -C /source .
            echo "✓ $VOL_NAME backed up"
        fi
    done
    
    echo ""
    echo "✅ Backup completed: $BACKUP_DIR"
}

function restore_all() {
    if [ ! -d "./docker_backups" ]; then
        echo "❌ No backups found in ./docker_backups"
        exit 1
    fi
    
    echo "Available backups:"
    ls -1 ./docker_backups
    echo ""
    read -p "Enter backup directory name: " BACKUP_NAME
    
    BACKUP_DIR="./docker_backups/$BACKUP_NAME"
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "❌ Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    echo "📦 Restoring volumes from: $BACKUP_DIR"
    echo "========================================"
    
    for vol in "${VOLUMES[@]}"; do
        VOL_NAME=$(basename "$vol")
        BACKUP_FILE="$BACKUP_DIR/${VOL_NAME}.tar.gz"
        
        if [ -f "$BACKUP_FILE" ]; then
            echo "Restoring: $VOL_NAME..."
            docker run --rm \
                -v "$vol":/target \
                -v "$(pwd)/$BACKUP_DIR":/backup \
                alpine sh -c "rm -rf /target/* /target/..?* /target/.[!.]* 2>/dev/null; tar xzf /backup/${VOL_NAME}.tar.gz -C /target"
            echo "✓ $VOL_NAME restored"
        else
            echo "⚠ Backup not found for: $VOL_NAME (skipping)"
        fi
    done
    
    echo ""
    echo "✅ Restore completed"
}

function export_volume() {
    VOL_SHORT="$1"
    VOL_FULL="v3quran_verificator_quran_${VOL_SHORT}"
    
    if ! docker volume inspect "$VOL_FULL" &>/dev/null; then
        echo "❌ Volume not found: $VOL_FULL"
        exit 1
    fi
    
    EXPORT_DIR="./volume_exports"
    mkdir -p "$EXPORT_DIR"
    
    echo "📤 Exporting $VOL_FULL to $EXPORT_DIR/${VOL_SHORT}/"
    
    docker run --rm \
        -v "$VOL_FULL":/source:ro \
        -v "$(pwd)/$EXPORT_DIR":/export \
        alpine sh -c "rm -rf /export/${VOL_SHORT} && mkdir -p /export/${VOL_SHORT} && cp -a /source/. /export/${VOL_SHORT}/"
    
    echo "✅ Exported to: $EXPORT_DIR/${VOL_SHORT}/"
}

function import_volume() {
    VOL_SHORT="$1"
    VOL_FULL="v3quran_verificator_quran_${VOL_SHORT}"
    IMPORT_DIR="./volume_exports/${VOL_SHORT}"
    
    if [ ! -d "$IMPORT_DIR" ]; then
        echo "❌ Import directory not found: $IMPORT_DIR"
        exit 1
    fi
    
    echo "📥 Importing from $IMPORT_DIR to $VOL_FULL"
    
    docker run --rm \
        -v "$VOL_FULL":/target \
        -v "$(pwd)/volume_exports":/import \
        alpine sh -c "rm -rf /target/* /target/..?* /target/.[!.]* 2>/dev/null; cp -a /import/${VOL_SHORT}/. /target/"
    
    echo "✅ Imported successfully"
}

function inspect_volume() {
    VOL_SHORT="$1"
    VOL_FULL="v3quran_verificator_quran_${VOL_SHORT}"
    
    if ! docker volume inspect "$VOL_FULL" &>/dev/null; then
        echo "❌ Volume not found: $VOL_FULL"
        exit 1
    fi
    
    echo "🔍 Volume Information:"
    docker volume inspect "$VOL_FULL"
    
    echo ""
    echo "📁 Contents:"
    docker run --rm -v "$VOL_FULL":/data alpine ls -lah /data
}

function browse_volume() {
    VOL_SHORT="$1"
    VOL_FULL="v3quran_verificator_quran_${VOL_SHORT}"
    
    if ! docker volume inspect "$VOL_FULL" &>/dev/null; then
        echo "❌ Volume not found: $VOL_FULL"
        exit 1
    fi
    
    echo "🗂️  Browsing volume: $VOL_FULL"
    echo "Type 'exit' to quit, or enter a path to explore"
    echo ""
    
    docker run --rm -it -v "$VOL_FULL":/data alpine sh -c "cd /data && /bin/sh"
}

function clean_volumes() {
    echo "⚠️  WARNING: This will delete ALL volume data!"
    echo "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        echo "❌ Cancelled"
        exit 0
    fi
    
    echo "🗑️  Removing volumes..."
    docker-compose down -v
    
    echo "✅ All volumes removed"
}

# Main script
case "${1:-help}" in
    list)
        list_volumes
        ;;
    backup)
        backup_all
        ;;
    restore)
        restore_all
        ;;
    export)
        if [ -z "$2" ]; then
            echo "❌ Please specify a volume to export"
            echo "Usage: $0 export [database|models|finetuning|uploads|reports]"
            exit 1
        fi
        export_volume "$2"
        ;;
    import)
        if [ -z "$2" ]; then
            echo "❌ Please specify a volume to import"
            echo "Usage: $0 import [database|models|finetuning|uploads|reports]"
            exit 1
        fi
        import_volume "$2"
        ;;
    inspect)
        if [ -z "$2" ]; then
            echo "❌ Please specify a volume to inspect"
            echo "Usage: $0 inspect [database|models|finetuning|uploads|reports]"
            exit 1
        fi
        inspect_volume "$2"
        ;;
    browse)
        if [ -z "$2" ]; then
            echo "❌ Please specify a volume to browse"
            echo "Usage: $0 browse [database|models|finetuning|uploads|reports]"
            exit 1
        fi
        browse_volume "$2"
        ;;
    clean)
        clean_volumes
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

