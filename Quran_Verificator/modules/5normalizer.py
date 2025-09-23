# Text normalization for Arabic

import re
import unicodedata

class ArabicNormalizer:
    """Normalize Arabic text for comparison."""
    
    def __init__(self):
        # Common Arabic diacritics
        self.diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        
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
        Normalize Arabic text:
        1. NFC normalization
        2. Remove tatweel (kashida)
        3. Optionally remove diacritics
        4. Normalize Hamza forms
        """
        # Apply NFC normalization
        text = unicodedata.normalize('NFC', text)
        
        # Remove tatweel
        text = self.tatweel.sub('', text)
        
        # Optionally remove diacritics
        if drop_diacritics:
            text = self.diacritics.sub('', text)
        
        # Normalize Hamza forms
        for hamza, replacement in self.hamza_forms.items():
            text = text.replace(hamza, replacement)
        
        return text