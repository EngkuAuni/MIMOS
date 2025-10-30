#!/usr/bin/env python3
"""
Import Tanzil Quran database from SQL to SQLite
Converts MySQL format to SQLite and populates uthmani_quran.db
"""

import sqlite3
import re
import sys

def import_tanzil_to_sqlite(sql_file='Tanzil_quran-uthmani.sql', db_file='uthmani_quran.db'):
    """Import Tanzil SQL file into SQLite database"""
    
    print(f"📚 Importing Tanzil Quran from {sql_file} to {db_file}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Drop existing table if any
    cursor.execute("DROP TABLE IF EXISTS quran_text")
    
    # Create table with proper schema for SQLite
    cursor.execute("""
        CREATE TABLE quran_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sura INTEGER NOT NULL,
            aya INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)
    
    # Create indices for faster queries
    cursor.execute("CREATE INDEX idx_sura_aya ON quran_text(sura, aya)")
    cursor.execute("CREATE INDEX idx_sura ON quran_text(sura)")
    
    print("✅ Table created successfully")
    
    # Read and parse SQL file
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract INSERT statements
    insert_pattern = r"INSERT INTO `quran_text` \(`index`, `sura`, `aya`, `text`\) VALUES\s+(.*?);"
    inserts = re.findall(insert_pattern, content, re.DOTALL)
    
    total_verses = 0
    
    for insert_block in inserts:
        # Split individual value tuples
        value_pattern = r"\((\d+),\s*(\d+),\s*(\d+),\s*'([^']+)'\)"
        values = re.findall(value_pattern, insert_block)
        
        for index, sura, aya, text in values:
            # Unescape SQL escapes
            text = text.replace("\\'", "'").replace("\\\\", "\\")
            
            cursor.execute(
                "INSERT INTO quran_text (sura, aya, text) VALUES (?, ?, ?)",
                (int(sura), int(aya), text)
            )
            total_verses += 1
            
            if total_verses % 1000 == 0:
                print(f"  Imported {total_verses} verses...")
    
    # Commit changes
    conn.commit()
    
    # Verify import
    cursor.execute("SELECT COUNT(*) FROM quran_text")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(sura) FROM quran_text")
    max_sura = cursor.fetchone()[0]
    
    print(f"\n✅ Import completed successfully!")
    print(f"   Total verses: {count}")
    print(f"   Total surahs: {max_sura}")
    
    # Show sample verses
    print(f"\n📖 Sample verses:")
    cursor.execute("SELECT sura, aya, text FROM quran_text WHERE sura = 1 LIMIT 7")
    for sura, aya, text in cursor.fetchall():
        print(f"   {sura}:{aya} - {text[:50]}...")
    
    conn.close()
    print(f"\n💾 Database saved to: {db_file}")

if __name__ == "__main__":
    try:
        import_tanzil_to_sqlite()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

