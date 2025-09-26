# Text normalization

import re
import unicodedata

class ArabicNormalizer:
    """Normalize Arabic text for comparison."""
    
    def __init__(self):
        """Initialize normalization patterns."""
        # Common Arabic diacritics
        self.diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        
        # Waqf signs (Quran-specific marks)
        self.waqf_signs = re.compile(r'[\u06d6-\u06ed]')
        
        # Zero-width characters and spaces
        self.zero_width = re.compile(r'[\u200c\u200d\ufeff]')
        
        # Tatweel character (kashida)
        self.tatweel = re.compile(r'\u0640')
        
        # Different forms of Hamza
        self.hamza_forms = {
            '\u0622': '\u0627',  # آ -> ا
            '\u0623': '\u0627',  # أ -> ا
            '\u0625': '\u0627',  # إ -> ا
            '\u0624': '\u0648',  # ؤ -> و
            '\u0626': '\u064A',  # ئ -> ي
        }
    
    def normalize(self, text, drop_diacritics=False):
        """
        Normalize Arabic text for consistent comparison.
        
        Args:
            text (str): Arabic text to normalize
            drop_diacritics (bool): Whether to remove diacritical marks
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
            
        # Apply NFC normalization (canonical decomposition + canonical composition)
        text = unicodedata.normalize('NFC', text)
        
        # Remove tatweel (elongation character)
        text = self.tatweel.sub('', text)
        
        # Remove zero-width characters
        text = self.zero_width.sub('', text)
        
        # Optionally remove diacritics
        if drop_diacritics:
            text = self.diacritics.sub('', text)
            text = self.waqf_signs.sub('', text)
        
        # Normalize Hamza forms
        for hamza, replacement in self.hamza_forms.items():
            text = text.replace(hamza, replacement)
        
        return text