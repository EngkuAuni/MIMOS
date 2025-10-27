# OCR vs DB comparison with multi-level matching
# Uses original, normalized, and no-diacritics variants for accurate comparison

from rapidfuzz import fuzz, process
from typing import List, Dict
from utils.normalizer import ArabicNormalizer

class OCRComparator:
    """
    Advanced OCR comparison using multiple text variants.
    Provides accurate matching for Arabic Quranic text.
    """
    
    def __init__(self):
        self.normalizer = ArabicNormalizer()
        
        # Similarity thresholds
        self.thresholds = {
            'excellent': 95,  # Nearly perfect match
            'good': 90,       # Minor differences only
            'acceptable': 85, # Some differences
            'poor': 70,       # Significant differences
        }
    
    def compare_with_variants(self, ocr_text: str, db_verse: Dict) -> Dict:
        """
        Compare OCR text against database verse using all available variants.
        
        Args:
            ocr_text: Text extracted from OCR
            db_verse: Database verse with variants (from get_verse_with_variants)
            
        Returns:
            Dictionary with scores and best match
        """
        # Normalize OCR text
        ocr_normalized = self.normalizer.normalize(ocr_text, drop_diacritics=False)
        ocr_no_diacritics = self.normalizer.normalize(ocr_text, drop_diacritics=True)
        
        # Compare against original (strictest)
        score_original = fuzz.ratio(ocr_text, db_verse.get('original', ''))
        
        # Compare against normalized
        score_normalized = fuzz.ratio(ocr_normalized, db_verse.get('normalized', ''))
        
        # Compare against no-diacritics (most lenient)
        score_no_diacritics = fuzz.ratio(ocr_no_diacritics, db_verse.get('no_diacritics', ''))
        
        # Use best score
        best_score = max(score_original, score_normalized, score_no_diacritics)
        
        # Determine match level
        if best_score >= self.thresholds['excellent']:
            match_level = 'excellent'
        elif best_score >= self.thresholds['good']:
            match_level = 'good'
        elif best_score >= self.thresholds['acceptable']:
            match_level = 'acceptable'
        elif best_score >= self.thresholds['poor']:
            match_level = 'poor'
        else:
            match_level = 'failed'
        
        return {
            'score': best_score,
            'score_original': score_original,
            'score_normalized': score_normalized,
            'score_no_diacritics': score_no_diacritics,
            'match_level': match_level,
            'db_verse': db_verse.get('original', ''),
            'ocr_verse': ocr_text
        }
    
    def compare(self, verses: Dict, db_verses: List) -> List[Dict]:
        """
        Compare extracted verses against database verses.
        
        Args:
            verses: Dictionary with 'verses' key containing OCR-extracted verses
            db_verses: List of verse strings OR list of verse dictionaries with variants
            
        Returns:
            List of comparison results
        """
        results = []
        ocr_verses = verses.get("verses", [])
        
        for ocr_text, db_data in zip(ocr_verses, db_verses):
            # Handle None values
            if ocr_text is None:
                ocr_text = ""
            
            # Check if db_data is a dictionary with variants or just a string
            if isinstance(db_data, dict):
                # Use advanced comparison with variants
                comparison = self.compare_with_variants(ocr_text, db_data)
            else:
                # Fallback to simple comparison
                db_str = db_data if db_data is not None else ""
                score = fuzz.ratio(ocr_text, db_str)
                comparison = {
                    'score': score,
                    'match_level': 'good' if score >= 90 else 'poor',
                    'db_verse': db_str,
                    'ocr_verse': ocr_text
                }
            
            results.append(comparison)
        
        return results


def compare_ocr(verses: Dict, db_verses: List) -> List[Dict]:
    """
    Legacy function for backward compatibility.
    
    Args:
        verses: Dictionary with 'verses' key
        db_verses: List of database verses (strings or dicts)
        
    Returns:
        List of comparison results with scores
    """
    comparator = OCRComparator()
    return comparator.compare(verses, db_verses)