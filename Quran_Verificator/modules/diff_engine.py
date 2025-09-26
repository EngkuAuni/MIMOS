# Generates diff between texts

import difflib
import html

class DiffGenerator:
    """Generate differences between two Arabic texts."""
    
    def __init__(self):
        """Initialize the diff generator."""
        pass
    
    def generate_html_diff(self, reference_text, ocr_text):
        """
        Generate an HTML diff between reference and OCR text.
        
        Returns HTML with:
        - Insertions in green
        - Deletions in red
        """
        # Generate diff
        diff = difflib.ndiff(reference_text, ocr_text)
        
        # Create HTML
        html_diff = []
        
        for op in diff:
            if op.startswith('- '):
                # Deletion (in reference, not in OCR)
                char = op[2:]
                html_diff.append(f'<span style="background-color: #ffcccc;">{html.escape(char)}</span>')
            elif op.startswith('+ '):
                # Insertion (in OCR, not in reference)
                char = op[2:]
                html_diff.append(f'<span style="background-color: #ccffcc;">{html.escape(char)}</span>')
            elif op.startswith('  '):
                # No change
                char = op[2:]
                html_diff.append(html.escape(char))
        
        # Wrap in div with RTL direction for Arabic
        return f'<div dir="rtl" style="text-align: right;">{"".join(html_diff)}</div>'
    
    def generate_character_diff(self, reference_text, ocr_text):
        """
        Generate a character-by-character diff between reference and OCR text.
        
        Returns a list of tuples (char, status) where status is:
        - 'same': character is the same in both texts
        - 'deleted': character is in reference but not in OCR
        - 'inserted': character is in OCR but not in reference
        """
        # Generate diff
        matcher = difflib.SequenceMatcher(None, reference_text, ocr_text)
        
        # Build character diff
        char_diff = []
        
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                # Characters are the same
                for i in range(i1, i2):
                    char_diff.append((reference_text[i], 'same'))
            elif op == 'delete':
                # Characters in reference but not in OCR
                for i in range(i1, i2):
                    char_diff.append((reference_text[i], 'deleted'))
            elif op == 'insert':
                # Characters in OCR but not in reference
                for j in range(j1, j2):
                    char_diff.append((ocr_text[j], 'inserted'))
            elif op == 'replace':
                # Characters in reference replaced by different ones in OCR
                for i in range(i1, i2):
                    char_diff.append((reference_text[i], 'deleted'))
                for j in range(j1, j2):
                    char_diff.append((ocr_text[j], 'inserted'))
        
        return char_diff