# LLM-based explaination generation

import os
import subprocess
import tempfile

class LLMExplainer:
    """Generate explanations for text differences using a local LLM."""
    
    def __init__(self, model_name="phi-3-mini"):
        """Initialize the LLM explainer with the specified model."""
        self.model_name = model_name
        
        # Check if Ollama is available (for local LLM inference)
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            self.ollama_available = result.returncode == 0
        except:
            self.ollama_available = False
    
    def explain_difference(self, reference_text, ocr_text, char_diff=None):
        """
        Generate an explanation for the difference between reference and OCR text.
        
        Args:
            reference_text: The reference (canonical) text
            ocr_text: The OCR-generated text
            char_diff: Optional character diff from DiffGenerator
            
        Returns:
            An explanation string
        """
        if not self.ollama_available:
            return "LLM explanation not available. Ollama is not installed or running."
        
        # Build prompt
        prompt = self._build_prompt(reference_text, ocr_text, char_diff)
        
        try:
            # Call Ollama
            result = subprocess.run(
                ['ollama', 'run', self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=30  # 30-second timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error generating explanation: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "LLM explanation timed out."
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def _build_prompt(self, reference_text, ocr_text, char_diff=None):
        """Build a prompt for the LLM."""
        # Basic prompt structure
        prompt = """
You are an expert in Arabic text and Quranic verification. I will provide you with two pieces of text:
1. The reference (canonical) text from the Quran
2. The OCR-detected text from a scanned image

Please explain the differences between these texts in a clear and concise way. Focus on:
- Missing or extra diacritics
- Missing or different characters
- Any other discrepancies

Reference text: {reference}
OCR text: {ocr}
        """.format(reference=reference_text, ocr=ocr_text)
        
        # Add character diff information if available
        if char_diff:
            diff_description = []
            for char, status in char_diff:
                if status == 'deleted':
                    diff_description.append(f"'{char}' is missing in OCR text")
                elif status == 'inserted':
                    diff_description.append(f"'{char}' is extra in OCR text")
            
            if diff_description:
                prompt += "\nSpecific differences:\n" + "\n".join(diff_description)
        
        # Add final instruction
        prompt += "\n\nExplanation (in English, keep it short and focused on the text differences):"
        
        return prompt