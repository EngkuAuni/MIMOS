# Hash/token matching for cryptographic verification
# Uses pre-computed SHA256 hashes from database for integrity checking

import hashlib
from typing import List, Dict
from utils.normalizer import ArabicNormalizer

class HashComparator:
    """
    Cryptographic hash-based verification for Quranic text.
    Uses pre-computed hashes from database for exact matching.
    """
    
    def __init__(self):
        self.normalizer = ArabicNormalizer()
    
    def compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def compare_with_variants(self, ocr_text: str, db_verse: Dict) -> Dict:
        """
        Compare OCR text hash against database verse hashes (all variants).
        
        Args:
            ocr_text: Text extracted from OCR
            db_verse: Database verse with pre-computed hashes
            
        Returns:
            Dictionary with hash comparison results
        """
        # Compute hashes for OCR text
        ocr_hash_original = self.compute_hash(ocr_text)
        ocr_normalized = self.normalizer.normalize(ocr_text, drop_diacritics=False)
        ocr_hash_normalized = self.compute_hash(ocr_normalized)
        ocr_no_diacritics = self.normalizer.normalize(ocr_text, drop_diacritics=True)
        ocr_hash_no_diacritics = self.compute_hash(ocr_no_diacritics)
        
        # Compare against database hashes
        hash_match_original = (ocr_hash_original == db_verse.get('hash_original', ''))
        hash_match_normalized = (ocr_hash_normalized == db_verse.get('hash_normalized', ''))
        hash_match_no_diacritics = (ocr_hash_no_diacritics == db_verse.get('hash_no_diacritics', ''))
        
        # Any match is good (exact cryptographic match)
        hash_match = hash_match_original or hash_match_normalized or hash_match_no_diacritics
        
        # Determine match type
        if hash_match_original:
            match_type = 'exact'
        elif hash_match_normalized:
            match_type = 'normalized'
        elif hash_match_no_diacritics:
            match_type = 'no_diacritics'
        else:
            match_type = 'mismatch'
        
        return {
            'hash_mismatch': not hash_match,
            'match_type': match_type,
            'ocr_hash': ocr_hash_original,
            'db_hash': db_verse.get('hash_original', ''),
            'verse': ocr_text,
            'db_verse': db_verse.get('original', ''),
            'exact_match': hash_match_original,
            'normalized_match': hash_match_normalized,
            'no_diacritics_match': hash_match_no_diacritics
        }
    
    def compare(self, verses: Dict, db_verses: List) -> List[Dict]:
        """
        Compare extracted verses against database using hash verification.
        
        Args:
            verses: Dictionary with 'verses' key containing OCR-extracted verses
            db_verses: List of verse dictionaries with hashes from database
            
        Returns:
            List of hash comparison results
        """
        results = []
        ocr_verses = verses.get("verses", [])
        
        for ocr_text, db_data in zip(ocr_verses, db_verses):
            # Handle None values
            if ocr_text is None:
                ocr_text = ""
            
            # Check if db_data has hash information
            if isinstance(db_data, dict) and 'hash_original' in db_data:
                # Use cryptographic hash comparison
                comparison = self.compare_with_variants(ocr_text, db_data)
            else:
                # Fallback to simple hash comparison
                db_str = db_data if isinstance(db_data, str) else db_data.get('text', '') if isinstance(db_data, dict) else ""
                ocr_hash = self.compute_hash(ocr_text)
                db_hash = self.compute_hash(db_str)
                comparison = {
                    'hash_mismatch': ocr_hash != db_hash,
                    'match_type': 'exact' if ocr_hash == db_hash else 'mismatch',
                    'verse': ocr_text,
                    'db_verse': db_str
                }
            
            results.append(comparison)
        
        return results


def compare_hash(verses: Dict, db_verses: List) -> List[Dict]:
    """
    Legacy function for backward compatibility.
    
    Args:
        verses: Dictionary with 'verses' key
        db_verses: List of database verses (dicts with hashes preferred)
        
    Returns:
        List of hash comparison results
    """
    comparator = HashComparator()
    return comparator.compare(verses, db_verses)