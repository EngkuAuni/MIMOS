"""
Production Configuration for Quran Verification Engine
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration"""
    sqlite_path: str = "database/quran_verses.db"
    postgres_url: str = os.getenv("DATABASE_URL", "postgresql://quran_user:quran_secure_password@localhost:5432/quran_verification")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    connection_pool_size: int = 20
    query_timeout: int = 30

@dataclass
class ModelConfig:
    """AI Model configuration"""
    qari_ocr_path: str = "NAMAA-Space/Qari-OCR-0.1-VL-2B-Instruct"
    fallback_ocr: bool = True
    max_new_tokens: int = 512
    temperature: float = 0.0
    confidence_threshold: float = 0.85
    batch_size: int = 1
    device: str = "auto"  # auto, cpu, cuda

@dataclass
class VerificationConfig:
    """Verification methods configuration"""
    enable_text_verification: bool = True
    enable_structural_verification: bool = True
    enable_semantic_verification: bool = True
    enable_visual_verification: bool = True
    enable_hash_verification: bool = True
    
    # Text verification thresholds
    character_accuracy_threshold: float = 95.0
    diacritic_accuracy_threshold: float = 90.0
    
    # Structural verification thresholds
    layout_compliance_threshold: float = 85.0
    verse_segmentation_threshold: float = 90.0
    
    # Semantic verification thresholds
    semantic_similarity_threshold: float = 80.0
    contextual_accuracy_threshold: float = 75.0
    
    # Visual verification thresholds
    image_quality_threshold: float = 80.0
    font_consistency_threshold: float = 90.0

@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "light"
    language: str = "en"  # en, ar
    show_confidence_scores: bool = True
    show_anomaly_explanations: bool = True
    enable_export: bool = True
    max_file_size_mb: int = 50
    supported_formats: list = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["pdf", "jpg", "jpeg", "png", "tiff"]

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_authentication: bool = False
    session_timeout: int = 3600  # 1 hour
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_ips: list = None
    enable_ssl: bool = False
    ssl_cert_path: str = None
    ssl_key_path: str = None
    
    def __post_init__(self):
        if self.allowed_ips is None:
            self.allowed_ips = []  # Allow all if empty

@dataclass
class PerformanceConfig:
    """Performance configuration"""
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_workers: int = 4
    enable_gpu: bool = True
    memory_limit_gb: int = 8
    enable_async: bool = True
    request_timeout: int = 300  # 5 minutes

class ProductionConfig:
    """Main production configuration class"""
    
    def __init__(self, config_file: str = None):
        self.database = DatabaseConfig()
        self.model = ModelConfig()
        self.verification = VerificationConfig()
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.performance = PerformanceConfig()
        
        # Load from environment variables
        self._load_from_env()
        
        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv("DATABASE_URL"):
            self.database.postgres_url = os.getenv("DATABASE_URL")
        if os.getenv("REDIS_URL"):
            self.database.redis_url = os.getenv("REDIS_URL")
        
        # Model
        if os.getenv("QARI_OCR_PATH"):
            self.model.qari_ocr_path = os.getenv("QARI_OCR_PATH")
        if os.getenv("CONFIDENCE_THRESHOLD"):
            self.model.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD"))
        
        # Verification thresholds
        if os.getenv("CHARACTER_ACCURACY_THRESHOLD"):
            self.verification.character_accuracy_threshold = float(os.getenv("CHARACTER_ACCURACY_THRESHOLD"))
        if os.getenv("DIACRITIC_ACCURACY_THRESHOLD"):
            self.verification.diacritic_accuracy_threshold = float(os.getenv("DIACRITIC_ACCURACY_THRESHOLD"))
        
        # Security
        if os.getenv("ENABLE_AUTHENTICATION"):
            self.security.enable_authentication = os.getenv("ENABLE_AUTHENTICATION").lower() == "true"
        if os.getenv("ALLOWED_IPS"):
            self.security.allowed_ips = os.getenv("ALLOWED_IPS").split(",")
        
        # Performance
        if os.getenv("MAX_WORKERS"):
            self.performance.max_workers = int(os.getenv("MAX_WORKERS"))
        if os.getenv("ENABLE_GPU"):
            self.performance.enable_gpu = os.getenv("ENABLE_GPU").lower() == "true"
    
    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        import json
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration with file data
            for section, values in config_data.items():
                if hasattr(self, section):
                    section_obj = getattr(self, section)
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'database': self.database.__dict__,
            'model': self.model.__dict__,
            'verification': self.verification.__dict__,
            'ui': self.ui.__dict__,
            'logging': self.logging.__dict__,
            'security': self.security.__dict__,
            'performance': self.performance.__dict__
        }
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Validate database paths
        if not os.path.exists(self.database.sqlite_path):
            errors.append(f"SQLite database not found: {self.database.sqlite_path}")
        
        # Validate model path
        if not self.model.qari_ocr_path:
            errors.append("QariOCR model path not specified")
        
        # Validate thresholds
        if not (0 <= self.verification.character_accuracy_threshold <= 100):
            errors.append("Character accuracy threshold must be between 0 and 100")
        
        if not (0 <= self.verification.diacritic_accuracy_threshold <= 100):
            errors.append("Diacritic accuracy threshold must be between 0 and 100")
        
        # Validate file paths
        if self.logging.file_path and not os.path.exists(os.path.dirname(self.logging.file_path)):
            try:
                os.makedirs(os.path.dirname(self.logging.file_path), exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory: {e}")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# Default production configuration
DEFAULT_CONFIG = ProductionConfig()

# Environment-specific configurations
DEVELOPMENT_CONFIG = ProductionConfig()
DEVELOPMENT_CONFIG.logging.level = "DEBUG"
DEVELOPMENT_CONFIG.verification.character_accuracy_threshold = 80.0

STAGING_CONFIG = ProductionConfig()
STAGING_CONFIG.security.enable_authentication = True
STAGING_CONFIG.performance.enable_caching = True

PRODUCTION_CONFIG = ProductionConfig()
PRODUCTION_CONFIG.security.enable_authentication = True
PRODUCTION_CONFIG.security.enable_ssl = True
PRODUCTION_CONFIG.performance.enable_caching = True
PRODUCTION_CONFIG.performance.max_workers = 8
