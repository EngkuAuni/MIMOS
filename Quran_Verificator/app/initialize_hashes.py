import sqlite3
import os
from modules.normalizer import ArabicNormalizer
from modules.verifier import TextVerifier

def initialize_hash_tables(db_path="Data/quran.db"):
    print(f"Initializing hash tables in {db_path}...")
    
    # Check if DB exists
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        print("Run convert_db.py first to create the SQLite database.")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if quran_text table has data
    cursor.execute("SELECT COUNT(*) FROM quran_text")
    count = cursor.fetchone()[0]
    if count == 0:
        print("Error: No data in quran_text table.")
        return
    
    print(f"Found {count} verses in quran_text table")
    
    # Clear existing hash data
    cursor.execute("DELETE FROM ayah_hash")
    
    # Initialize normalizer and verifier
    normalizer = ArabicNormalizer()
    verifier = TextVerifier()
    
    # Get all quran text
    cursor.execute("SELECT id, sura, aya, text FROM quran_text")
    verses = cursor.fetchall()
    
    # Compute and store hashes
    print("Computing hashes for all verses...")
    for id, sura, aya, text in verses:
        # Normalize text with and without diacritics
        normalized_text = normalizer.normalize(text)
        normalized_no_diacritics = normalizer.normalize(text, drop_diacritics=True)
        
        # Compute hashes
        hash_full = verifier.compute_hash(normalized_text)
        hash_no_diacritics = verifier.compute_hash(normalized_no_diacritics)
        
        # Store hashes
        cursor.execute(
            "INSERT INTO ayah_hash (sura, aya, hash_full, hash_no_diacritics) VALUES (?, ?, ?, ?)",
            (sura, aya, hash_full, hash_no_diacritics)
        )
        
        if id % 100 == 0:
            print(f"Processed {id}/{count} verses")
    
    conn.commit()
    
    # Verify hash table creation
    cursor.execute("SELECT COUNT(*) FROM ayah_hash")
    hash_count = cursor.fetchone()[0]
    print(f"Created {hash_count} hash entries")
    
    conn.close()
    print("Hash initialization complete!")

if __name__ == "__main__":
    # Create Data directory if it doesn't exist
    os.makedirs("Data", exist_ok=True)
    
    initialize_hash_tables()
    print("The system should now be able to use hash-based verification.")