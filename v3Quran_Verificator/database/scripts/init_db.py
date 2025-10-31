# Convert and build the SQLite database (quran_verses.db) from Tanzil MySQL dump + page_mappping

import os
import re
import sqlite3
import hashlib
import sys
from pathlib import Path

# Import config variables and normalizer
from config import TANZIL_SQL_PATH, SQLITE_DB_PATH
from utils.normalizer import ArabicNormalizer
from utils.logger import get_logger

logger = get_logger()

class QuranDatabaseInitializer:
    """Initialize and populate the Quran database from Tanzil SQL."""

    def __init__(self, sql_file_path=TANZIL_SQL_PATH, db_path=SQLITE_DB_PATH):
        self.sql_file_path = sql_file_path
        self.db_path = db_path
        self.normalizer = ArabicNormalizer()

    def parse_tanzil_sql(self):
        """Parse the Tanzil SQL file and extract verse data."""
        logger.info("Parsing Tanzil SQL file...")
        verses = []

        with open(self.sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        insert_pattern = r"INSERT INTO `quran_text`[^(]*\(`index`, `sura`, `aya`, `text`\) VALUES\s*\n(.*?);"
        matches = re.findall(insert_pattern, content, re.DOTALL)

        for match in matches:
            row_pattern = r"\((\d+),\s*(\d+),\s*(\d+),\s*'([^']*)'\)"
            rows = re.findall(row_pattern, match)
            for row in rows:
                try:
                    verse_id = int(row[0])
                    sura = int(row[1])
                    aya = int(row[2])
                    text = row[3].replace("\\'", "'").replace("\\\\", "\\")
                    verses.append({
                        'id': verse_id,
                        'sura': sura,
                        'aya': aya,
                        'text': text
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing row: {row} - {e}")
                    continue
        logger.info(f"Parsed {len(verses)} verses from SQL file")
        return verses
    
    def create_database_schema(self):
        """Create the SQLite database schema."""
        logger.info("Creating database schema...")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE verses (
            id INTEGER PRIMARY KEY,
            sura_number INTEGER NOT NULL,
            aya_number INTEGER NOT NULL,
            text_original TEXT NOT NULL,
            text_normalized TEXT NOT NULL,
            text_no_diacritics TEXT NOT NULL,
            hash_original TEXT NOT NULL,
            hash_normalized TEXT NOT NULL,
            hash_no_diacritics TEXT NOT NULL,
            word_count INTEGER,
            character_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('CREATE INDEX idx_sura_aya ON verses (sura_number, aya_number)')
        cursor.execute('CREATE INDEX idx_hash_original ON verses (hash_original)')
        cursor.execute('CREATE INDEX idx_hash_normalized ON verses (hash_normalized)')
        cursor.execute('CREATE INDEX idx_hash_no_diacritics ON verses (hash_no_diacritics)')
        cursor.execute('''
        CREATE TABLE page_mapping (
            page_number INTEGER PRIMARY KEY,
            sura_start INTEGER NOT NULL,
            aya_start INTEGER NOT NULL,
            sura_end INTEGER NOT NULL,
            aya_end INTEGER NOT NULL,
            edition TEXT DEFAULT 'uthmani',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database schema created successfully")

    def populate_verses(self, verses_data):
        """Populate the database with verse data and computed hashes."""
        logger.info("Populating database with verses and computing hashes...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        processed_count = 0
        for verse in verses_data:
            try:
                text_original = verse['text']
                text_normalized = self.normalizer.normalize(text_original)
                text_no_diacritics = self.normalizer.normalize(text_original, drop_diacritics=True)
                hash_original = hashlib.sha256(text_original.encode('utf-8')).hexdigest()
                hash_normalized = hashlib.sha256(text_normalized.encode('utf-8')).hexdigest()
                hash_no_diacritics = hashlib.sha256(text_no_diacritics.encode('utf-8')).hexdigest()
                word_count = len(text_original.split())
                character_count = len(text_original)
                cursor.execute('''
                INSERT INTO verses (
                    id, sura_number, aya_number, text_original, text_normalized,
                    text_no_diacritics, hash_original, hash_normalized,
                    hash_no_diacritics, word_count, character_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verse['id'], verse['sura'], verse['aya'], text_original,
                    text_normalized, text_no_diacritics, hash_original,
                    hash_normalized, hash_no_diacritics, word_count, character_count
                ))
                processed_count += 1
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} verses...")
            except Exception as e:
                logger.warning(f"Error processing verse {verse['id']}: {e}")
                continue
        conn.commit()
        conn.close()
        logger.info(f"Successfully populated {processed_count} verses")
        return processed_count

    def add_page_mappings(self, page_mappings):
        """Add page mappings for reference images."""
        logger.info("Adding page mappings...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for mapping in page_mappings:
            cursor.execute('''
            INSERT OR REPLACE INTO page_mapping
            (page_number, sura_start, aya_start, sura_end, aya_end)
            VALUES (?, ?, ?, ?, ?)
            ''', (mapping['page_number'], mapping['sura_start'], mapping['aya_start'], mapping['sura_end'], mapping['aya_end']))
        conn.commit()
        conn.close()
        logger.info(f"Added {len(page_mappings)} page mappings")

    def initialize_database(self, page_mappings):
        """Complete database initialization process."""
        logger.info("Starting Quran database initialization...")
        verses_data = self.parse_tanzil_sql()
        if not verses_data:
            logger.error("No verses found in SQL file")
            return False
        self.create_database_schema()
        self.populate_verses(verses_data)
        self.add_page_mappings(page_mappings)
        logger.info("Database initialization completed successfully.")
        return True

def main():
    logger.info("Quran Database Initializer")
    initializer = QuranDatabaseInitializer()

    # First populate verses from the Tanzil SQL dump. We pass an empty page_mappings list
    # because page mapping will be built separately by the page_mapper module.
    success = initializer.initialize_database([])
    if not success:
        logger.error("Initialization failed while populating verses.")
        return

    # Now build and insert canonical page mappings from quran_metadata.js
    try:
        # Import here to avoid a circular import at module import time
        import database.page_mapper as page_mapper
        logger.info("Building and inserting page mappings using database.page_mapper...")
        page_mapper.main()
        logger.info("Page mappings inserted successfully.")
        logger.info("Ready to use the enhanced verification system!")
    except Exception as e:
        logger.exception(f"Failed to build/insert page mappings: {e}")

if __name__ == "__main__":
    main()