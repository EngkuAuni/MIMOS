# Page to ayah mapping builder

import sqlite3
import re
from config import SQLITE_DB_PATH

QURAN_METADATA_JS_PATH = "database/quran_metadata.js"
TOTAL_PAGES = 604


def parse_qurandata_page(js_path):
    """Parse QuranData.Page array from quran_metadata.js and build page-to-ayah mapping.

    This is more robust than a line-by-line search: it pulls the full Page array block
    and finds all [sura, aya] pairs using a global regex. Returns a list of (sura, aya)
    tuples in page order (should be length == TOTAL_PAGES).
    
    Now handles complete metadata with all 114 surahs properly mapped to 604 pages.
    """
    with open(js_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the Page array block: content between "QuranData.Page = [" and the closing "]";
    m = re.search(r"QuranData\.Page\s*=\s*\[\s*(.*?)\s*\];", text, re.S)
    if not m:
        raise RuntimeError(f"Could not locate QuranData.Page section in {js_path}")

    block = m.group(1)
    # Find all [num, num] pairs within the block (skip the initial empty [] entry)
    pairs = re.findall(r"\[\s*(\d+)\s*,\s*(\d+)\s*\]", block)
    pages = [(int(a), int(b)) for a, b in pairs]

    # Validate the parsed data
    if len(pages) != TOTAL_PAGES:
        raise RuntimeError(
            f"Metadata contains {len(pages)} page mappings, expected {TOTAL_PAGES}. "
            "The quran_metadata.js file may be incomplete or corrupted."
        )
    
    # Validate surah numbers are in valid range (1-114)
    max_sura = max(sura for sura, _ in pages)
    min_sura = min(sura for sura, _ in pages)
    if min_sura < 1 or max_sura > 114:
        raise RuntimeError(
            f"Invalid surah numbers found in metadata: min={min_sura}, max={max_sura}. "
            "Expected surahs in range 1-114."
        )
    
    print(f"Successfully parsed {len(pages)} page mappings from metadata")
    return pages

def build_page_mapping(pages, total_pages):
    """Build mapping: page_number -> sura_start, aya_start, sura_end, aya_end."""
    mapping = []
    for i in range(total_pages):
        sura_start, aya_start = pages[i]
        if i < total_pages - 1:
            sura_end, aya_end = pages[i + 1]
            # End ayah is the ayah before the next page's start
            # But ayah numbering is not continuous between surahs, so we need to find the previous ayah
        else:
            # Last page: take last ayah of Quran (Surah 114, Ayah 6)
            sura_end, aya_end = 114, 6
        mapping.append({
            'page_number': i + 1,
            'sura_start': sura_start,
            'aya_start': aya_start,
            'sura_end': sura_end,
            'aya_end': aya_end
        })
    return mapping

def fix_page_end_ayahs(mapping, db_path):
    """For each page, find the actual last ayah using the ayah DB."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for i in range(len(mapping) - 1):
        next_sura = mapping[i + 1]['sura_start']
        next_aya = mapping[i + 1]['aya_start']
        # Find previous ayah: if next_aya > 1, then previous is (next_sura, next_aya - 1)
        # If next_aya == 1, then previous is (next_sura - 1, last ayah of previous sura)
        if next_aya > 1:
            sura_end = next_sura
            aya_end = next_aya - 1
        else:
            sura_end = next_sura - 1
            cursor.execute("SELECT MAX(aya_number) FROM verses WHERE sura_number=?", (sura_end,))
            aya_end = cursor.fetchone()[0]
        mapping[i]['sura_end'] = sura_end
        mapping[i]['aya_end'] = aya_end
    conn.close()
    # Last page already set
    return mapping

def insert_page_mapping(db_path, mapping):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for row in mapping:
        cursor.execute('''
        INSERT OR REPLACE INTO page_mapping
        (page_number, sura_start, aya_start, sura_end, aya_end)
        VALUES (?, ?, ?, ?, ?)
        ''', (row['page_number'], row['sura_start'], row['aya_start'], row['sura_end'], row['aya_end']))
    conn.commit()
    conn.close()
    print(f"Inserted/updated mapping for {len(mapping)} pages.")

def verify_surah_mappings(pages):
    """Verify that all 114 surahs have their first page properly mapped."""
    # Extract first page of each surah (where aya == 1)
    surah_first_pages = {}
    for page_num, (sura, aya) in enumerate(pages, start=1):
        if aya == 1 and sura not in surah_first_pages:
            surah_first_pages[sura] = page_num
    
    # Check all surahs are present
    missing_surahs = [i for i in range(1, 115) if i not in surah_first_pages]
    
    if missing_surahs:
        print(f"WARNING: {len(missing_surahs)} surahs missing from page mappings: {missing_surahs[:10]}...")
        return False
    
    print(f"✓ Verified all 114 surahs have proper page mappings")
    return True

def main():
    pages = parse_qurandata_page(QURAN_METADATA_JS_PATH)
    
    # Verify the metadata is complete
    if not verify_surah_mappings(pages):
        print("Warning: Metadata verification failed, but proceeding...")
    
    mapping = build_page_mapping(pages, TOTAL_PAGES)
    mapping = fix_page_end_ayahs(mapping, SQLITE_DB_PATH)
    insert_page_mapping(SQLITE_DB_PATH, mapping)

if __name__ == "__main__":
    main()