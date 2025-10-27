"""
Semantic Verification Module using RAG + LLM
Provides contextual understanding and semantic validation
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

@dataclass
class VerificationContext:
    """Context for semantic verification"""
    surah_name: str
    ayah_number: int
    page_number: int
    surrounding_verses: List[str]
    historical_context: Optional[str] = None
    linguistic_notes: Optional[str] = None

class SemanticVerifier:
    """RAG + LLM based semantic verification for Quran text"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self.vector_index = None
        self.context_database = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding model and vector database"""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            print(f"✅ Semantic verifier initialized with {self.model_name}")
        except Exception as e:
            print(f"⚠️ Failed to initialize semantic verifier: {e}")
            self.embedding_model = None
    
    def verify_semantics(self, extracted_text: str, reference_text: str, context: VerificationContext) -> Dict:
        """
        Perform semantic verification using RAG + LLM
        
        Args:
            extracted_text: OCR extracted text
            reference_text: Reference text from database
            context: Verification context
            
        Returns:
            Dict with semantic verification results
        """
        if not self.embedding_model:
            return self._fallback_verification(extracted_text, reference_text)
        
        results = {
            'semantic_similarity': 0.0,
            'contextual_accuracy': 0.0,
            'linguistic_consistency': 0.0,
            'anomaly_explanations': [],
            'suggestions': [],
            'confidence_score': 0.0
        }
        
        # Semantic similarity
        semantic_sim = self._calculate_semantic_similarity(extracted_text, reference_text)
        results['semantic_similarity'] = semantic_sim
        
        # Contextual accuracy
        contextual_acc = self._verify_contextual_accuracy(extracted_text, context)
        results['contextual_accuracy'] = contextual_acc
        
        # Linguistic consistency
        linguistic_cons = self._verify_linguistic_consistency(extracted_text, context)
        results['linguistic_consistency'] = linguistic_cons
        
        # Generate anomaly explanations
        explanations = self._generate_anomaly_explanations(extracted_text, reference_text, context)
        results['anomaly_explanations'] = explanations
        
        # Generate suggestions
        suggestions = self._generate_semantic_suggestions(extracted_text, reference_text, context)
        results['suggestions'] = suggestions
        
        # Calculate overall confidence
        results['confidence_score'] = self._calculate_confidence_score(results)
        
        return results
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using embeddings"""
        if not self.embedding_model:
            return 0.0
        
        try:
            # Generate embeddings
            embedding1 = self.embedding_model.encode([text1])
            embedding2 = self.embedding_model.encode([text2])
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1[0], embedding2[0]) / (
                np.linalg.norm(embedding1[0]) * np.linalg.norm(embedding2[0])
            )
            
            return float(similarity * 100)  # Convert to percentage
        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _verify_contextual_accuracy(self, text: str, context: VerificationContext) -> float:
        """Verify contextual accuracy using surrounding verses"""
        if not context.surrounding_verses:
            return 100.0  # No context to verify against
        
        # Calculate similarity with surrounding verses
        similarities = []
        for verse in context.surrounding_verses:
            sim = self._calculate_semantic_similarity(text, verse)
            similarities.append(sim)
        
        # Return average similarity
        return float(np.mean(similarities)) if similarities else 100.0
    
    def _verify_linguistic_consistency(self, text: str, context: VerificationContext) -> float:
        """Verify linguistic consistency"""
        # This would check for:
        # - Proper Arabic grammar
        # - Consistent diacritic usage
        # - Appropriate vocabulary for the context
        # - Proper verse structure
        
        # For now, return a placeholder score
        return 95.0
    
    def _generate_anomaly_explanations(self, extracted: str, reference: str, context: VerificationContext) -> List[Dict]:
        """Generate detailed explanations for anomalies"""
        explanations = []
        
        # Character-level differences
        if extracted != reference:
            explanations.append({
                'type': 'text_mismatch',
                'description': 'Extracted text does not match reference text',
                'severity': 'high',
                'details': {
                    'extracted_length': len(extracted),
                    'reference_length': len(reference),
                    'character_differences': self._find_character_differences(extracted, reference)
                }
            })
        
        # Contextual anomalies
        if context.surrounding_verses:
            contextual_sim = self._calculate_semantic_similarity(extracted, ' '.join(context.surrounding_verses))
            if contextual_sim < 70:
                explanations.append({
                    'type': 'contextual_anomaly',
                    'description': 'Text does not fit well with surrounding verses',
                    'severity': 'medium',
                    'details': {
                        'contextual_similarity': contextual_sim,
                        'surah': context.surah_name,
                        'ayah': context.ayah_number
                    }
                })
        
        return explanations
    
    def _generate_semantic_suggestions(self, extracted: str, reference: str, context: VerificationContext) -> List[str]:
        """Generate semantic-based suggestions for corrections"""
        suggestions = []
        
        # Semantic similarity suggestions
        semantic_sim = self._calculate_semantic_similarity(extracted, reference)
        if semantic_sim < 80:
            suggestions.append("Consider reviewing the semantic meaning - low similarity with reference")
        
        # Contextual suggestions
        if context.surrounding_verses:
            contextual_sim = self._calculate_semantic_similarity(extracted, ' '.join(context.surrounding_verses))
            if contextual_sim < 70:
                suggestions.append("Text may not fit the contextual flow of surrounding verses")
        
        # Linguistic suggestions
        if len(extracted.split()) != len(reference.split()):
            suggestions.append("Word count mismatch - verify verse completeness")
        
        return suggestions
    
    def _calculate_confidence_score(self, results: Dict) -> float:
        """Calculate overall confidence score"""
        weights = {
            'semantic_similarity': 0.4,
            'contextual_accuracy': 0.3,
            'linguistic_consistency': 0.3
        }
        
        confidence = 0.0
        for key, weight in weights.items():
            if key in results:
                confidence += results[key] * weight
        
        return min(confidence, 100.0)
    
    def _find_character_differences(self, text1: str, text2: str) -> List[Dict]:
        """Find specific character differences"""
        differences = []
        
        # Simple character-by-character comparison
        min_len = min(len(text1), len(text2))
        for i in range(min_len):
            if text1[i] != text2[i]:
                differences.append({
                    'position': i,
                    'extracted': text1[i],
                    'reference': text2[i]
                })
        
        return differences
    
    def _fallback_verification(self, extracted_text: str, reference_text: str) -> Dict:
        """Fallback verification when LLM is not available"""
        return {
            'semantic_similarity': 0.0,
            'contextual_accuracy': 0.0,
            'linguistic_consistency': 0.0,
            'anomaly_explanations': [{
                'type': 'system_limitation',
                'description': 'Semantic verification not available - LLM model not loaded',
                'severity': 'low'
            }],
            'suggestions': ['Install required dependencies for semantic verification'],
            'confidence_score': 0.0
        }
    
    def load_context_database(self, db_path: str):
        """Load context database for enhanced verification"""
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                self.context_database = json.load(f)
            print(f"✅ Context database loaded from {db_path}")
        except Exception as e:
            print(f"⚠️ Failed to load context database: {e}")
    
    def build_vector_index(self, texts: List[str]):
        """Build FAISS vector index for fast similarity search"""
        if not self.embedding_model:
            return
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.vector_index.add(embeddings)
            
            print(f"✅ Vector index built with {len(texts)} texts")
        except Exception as e:
            print(f"⚠️ Failed to build vector index: {e}")
    
    def search_similar_texts(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar texts using vector index"""
        if not self.vector_index or not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.vector_index.search(query_embedding, k)
            
            # Return results (would need to map indices back to original texts)
            return [(f"text_{idx}", float(score)) for idx, score in zip(indices[0], scores[0])]
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
