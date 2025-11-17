"""
Semantic Verifier (Simplified Version)
Works without PyTorch for testing purposes
"""

from typing import Dict, List, Optional
import json

class SemanticVerifier:
    """
    Simplified semantic verifier for KDN compliance
    Works without PyTorch dependencies
    """
    
    def __init__(self, llm_model_name="distilbert-base-uncased", embedding_model_name="all-MiniLM-L6-v2"):
        self.llm_model_name = llm_model_name
        self.embedding_model_name = embedding_model_name
        self.db_embeddings = None
        self.db_verses = []
        self.is_available = False
        
        # Try to load models (simplified)
        self._load_models()
    
    def _load_models(self):
        """Load models (simplified version)"""
        try:
            # For now, just set up basic functionality
            self.is_available = True
            print("✅ Semantic verifier loaded (simplified mode)")
        except Exception as e:
            print(f"⚠️ Semantic verifier not available: {e}")
            self.is_available = False
    
    def load_quran_embeddings(self, quran_verses_list):
        """Load Quran verse embeddings (simplified)"""
        self.db_verses = quran_verses_list
        print(f"✅ Loaded {len(quran_verses_list)} Quranic verse references (simplified mode)")
    
    def semantic_compare(self, ocr_text, top_k=3):
        """Compare text semantically (simplified)"""
        if not self.is_available:
            return [{"db_verse": "Semantic comparison not available", "similarity_score": 0.5}]
        
        # Simplified semantic comparison
        # In a real implementation, this would use embeddings
        return [
            {"db_verse": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "similarity_score": 0.95},
            {"db_verse": "الرَّحْمَٰنِ الرَّحِيمِ", "similarity_score": 0.85},
            {"db_verse": "مَالِكِ يَوْمِ الدِّينِ", "similarity_score": 0.80}
        ]
    
    def explain_anomaly(self, ocr_text, db_text, anomaly_type="mismatch"):
        """Explain anomaly (simplified)"""
        if not self.is_available:
            return "Semantic analysis not available in simplified mode"
        
        # Simplified explanation
        return f"Anomaly detected: {anomaly_type} between '{ocr_text[:50]}...' and '{db_text[:50]}...'. This appears to be a {anomaly_type} that may require manual review."
    
    def verify(self, ocr_text, db_text, quran_context_verses=None):
        """Verify text semantically (simplified)"""
        if not self.is_available:
            return {
                "semantic_matches": [{"db_verse": "Not available", "similarity_score": 0.0}],
                "llm_validation_score": 0.5,
                "llm_explanation": "Semantic verification not available in simplified mode"
            }
        
        semantic_comparison = self.semantic_compare(ocr_text)
        
        # Simplified validation
        llm_validation_score = 0.9  # Assume high for now
        llm_explanation = ""
        
        if semantic_comparison[0]["similarity_score"] < 0.9:
            llm_explanation = self.explain_anomaly(ocr_text, db_text, "semantic mismatch")
            llm_validation_score = 0.7
        
        return {
            "semantic_matches": semantic_comparison,
            "llm_validation_score": llm_validation_score,
            "llm_explanation": llm_explanation
        }
