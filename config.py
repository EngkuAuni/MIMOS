# Paths to Tanzil SQL dump, SQLite DB, and Quran metadata (for page mapping)
TANZIL_SQL_PATH = "database/Tanzil_quran-uthmani.sql"      # Tanzil SQL dump location
SQLITE_DB_PATH = "database/quran_verses.db"                # Main SQLite database file

# Quran metadata (for page mapping automation)
QURAN_METADATA_JS_PATH = "database/quran_metadata.js"              

# Total page count for Medina Mushaf
TOTAL_PAGES = 604

# OCR model checkpoint path (update as needed)
QARI_OCR_MODEL_PATH = "models/FT1_QariOCR"  # Using fine-tuned model
# Other global config options (add as required)
# e.g. CV feature count, confidence thresholds, logging options, etc.
CV_ORB_FEATURES = 500
OCR_CONFIDENCE_THRESHOLD = 0.85

# Default edition tag for page mapping
MUSHAF_EDITION = "uthmani"