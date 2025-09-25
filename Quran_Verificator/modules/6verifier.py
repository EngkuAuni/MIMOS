# Logic for verifying text againts references

import hashlib
import difflib
from modules.normalizer5 import ArabicNormalizer
from modules.verifier6 import TextVerifier  

class TextVerifier:
    """Verify Quran text against reference database."""
    
    def __init__(self):
        """Initialize the text verifier."""
        self.normalizer = ArabicNormalizer()
    
    def compute_hash(self, text):
        """Compute SHA-256 hash of a text string."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def verify_text(self, ocr_text, db):
        """
        Verify OCR text against reference database.
        
        Returns a dictionary with the verification results:
        {
            'status': 'exact', 'near', or 'no_match',
            'match_type': 'hash' or 'fuzzy',
            'with_diacritics': True or False,
            'ayah': (sura, aya) or None,
            'text': reference text or None,
            'similarity': similarity score (for near matches),
            'fuzzy_matches': list of top fuzzy matches (for no exact match)
        }
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
    
    def verify_page(self, page, edition, ocr_text, db):
        """
        Verify OCR text against a specific page and edition.
        
        This is for edition-locked verification, where we know which page
        and edition we're checking.
        """
        # Get ayahs for this page and edition
        ayahs = db.get_page_ayahs(page, edition)
        
        # Normalize OCR text
        normalized_ocr = self.normalizer.normalize(ocr_text)
        
        # Check if the OCR text contains all ayahs
        all_matched = True
        matches = []
        
        for sura, aya, ref_text in ayahs:
            normalized_ref = self.normalizer.normalize(ref_text)
            
            # Check if normalized_ref is in normalized_ocr
            if normalized_ref in normalized_ocr:
                matches.append({
                    'sura': sura,
                    'aya': aya,
                    'text': ref_text,
                    'status': 'exact',
                    'similarity': 1.0
                })
            else:
                # Try fuzzy matching
                similarity = difflib.SequenceMatcher(None, normalized_ocr, normalized_ref).ratio()
                
                if similarity >= 0.8:
                    matches.append({
                        'sura': sura,
                        'aya': aya,
                        'text': ref_text,
                        'status': 'near',
                        'similarity': similarity
                    })
                else:
                    matches.append({
                        'sura': sura,
                        'aya': aya,
                        'text': ref_text,
                        'status': 'no_match',
                        'similarity': similarity
                    })
                
                all_matched = False
        
        # Determine overall status
        if all_matched:
            status = 'exact'
        elif any(m['status'] == 'near' for m in matches):
            status = 'near'
        else:
            status = 'no_match'
        
        return {
            'status': status,
            'edition': edition,
            'page': page,
            'matches': matches
        }