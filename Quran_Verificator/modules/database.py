# Handles database connections and queries

import os
import sqlite3
import pandas as pd

class QuranDatabase:
    """Handle database operations for Quran verification."""
    
    def __init__(self, db_path="Data/Tanzil_quran-uthmani.sql"):
        """
        Initialize the database connection.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Check if database exists, if not create it
        if not os.path.exists(db_path):
            self.setup_database()
    
    def setup_database(self):
        """Set up the SQLite database from the Tanzil SQL dump."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Create tables
            c.execute('''
            CREATE TABLE IF NOT EXISTS quran_text (
                id INTEGER PRIMARY KEY,
                sura INTEGER,
                aya INTEGER,
                text TEXT
            )
            ''')
            
            c.execute('''
            CREATE TABLE IF NOT EXISTS ayah_hash (
                id INTEGER PRIMARY KEY,
                sura INTEGER,
                aya INTEGER,
                hash_full TEXT,
                hash_no_diacritics TEXT
            )
            ''')
            
            c.execute('''
            CREATE TABLE IF NOT EXISTS page_map (
                id INTEGER PRIMARY KEY,
                page INTEGER,
                edition TEXT,
                sura INTEGER,
                ayah_start INTEGER,
                ayah_end INTEGER
            )
            ''')
            
            # Import sample data (first surah)
            sample_data = [
                (1, 1, 1, 'بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ'),
                (2, 1, 2, 'ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ'),
                (3, 1, 3, 'ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ'),
                (4, 1, 4, 'مَـٰلِكِ يَوْمِ ٱلدِّينِ'),
                (5, 1, 5, 'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ'),
                (6, 1, 6, 'ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ'),
                (7, 1, 7, 'صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ')
            ]

            c.executemany('INSERT INTO quran_text VALUES (?, ?, ?, ?)', sample_data)
            conn.commit()
            conn.close()
            
            # After importing text data, compute and store hashes
            from modules.normalizer import ArabicNormalizer
            from modules.verifier import TextVerifier      
            normalizer = ArabicNormalizer()
            verifier = TextVerifier()
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get all quran text
            df = pd.read_sql("SELECT * FROM quran_text", conn)
            
            # Compute hashes and store them
            for _, row in df.iterrows():
                sura = row['sura']
                aya = row['aya']
                text = row['text']
                
                # Normalize text with and without diacritics
                normalized_text = normalizer.normalize(text)
                normalized_no_diacritics = normalizer.normalize(text, drop_diacritics=True)
                
                # Compute hashes
                hash_full = verifier.compute_hash(normalized_text)
                hash_no_diacritics = verifier.compute_hash(normalized_no_diacritics)
                
                # Store hashes
                c.execute(
                    "INSERT INTO ayah_hash (sura, aya, hash_full, hash_no_diacritics) VALUES (?, ?, ?, ?)",
                    (sura, aya, hash_full, hash_no_diacritics)
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise RuntimeError(f"Database setup failed: {str(e)}")
    
    def get_connection(self):
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        return sqlite3.connect(self.db_path)
    
    def get_ayah_by_hash(self, ayah_hash, with_diacritics=True):
        """
        Get ayah information by hash.
        
        Args:
            ayah_hash (str): Hash to look up
            with_diacritics (bool): Whether the hash includes diacritics
            
        Returns:
            tuple: (sura, aya) or None if not found
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        hash_field = "hash_full" if with_diacritics else "hash_no_diacritics"
        
        c.execute(f"SELECT sura, aya FROM ayah_hash WHERE {hash_field} = ?", (ayah_hash,))
        result = c.fetchone()
        
        conn.close()
        return result
    
    def get_ayah_text(self, sura, aya):
        """
        Get the text of a specific ayah.
        
        Args:
            sura (int): Surah number
            aya (int): Ayah number
            
        Returns:
            str: Ayah text or None if not found
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT text FROM quran_text WHERE sura = ? AND aya = ?", (sura, aya))
        result = c.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_fuzzy_matches(self, normalized_text, threshold=0.8):
        """
        Get potential fuzzy matches for a given text.
        
        Args:
            normalized_text (str): Normalized text to match
            threshold (float): Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            list: List of potential matches with similarity scores
        """
        import difflib
        from modules.normalizer import ArabicNormalizer
        
        normalizer = ArabicNormalizer()
                
        conn = self.get_connection()
        all_ayahs = pd.read_sql("SELECT sura, aya, text FROM quran_text", conn)
        conn.close()
        
        matches = []
        
        for _, row in all_ayahs.iterrows():
            ref_text = normalizer.normalize(row['text'], drop_diacritics=True)
            similarity = difflib.SequenceMatcher(None, normalized_text, ref_text).ratio()
            
            if similarity >= threshold:
                matches.append({
                    'sura': row['sura'],
                    'aya': row['aya'],
                    'text': row['text'],
                    'similarity': similarity
                })
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:5]  # Return top 5 matches