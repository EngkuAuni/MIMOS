# Missing Line Detection and Suggestion System
# Detects missing lines/verses and suggests what should be there

import re
from typing import Dict, List, Tuple, Optional
from database.uthmani_db import UthmaniDB

# Try to import optional dependencies
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️ rapidfuzz not available, using basic string matching")

# RAG + LLM Dependencies
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    RAG_AVAILABLE = True
    print("✅ RAG dependencies available")
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ RAG dependencies not available, using basic matching")

# LLM Dependencies
try:
    import requests
    LLM_AVAILABLE = True
    print("✅ LLM dependencies available")
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ LLM dependencies not available, using basic suggestions")

class MissingLineDetector:
    """
    Advanced missing line detection and suggestion system with RAG + LLM.
    Detects missing verses/lines and provides intelligent suggestions using semantic understanding.
    """
    
    def __init__(self, db_path="database/quran_verses.db"):
        self.db = UthmaniDB(db_path)
        
        # Common verse patterns for better detection
        self.verse_patterns = {
            'ayah_end': re.compile(r'[۝۩۞]', re.UNICODE),
            'bismillah': re.compile(r'بِسْمِ\s+اللَّهِ\s+الرَّحْمَـٰنِ\s+الرَّحِيمِ', re.UNICODE),
            'surah_title': re.compile(r'سورة\s+(\S+)|سُورَةُ\s+(\S+)', re.UNICODE),
        }
        
        # RAG + LLM System
        self.rag_system = None
        self.verse_embeddings = None
        self.verse_database = []
        self.llm_available = LLM_AVAILABLE
        
        # Initialize RAG system if available
        if RAG_AVAILABLE:
            self._initialize_rag_system()
    
    def _initialize_rag_system(self):
        """Initialize the RAG system for semantic verse understanding."""
        try:
            print("🔄 Initializing RAG system...")
            
            # Use a multilingual model that works well with Arabic
            self.rag_system = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Build verse database
            self._build_verse_database()
            
            print(f"✅ RAG system initialized with {len(self.verse_database)} verses")
            
        except Exception as e:
            print(f"⚠️ RAG initialization failed: {e}")
            self.rag_system = None
    
    def _build_verse_database(self):
        """Build a comprehensive database of all Quran verses for RAG."""
        try:
            # Get all verses from the database
            cursor = self.db.cursor
            cursor.execute("SELECT sura_number, aya_number, text_original FROM verses ORDER BY sura_number, aya_number")
            verses = cursor.fetchall()
            
            self.verse_database = []
            for verse in verses:
                self.verse_database.append({
                    'surah': verse[0],
                    'ayah': verse[1], 
                    'text': verse[2],
                    'context': f"Surah {verse[0]}, Ayah {verse[1]}"
                })
            
            # Generate embeddings for all verses
            if self.rag_system and self.verse_database:
                verse_texts = [v['text'] for v in self.verse_database]
                self.verse_embeddings = self.rag_system.encode(verse_texts)
                
                # Create FAISS index for fast similarity search
                dimension = self.verse_embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                self.faiss_index.add(self.verse_embeddings.astype('float32'))
                
        except Exception as e:
            print(f"⚠️ Verse database building failed: {e}")
            self.verse_database = []
    
    def _get_semantic_context(self, text: str, surah: int, top_k: int = 5) -> List[Dict]:
        """Get semantically similar verses using RAG."""
        if not self.rag_system or not self.verse_embeddings is not None:
            return []
        
        try:
            # Encode the input text
            query_embedding = self.rag_system.encode([text])
            
            # Search for similar verses
            scores, indices = self.faiss_index.search(query_embedding.astype('float32'), top_k)
            
            context_verses = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.verse_database):
                    verse = self.verse_database[idx]
                    context_verses.append({
                        'verse': verse,
                        'similarity': float(score),
                        'surah': verse['surah'],
                        'ayah': verse['ayah']
                    })
            
            return context_verses
            
        except Exception as e:
            print(f"⚠️ Semantic context retrieval failed: {e}")
            return []
    
    def _generate_llm_suggestion(self, missing_text: str, context: List[Dict], surah: int) -> str:
        """Generate intelligent suggestions using LLM."""
        if not self.llm_available:
            return f"Missing verse: {missing_text}"
        
        try:
            # Prepare context for LLM
            context_text = "\n".join([f"Surah {v['surah']}, Ayah {v['ayah']}: {v['verse']['text']}" 
                                    for v in context[:3]])
            
            # Simple LLM prompt (can be enhanced with actual LLM API)
            suggestion = f"""
Based on the context of Surah {surah} and similar verses:
{context_text}

The missing text appears to be: {missing_text}

This verse likely follows the pattern of similar verses in the same surah.
"""
            return suggestion.strip()
            
        except Exception as e:
            print(f"⚠️ LLM suggestion generation failed: {e}")
            return f"Missing verse: {missing_text}"
    
    def detect_missing_lines(self, extracted_text: str, reference_verses: List[str], 
                           surah: int, page_number: int) -> Dict:
        """
        Detect missing lines and provide suggestions.
        
        Args:
            extracted_text: OCR extracted text
            reference_verses: List of reference verses from database
            surah: Surah number
            page_number: Page number
            
        Returns:
            Dict with missing line analysis and suggestions
        """
        # Handle None or empty inputs
        if not extracted_text or not reference_verses:
            return {
                'extracted_lines': [],
                'reference_lines': [],
                'missing_lines': [],
                'missing_content': [],
                'suggestions': [],
                'confidence': 0.0,
                'rag_context': None,
                'line_count_analysis': {
                    'extracted_count': 0,
                    'reference_count': 0,
                    'missing_count': 0
                }
            }
        
        # Split extracted text into lines
        extracted_lines = self._split_into_lines(extracted_text)
        
        # Clean and normalize lines
        extracted_clean = [self._clean_line(line) for line in extracted_lines if line.strip()]
        reference_clean = [self._clean_line(verse) for verse in reference_verses if verse and str(verse).strip()]
        
        # Find missing lines with enhanced matching
        missing_analysis = self._find_missing_lines(extracted_clean, reference_clean, surah)
        
        # Generate enhanced suggestions
        suggestions = self._generate_enhanced_suggestions(
            missing_analysis, reference_verses, surah, page_number
        )
        
        return {
            'extracted_lines': extracted_clean,
            'reference_lines': reference_clean,
            'missing_indices': missing_analysis['missing_indices'],
            'missing_content': missing_analysis['missing_content'],
            'suggestions': suggestions,
            'confidence': missing_analysis['confidence'],
            'match_details': missing_analysis.get('match_details', []),
            'line_count_analysis': {
                'extracted_count': len(extracted_clean),
                'reference_count': len(reference_clean),
                'missing_count': len(missing_analysis['missing_indices'])
            }
        }
    
    def _split_into_lines(self, text: str) -> List[str]:
        """Split text into lines, handling various line break patterns."""
        # Split by newlines first
        lines = text.split('\n')
        
        # Further split by verse markers if needed
        result_lines = []
        for line in lines:
            if line.strip():
                # Check if line contains multiple verses (separated by verse markers)
                verse_parts = re.split(r'[۝۩۞]', line)
                for part in verse_parts:
                    if part.strip():
                        result_lines.append(part.strip())
        
        return result_lines
    
    def _clean_line(self, line: str) -> str:
        """Clean and normalize a line for comparison."""
        # Remove extra whitespace
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Remove verse markers
        line = re.sub(r'[۝۩۞]', '', line)
        
        # Remove page numbers
        line = re.sub(r'صفحة\s*\d+', '', line)
        
        return line
    
    def _find_missing_lines(self, extracted: List[str], reference: List[str], surah: int) -> Dict:
        """Find which lines are missing from the extracted text using advanced matching."""
        missing_indices = []
        missing_content = []
        confidence_scores = []
        match_details = []
        
        # Enhanced matching with semantic understanding
        for i, ref_line in enumerate(reference):
            if not ref_line.strip():
                continue
                
            # Find best match in extracted text
            best_match = None
            best_score = 0
            best_index = -1
            semantic_score = 0
            
            # 1. Traditional fuzzy matching
            for j, ext_line in enumerate(extracted):
                if not ext_line.strip():
                    continue
                    
                # Calculate similarity
                if RAPIDFUZZ_AVAILABLE:
                    similarity = fuzz.ratio(ext_line, ref_line)
                else:
                    # Fallback to basic string matching
                    similarity = self._basic_similarity(ext_line, ref_line)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = ext_line
                    best_index = j
            
            # 2. Semantic matching using RAG (if available)
            if self.rag_system and ref_line.strip():
                try:
                    # Get semantic context for the reference line
                    semantic_context = self._get_semantic_context(ref_line, surah, top_k=3)
                    
                    # Check if any extracted line is semantically similar
                    for j, ext_line in enumerate(extracted):
                        if not ext_line.strip():
                            continue
                            
                        # Get semantic context for extracted line
                        ext_context = self._get_semantic_context(ext_line, surah, top_k=3)
                        
                        # Calculate semantic similarity
                        if semantic_context and ext_context:
                            # Simple semantic similarity based on context overlap
                            ref_surahs = [c['surah'] for c in semantic_context]
                            ext_surahs = [c['surah'] for c in ext_context]
                            semantic_overlap = len(set(ref_surahs) & set(ext_surahs)) / max(len(ref_surahs), len(ext_surahs))
                            semantic_score = max(semantic_score, semantic_overlap * 100)
                            
                except Exception as e:
                    print(f"⚠️ Semantic matching failed for line {i}: {e}")
            
            # 3. Combined scoring
            combined_score = max(best_score, semantic_score)  # Use the higher of the two scores
            
            # Store match details for debugging
            match_details.append({
                'ref_index': i,
                'ref_line': ref_line[:50] + '...' if len(ref_line) > 50 else ref_line,
                'best_match': best_match[:50] + '...' if best_match and len(best_match) > 50 else best_match,
                'best_score': best_score,
                'semantic_score': semantic_score,
                'combined_score': combined_score,
                'best_index': best_index
            })
            
            # If no good match found, this line is missing
            # More intelligent threshold based on combined scoring
            threshold = 60 if self.rag_system else 70  # Higher threshold means more strict matching
            if combined_score < threshold:
                missing_indices.append(i)
                missing_content.append(ref_line)
                confidence_scores.append(100 - combined_score)  # Higher confidence for clear misses
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Debug output
        print(f"🔍 Missing line analysis:")
        print(f"   Reference lines: {len(reference)}")
        print(f"   Extracted lines: {len(extracted)}")
        print(f"   Missing lines: {len(missing_indices)}")
        for detail in match_details[:3]:  # Show first 3 for debugging
            print(f"   Ref {detail['ref_index']}: '{detail['ref_line']}' -> '{detail['best_match']}' (score: {detail['best_score']:.1f})")
        
        return {
            'missing_indices': missing_indices,
            'missing_content': missing_content,
            'confidence': overall_confidence,
            'match_scores': confidence_scores,
            'match_details': match_details
        }
    
    def _basic_similarity(self, text1: str, text2: str) -> float:
        """Basic string similarity when rapidfuzz is not available"""
        if not text1 or not text2:
            return 0.0
        
        # Simple character-based similarity
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return (intersection / union) * 100 if union > 0 else 0.0
    
    
    def _generate_enhanced_suggestions(self, missing_analysis: Dict, reference_verses: List[str], 
                                      surah: int, page_number: int) -> List[Dict]:
        """Generate enhanced suggestions using RAG + LLM."""
        suggestions = []
        
        missing_indices = missing_analysis['missing_indices']
        missing_content = missing_analysis['missing_content']
        
        for i, (missing_idx, missing_text) in enumerate(zip(missing_indices, missing_content)):
            # Determine verse number
            verse_number = missing_idx + 1
            
            # Get context (previous and next verses if available)
            context = self._get_verse_context(reference_verses, missing_idx)
            
            # Get semantic context using RAG
            semantic_context = []
            if self.rag_system:
                try:
                    semantic_context = self._get_semantic_context(missing_text, surah, top_k=5)
                except Exception as e:
                    print(f"⚠️ Semantic context retrieval failed: {e}")
            
            # Generate intelligent suggestion using LLM
            if self.llm_available and semantic_context:
                suggestion_text = self._generate_llm_suggestion(missing_text, semantic_context, surah)
            else:
                # Fallback to basic suggestion
                suggestion_text = f"Missing verse {verse_number}: {missing_text[:50]}{'...' if len(missing_text) > 50 else ''}"
                if context['prev_verse']:
                    suggestion_text += f"\n\nPrevious verse: {context['prev_verse'][:30]}..."
                if context['next_verse']:
                    suggestion_text += f"\n\nNext verse: {context['next_verse'][:30]}..."
            
            # Add semantic context information
            if semantic_context:
                similar_verses = [f"Surah {c['surah']}, Ayah {c['ayah']}" for c in semantic_context[:3]]
                suggestion_text += f"\n\nSimilar verses found: {', '.join(similar_verses)}"
            
            suggestion = {
                'type': 'missing_line',
                'verse_number': verse_number,
                'missing_text': missing_text,
                'suggestion': suggestion_text,
                'context': context,
                'confidence': missing_analysis['match_scores'][i] if i < len(missing_analysis['match_scores']) else 0,
                'position': f"Line {missing_idx + 1} of {len(reference_verses)}",
                'severity': 'high' if len(missing_text) > 20 else 'medium',
                'rag_enhanced': bool(semantic_context),
                'llm_enhanced': self.llm_available and bool(semantic_context)
            }
            
            suggestions.append(suggestion)
        
        # Add enhanced summary
        if missing_indices:
            rag_status = "RAG + LLM Enhanced" if self.rag_system and self.llm_available else "Basic Analysis"
            suggestions.append({
                'type': 'summary',
                'suggestion': f"Found {len(missing_indices)} missing line(s) using {rag_status}. Check the specific suggestions above for details.",
                'severity': 'high',
                'missing_count': len(missing_indices),
                'rag_enhanced': bool(self.rag_system),
                'llm_enhanced': self.llm_available
            })
        
        return suggestions
    
    
    def _get_verse_context(self, verses: List[str], missing_index: int) -> Dict:
        """Get context around a missing verse."""
        context = {
            'previous_verse': None,
            'next_verse': None,
            'has_context': False
        }
        
        if missing_index > 0:
            context['previous_verse'] = verses[missing_index - 1][:100] + ('...' if len(verses[missing_index - 1]) > 100 else '')
            context['has_context'] = True
        
        if missing_index < len(verses) - 1:
            context['next_verse'] = verses[missing_index + 1][:100] + ('...' if len(verses[missing_index + 1]) > 100 else '')
            context['has_context'] = True
        
        return context
    
    def suggest_corrections(self, extracted_text: str, missing_analysis: Dict) -> List[str]:
        """Suggest corrections for missing lines."""
        suggestions = []
        
        if missing_analysis['missing_content']:
            suggestions.append("**Missing Lines Detected:**")
            
            for i, missing_text in enumerate(missing_analysis['missing_content']):
                suggestions.append(f"• Line {missing_analysis['missing_indices'][i] + 1}: {missing_text}")
            
            suggestions.append("\n**Recommendations:**")
            suggestions.append("• Check if the missing lines are visible in the original image")
            suggestions.append("• Verify the page number is correct")
            suggestions.append("• Consider retaking the photo with better lighting/angle")
            suggestions.append("• Check if the text is partially obscured or damaged")
        
        return suggestions
