"""
Enhanced Text Verification Module
Handles character-level, diacritic, and hash-based verification
"""

import hashlib
import re
from typing import Dict, List, Tuple, Optional
from rapidfuzz import fuzz
import unicodedata

class TextVerifier:
    """Advanced text verification for Uthmani Quran text"""
    
    def __init__(self):
        self.diacritic_patterns = self._load_diacritic_patterns()
        self.uthmani_characters = self._load_uthmani_characters()
    
    def _load_diacritic_patterns(self) -> Dict[str, str]:
        """Load Uthmani diacritic patterns and their Unicode representations"""
        return {
            'fatha': 'َ', 'damma': 'ُ', 'kasra': 'ِ',
            'shadda': 'ّ', 'sukun': 'ْ', 'tanween_fath': 'ً',
            'tanween_damm': 'ٌ', 'tanween_kasr': 'ٍ',
            'maddah': 'آ', 'hamza_above': 'أ', 'hamza_below': 'إ',
            'alif_hamza': 'أ', 'waw_hamza': 'ؤ', 'ya_hamza': 'ئ'
        }
    
    def _load_uthmani_characters(self) -> set:
        """Load valid Uthmani Arabic characters"""
        return set('ءآأؤإئابتثجحخدذرزسشصضطظعغفقكلمنهوي')
    
    def verify_text(self, extracted_text: str, reference_text: str) -> Dict:
        """
        Comprehensive text verification
        
        Returns:
            Dict with verification results including:
            - character_accuracy: float
            - diacritic_accuracy: float
            - hash_match: bool
            - anomalies: List[Dict]
            - suggestions: List[str]
        """
        results = {
            'character_accuracy': 0.0,
            'diacritic_accuracy': 0.0,
            'hash_match': False,
            'anomalies': [],
            'suggestions': []
        }
        
        # Character-level verification
        char_results = self._verify_characters(extracted_text, reference_text)
        results.update(char_results)
        
        # Diacritic verification
        diacritic_results = self._verify_diacritics(extracted_text, reference_text)
        results.update(diacritic_results)
        
        # Hash verification
        results['hash_match'] = self._verify_hash(extracted_text, reference_text)
        
        # Generate suggestions
        results['suggestions'] = self._generate_suggestions(extracted_text, reference_text)
        
        return results
    
    def _verify_characters(self, extracted: str, reference: str) -> Dict:
        """Verify character-level accuracy"""
        # Normalize texts
        extracted_norm = self._normalize_text(extracted)
        reference_norm = self._normalize_text(reference)
        
        # Calculate character accuracy
        char_accuracy = fuzz.ratio(extracted_norm, reference_norm)
        
        # Find character-level differences
        anomalies = self._find_character_anomalies(extracted_norm, reference_norm)
        
        return {
            'character_accuracy': char_accuracy,
            'character_anomalies': anomalies
        }
    
    def _verify_diacritics(self, extracted: str, reference: str) -> Dict:
        """Verify diacritic accuracy"""
        extracted_diacritics = self._extract_diacritics(extracted)
        reference_diacritics = self._extract_diacritics(reference)
        
        if not reference_diacritics:
            return {'diacritic_accuracy': 100.0, 'diacritic_anomalies': []}
        
        # Calculate diacritic accuracy
        diacritic_accuracy = fuzz.ratio(extracted_diacritics, reference_diacritics)
        
        # Find diacritic anomalies
        anomalies = self._find_diacritic_anomalies(extracted, reference)
        
        return {
            'diacritic_accuracy': diacritic_accuracy,
            'diacritic_anomalies': anomalies
        }
    
    def _verify_hash(self, extracted: str, reference: str) -> bool:
        """Verify cryptographic hash match"""
        extracted_hash = hashlib.sha256(extracted.encode('utf-8')).hexdigest()
        reference_hash = hashlib.sha256(reference.encode('utf-8')).hexdigest()
        return extracted_hash == reference_hash
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove diacritics for character comparison
        normalized = unicodedata.normalize('NFD', text)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return normalized.strip()
    
    def _extract_diacritics(self, text: str) -> str:
        """Extract only diacritics from text"""
        diacritics = []
        for char in text:
            if unicodedata.category(char) == 'Mn':  # Mark, nonspacing (diacritics)
                diacritics.append(char)
        return ''.join(diacritics)
    
    def _find_character_anomalies(self, extracted: str, reference: str) -> List[Dict]:
        """Find character-level anomalies"""
        anomalies = []
        
        # Use difflib for detailed comparison
        import difflib
        differ = difflib.unified_diff(
            reference.splitlines(keepends=True),
            extracted.splitlines(keepends=True),
            fromfile='reference',
            tofile='extracted'
        )
        
        for line in differ:
            if line.startswith('+') or line.startswith('-'):
                anomalies.append({
                    'type': 'character_mismatch',
                    'line': line.strip(),
                    'severity': 'high' if line.startswith('-') else 'medium'
                })
        
        return anomalies
    
    def _find_diacritic_anomalies(self, extracted: str, reference: str) -> List[Dict]:
        """Find diacritic-specific anomalies"""
        anomalies = []
        
        # Compare diacritics position by position
        extracted_diacritics = self._extract_diacritics(extracted)
        reference_diacritics = self._extract_diacritics(reference)
        
        min_len = min(len(extracted_diacritics), len(reference_diacritics))
        
        for i in range(min_len):
            if extracted_diacritics[i] != reference_diacritics[i]:
                anomalies.append({
                    'type': 'diacritic_mismatch',
                    'position': i,
                    'extracted': extracted_diacritics[i],
                    'reference': reference_diacritics[i],
                    'severity': 'high'
                })
        
        return anomalies
    
    def _generate_suggestions(self, extracted: str, reference: str) -> List[str]:
        """Generate correction suggestions"""
        suggestions = []
        
        # Character-level suggestions
        if fuzz.ratio(extracted, reference) < 95:
            suggestions.append("Consider reviewing character-level differences")
        
        # Diacritic suggestions
        extracted_diacritics = self._extract_diacritics(extracted)
        reference_diacritics = self._extract_diacritics(reference)
        
        if len(extracted_diacritics) != len(reference_diacritics):
            suggestions.append(f"Diacritic count mismatch: found {len(extracted_diacritics)}, expected {len(reference_diacritics)}")
        
        return suggestions
