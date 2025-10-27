# DB functions (SQLite/SQLAlchemy)
# Provides access to Uthmani Quran text database for verification

import sqlite3
from typing import List, Dict, Optional, Tuple
import hashlib

class UthmaniDB:
    """
    Database interface for Uthmani Quran verses.
    Provides verse retrieval, page mapping, and hash-based verification.
    """
    
    def __init__(self, db_path="database/quran_verses.db"):
        """Initialize database connection"""
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.conn.cursor()
        
        # Verify database structure
        self._verify_schema()
    
    def _verify_schema(self):
        """Verify that the database has the required schema"""
        try:
            # Check if verses table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verses'")
            if not self.cursor.fetchone():
                raise ValueError("Database missing 'verses' table")
            
            # Check if page_mapping table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='page_mapping'")
            if not self.cursor.fetchone():
                print("Warning: Database missing 'page_mapping' table - page detection will be limited")
        except Exception as e:
            print(f"Database schema verification failed: {e}")
    
    def get_verses(self, surah: int, ayah_nums: List[int]) -> List[str]:
        """
        Get verses by surah and ayah numbers.
        
        Args:
            surah: Surah number (1-114)
            ayah_nums: List of ayah numbers
            
        Returns:
            List of verse texts in original Uthmani script
        """
        try:
            if not ayah_nums:
                return []
            
            # Build query with proper parameter binding
            placeholders = ','.join('?' * len(ayah_nums))
            query = f"""
                SELECT text_original 
                FROM verses 
                WHERE sura_number = ? AND aya_number IN ({placeholders})
                ORDER BY aya_number
            """
            
            params = [surah] + ayah_nums
            self.cursor.execute(query, params)
            
            results = self.cursor.fetchall()
            return [row['text_original'] for row in results]
            
        except Exception as e:
            print(f"Error fetching verses: {e}")
            return []
    
    def get_verse_with_variants(self, surah: int, ayah: int) -> Dict:
        """
        Get a verse with all its text variants and hashes.
        
        Returns:
            Dictionary with original, normalized, and no-diacritics versions
        """
        try:
            query = """
                SELECT text_original, text_normalized, text_no_diacritics,
                       hash_original, hash_normalized, hash_no_diacritics,
                       word_count, character_count
                FROM verses
                WHERE sura_number = ? AND aya_number = ?
            """
            
            self.cursor.execute(query, (surah, ayah))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'original': row['text_original'],
                    'normalized': row['text_normalized'],
                    'no_diacritics': row['text_no_diacritics'],
                    'hash_original': row['hash_original'],
                    'hash_normalized': row['hash_normalized'],
                    'hash_no_diacritics': row['hash_no_diacritics'],
                    'word_count': row['word_count'],
                    'character_count': row['character_count']
                }
            return None
            
        except Exception as e:
            print(f"Error fetching verse variants: {e}")
            return None
    
    def get_page_info(self, page_number: int) -> Optional[Dict]:
        """
        Get information about which surahs/ayahs are on a given page.
        
        Args:
            page_number: Page number (1-604 for standard Uthmani mushaf)
            
        Returns:
            Dictionary with page information or None if not found
        """
        try:
            query = """
                SELECT page_number, sura_start, aya_start, sura_end, aya_end, edition
                FROM page_mapping
                WHERE page_number = ?
            """
            
            self.cursor.execute(query, (page_number,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'page_number': row['page_number'],
                    'sura_start': row['sura_start'],
                    'aya_start': row['aya_start'],
                    'sura_end': row['sura_end'],
                    'aya_end': row['aya_end'],
                    'edition': row['edition']
                }
            return None
            
        except Exception as e:
            print(f"Error fetching page info: {e}")
            return None
    
    def get_verses_for_page(self, page_number: int) -> List[Dict]:
        """
        Get all verses that appear on a specific page.
        
        Args:
            page_number: Page number (1-604)
            
        Returns:
            List of verse dictionaries with full information
        """
        page_info = self.get_page_info(page_number)
        if not page_info:
            return []
        
        try:
            # Handle single surah page
            if page_info['sura_start'] == page_info['sura_end']:
                query = """
                    SELECT sura_number, aya_number, text_original, text_normalized,
                           text_no_diacritics, hash_original
                    FROM verses
                    WHERE sura_number = ? AND aya_number BETWEEN ? AND ?
                    ORDER BY aya_number
                """
                self.cursor.execute(query, (
                    page_info['sura_start'],
                    page_info['aya_start'],
                    page_info['aya_end']
                ))
            else:
                # Handle page spanning multiple surahs
                query = """
                    SELECT sura_number, aya_number, text_original, text_normalized,
                           text_no_diacritics, hash_original
                    FROM verses
                    WHERE (sura_number = ? AND aya_number >= ?)
                       OR (sura_number > ? AND sura_number < ?)
                       OR (sura_number = ? AND aya_number <= ?)
                    ORDER BY sura_number, aya_number
                """
                self.cursor.execute(query, (
                    page_info['sura_start'], page_info['aya_start'],
                    page_info['sura_start'], page_info['sura_end'],
                    page_info['sura_end'], page_info['aya_end']
                ))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'sura': row['sura_number'],
                    'ayah': row['aya_number'],
                    'text': row['text_original'],
                    'normalized': row['text_normalized'],
                    'no_diacritics': row['text_no_diacritics'],
                    'hash': row['hash_original']
                })
            
            return results
            
        except Exception as e:
            print(f"Error fetching page verses: {e}")
            return []
    
    def find_page_by_content(self, text_sample: str, min_similarity: float = 0.7) -> Optional[int]:
        """
        Attempt to identify which page a text sample belongs to.
        Uses simple text matching - not perfect but helps with identification.
        
        Args:
            text_sample: Sample of text from the page
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            Page number if found, None otherwise
        """
        # This is a basic implementation - could be enhanced with better matching
        try:
            # Clean the sample text
            text_clean = text_sample.strip().replace('\n', ' ')
            
            # Try to find a matching verse
            query = """
                SELECT sura_number, aya_number
                FROM verses
                WHERE text_original LIKE ? OR text_normalized LIKE ?
                LIMIT 1
            """
            
            # Use first significant portion of text
            search_pattern = f"%{text_clean[:50]}%"
            self.cursor.execute(query, (search_pattern, search_pattern))
            result = self.cursor.fetchone()
            
            if result:
                # Find which page this verse is on
                sura, ayah = result['sura_number'], result['aya_number']
                page_query = """
                    SELECT page_number
                    FROM page_mapping
                    WHERE (sura_start = ? AND aya_start <= ? AND aya_end >= ?)
                       OR (sura_start < ? AND sura_end > ?)
                       OR (sura_start < ? AND sura_end = ? AND aya_end >= ?)
                    LIMIT 1
                """
                self.cursor.execute(page_query, (sura, ayah, ayah, sura, sura, sura, sura, ayah))
                page_result = self.cursor.fetchone()
                
                if page_result:
                    return page_result['page_number']
            
            return None
            
        except Exception as e:
            print(f"Error finding page by content: {e}")
            return None
    
    def get_total_verses(self) -> int:
        """Get total number of verses in database"""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM verses")
            return self.cursor.fetchone()['count']
        except:
            return 0
    
    def get_total_pages(self) -> int:
        """Get total number of pages in database"""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM page_mapping")
            return self.cursor.fetchone()['count']
        except:
            return 0
    
    def verify_hash(self, text: str, expected_hash: str, variant: str = 'original') -> bool:
        """
        Verify if a text's hash matches the expected hash.
        
        Args:
            text: The text to verify
            expected_hash: The expected SHA256 hash
            variant: Which text variant to use ('original', 'normalized', 'no_diacritics')
            
        Returns:
            True if hashes match, False otherwise
        """
        try:
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            return text_hash == expected_hash
        except:
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()