# 

import re

class ArabicNormalizer:
    """Arabic text normalizer supporting diacritics removal."""

    # Arabic diacritics Unicode block
    DIACRITICS_PATTERN = re.compile(r'[\u064B-\u0652]')

    def normalize(self, text, drop_diacritics=False):
        """Normalize Arabic text, optionally removing diacritics."""
        # Add more normalization as needed (e.g., unify Alef forms, remove Tatweel)
        text = text.replace('\u0640', '')  # Tatweel
        # Unify Alef forms
        text = re.sub(r'[\u0622\u0623\u0625]', '\u0627', text)
        if drop_diacritics:
            text = self.DIACRITICS_PATTERN.sub('', text)
        # Strip whitespace
        text = text.strip()
        return text