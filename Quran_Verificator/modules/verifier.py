# Verification logic

import hashlib
import difflib
from modules.normalizer import ArabicNormalizer

class TextVerifier:
    """Verify Quran text against reference database."""
    
    def __init__(self):
        """Initialize the text verifier."""
        self.normalizer = ArabicNormalizer()
    
    def compute_hash(self, text):
        """
        Compute SHA-256 hash of a text string.
        
        Args:
            text (str): Text to hash
            
        Returns:
            str: Hexadecimal representation of the SHA-256 hash
        """
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def verify_text(self, ocr_text, db):
        """
        Verify OCR text against reference database.
        
        Args:
            ocr_text (str): Text extracted by OCR
            db: Database connection object
            
        Returns:
            dict: Verification results
        """
        # Normalize text with diacritics
        normalized_text = self.normalizer.normalize(ocr_text)
        text_hash = self.compute_hash(normalized_text)
        
        # Try exact match with diacritics
        ayah = db.get_ayah_by_hash(text_hash, with_diacritics=True)
        if ayah:
            # Exact match with diacritics
            sura, aya = ayah
            reference_text = db.get_ayah_text(sura, aya)
            return {
                'status': 'exact',
                'match_type': 'hash',
                'with_diacritics': True,
                'ayah': (sura, aya),
                'text': reference_text,
                'similarity': 1.0,
                'fuzzy_matches': []
            }
        
        # Try exact match without diacritics
        normalized_text_no_diacritics = self.normalizer.normalize(ocr_text, drop_diacritics=True)
        text_hash_no_diacritics = self.compute_hash(normalized_text_no_diacritics)
        
        ayah = db.get_ayah_by_hash(text_hash_no_diacritics, with_diacritics=False)
        if ayah:
            # Exact match without diacritics
            sura, aya = ayah
            reference_text = db.get_ayah_text(sura, aya)
            
            # Calculate similarity with the original text (including diacritics)
            normalized_ref = self.normalizer.normalize(reference_text)
            similarity = difflib.SequenceMatcher(None, normalized_text, normalized_ref).ratio()
            
            return {
                'status': 'near',
                'match_type': 'hash',
                'with_diacritics': False,
                'ayah': (sura, aya),
                'text': reference_text,
                'similarity': similarity,
                'fuzzy_matches': []
            }
        
        # No exact match, try fuzzy matching
        fuzzy_matches = db.get_fuzzy_matches(normalized_text_no_diacritics)
        
        if fuzzy_matches and fuzzy_matches[0]['similarity'] >= 0.8:
            # Good fuzzy match
            best_match = fuzzy_matches[0]
            return {
                'status': 'near',
                'match_type': 'fuzzy',
                'with_diacritics': False,
                'ayah': (best_match['sura'], best_match['aya']),
                'text': best_match['text'],
                'similarity': best_match['similarity'],
                'fuzzy_matches': fuzzy_matches
            }
        
        # No good match
        return {
            'status': 'no_match',
            'match_type': None,
            'with_diacritics': None,
            'ayah': None,
            'text': None,
            'similarity': 0.0,
            'fuzzy_matches': fuzzy_matches
        }