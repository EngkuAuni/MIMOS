"""
Enhanced Quran Verification Engine
Integrated with QariOCR fine-tuning pipeline and multi-layer verification
"""

import streamlit as st
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import enhanced modules
from models.qari_ocr import QariOCR
from models.model_manager import ModelManager
from verification.text_verifier import TextVerifier
from verification.structural_verifier import StructuralVerifier
from verification.semantic_verifier_simple import SemanticVerifier
from verification.missing_line_detector import MissingLineDetector
from ui_components.anomaly_display import AnomalyDisplay
from utils.file_handler import load_file, convert_pdf_to_images
from preprocessing.preprocess import preprocess_image
from segmentation.verse_segmenter import segment_verses
from database.uthmani_db import UthmaniDB
from triangulation.ocr_compare import compare_ocr
from triangulation.cv_compare import compare_cv, CVPageComparator
from triangulation.hash_compare import compare_hash
from report.report_gen import generate_report
from utils.logger import get_logger

logger = get_logger()

def analyze_extracted_text(text):
    """Analyze extracted text for potential OCR issues"""
    issues = []
    
    if not text or len(text.strip()) < 10:
        issues.append("• Text is too short or empty")
    
    # Check for excessive underscores (unclear characters)
    underscore_ratio = text.count('_') / len(text) if text else 0
    if underscore_ratio > 0.1:  # More than 10% underscores
        issues.append(f"• High number of unclear characters ({underscore_ratio:.1%} underscores)")
    
    # Check for non-Arabic characters
    import re
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    arabic_ratio = arabic_chars / total_chars if total_chars > 0 else 0
    
    if arabic_ratio < 0.5:  # Less than 50% Arabic characters
        issues.append(f"• Low Arabic character ratio ({arabic_ratio:.1%})")
    
    # Note: Removed duplicate word detection as Quran legitimately repeats words
    
    # Check for very short lines (possible truncation)
    lines = text.split('\n')
    short_lines = [line for line in lines if len(line.strip()) < 5 and line.strip()]
    if len(short_lines) > len(lines) * 0.3:  # More than 30% short lines
        issues.append(f"• Many short lines detected ({len(short_lines)} out of {len(lines)})")
    
    # Count words for statistics
    words = text.split()
    
    return {
        'has_issues': len(issues) > 0,
        'issues': '\n'.join(issues) if issues else 'No issues detected',
        'arabic_ratio': arabic_ratio,
        'underscore_ratio': underscore_ratio,
        'line_count': len(lines),
        'word_count': len(words)
    }

# Page configuration
st.set_page_config(
    page_title="Quran Verification Engine",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize all components with caching"""
    try:
        # Initialize model manager
        model_manager = ModelManager()
        
        # Initialize verification components
        text_verifier = TextVerifier()
        structural_verifier = StructuralVerifier()
        semantic_verifier = SemanticVerifier()
        
        # Initialize QariOCR model for LLM functionality (eager load at startup)
        ocr_model = QariOCR("models/FT1_QariOCR", fallback_warn=True)
        
        # Missing line detector with QariOCR as LLM and TextVerifier for detailed analysis
        missing_line_detector = MissingLineDetector(
            ocr_model=ocr_model,
            text_verifier=text_verifier
        )
        
        # Initialize UI components
        anomaly_display = AnomalyDisplay()
        
        # Initialize CV page layout comparator
        try:
            cv_page_comparator = CVPageComparator()
            print("✅ CV page comparator initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize CV page comparator: {e}")
            cv_page_comparator = None
        
        # Initialize database (cached - loads once)
        db = UthmaniDB("database/quran_verses.db")
        
        # Initialize QariOCR model (cached - loads ONCE at startup)
        # First load takes 5-10 minutes, but then it's cached forever
        with st.spinner("🔄 Loading QariOCR fine-tuned model... First time only, please wait ~5-10 minutes..."):
            _ = ocr_model
        
        return {
            'model_manager': model_manager,
            'text_verifier': text_verifier,
            'structural_verifier': structural_verifier,
            'semantic_verifier': semantic_verifier,
            'missing_line_detector': missing_line_detector,
            'anomaly_display': anomaly_display,
            'cv_page_comparator': cv_page_comparator,
            'db': db,
            'ocr_model': ocr_model
        }
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        return None

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; text-align: center;'>🕌 Enhanced Quran Verification Engine</h1>
        <p style='color: white; text-align: center; margin: 10px 0 0 0; opacity: 0.9;'>
            National-Level Uthmani Mushaf Auditing with AI-Powered Multi-Layer Verification
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    components = initialize_components()
    if not components:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 System Configuration")
        
        # Model information (removed selection - using fine-tuned only)
        st.subheader("Model Information")
        st.info("🤖 Using Fine-Tuned QariOCR Model (FT1)")
        
        current_model = components['model_manager'].get_current_model()
        available_models = components['model_manager'].get_available_models()
        
        # Get fine-tuned model info (filter out base model from display)
        finetuned_models = [m for m in available_models if m['type'] == 'finetuned']
        if finetuned_models:
            selected_model_info = finetuned_models[0]
        else:
            selected_model_info = available_models[0] if available_models else {
                'name': 'FT1_QariOCR',
                'version': '1.0',
                'accuracy': {'wer': 0.045, 'cer': 0.012},
                'type': 'finetuned'
            }
        
        st.metric("Accuracy (WER)", f"{selected_model_info['accuracy']['wer']:.3f}")
        st.metric("Character Accuracy", f"{(1 - selected_model_info['accuracy']['cer']) * 100:.1f}%")
        st.metric("Model Type", selected_model_info['type'].title())
        
        # Training data info
        st.subheader("Training Data")
        training_data_info = components['model_manager'].get_training_data_info()
        if training_data_info['status'] == 'available':
            st.metric("Total Samples", training_data_info['total_samples'])
            st.metric("Training Samples", training_data_info['train_samples'])
            st.metric("Validation Samples", training_data_info['val_samples'])
        else:
            st.warning("Training data not available")
        
        # Verification settings
        st.subheader("Verification Settings")
        enable_text = st.checkbox("Text Verification", value=True)
        enable_structural = st.checkbox("Structural Verification", value=True)
        enable_semantic = st.checkbox("Semantic Verification", value=True)
        enable_visual = st.checkbox("Visual Verification", value=True)
        enable_cv_comparison = st.checkbox("📐 CV Page-Layout Comparison", value=True, 
                                         help="Computer vision-based layout and structural analysis")
        
        # Verification method selection (Three methods available)
        st.subheader("🔍 Verification Method")
        ocr_mode = st.radio(
            "Select Primary Verification Method",
            ["QariOCR Fine-Tuned (AI-based)", 
             "CV Page-Layout Comparison (requires page number)",
             "Hybrid (Show all methods)"],
            index=2,  # Default to Hybrid to show all
            help="Choose primary method. CV Comparison requires page number input."
        )
        
        # Confidence threshold
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.05
        )

        # Rendering controls (single-page PDF enforced)
        st.subheader("Document Rendering (PDF)")
        st.selectbox("PDF DPI", options=[150, 300, 600], index=1,
                     key="pdf_dpi_choice",
                     help="Single-page PDF input. 300 DPI recommended.")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Verification", "📊 Model Management", "📈 Analytics", "⚙️ Settings"])
    
    with tab1:
        verification_tab(components, selected_model_info, {
            'enable_text': enable_text,
            'enable_structural': enable_structural,
            'enable_semantic': enable_semantic,
            'enable_visual': enable_visual,
            'enable_cv_comparison': enable_cv_comparison,
            'confidence_threshold': confidence_threshold,
            'ocr_mode': ocr_mode
        })
    
    with tab2:
        model_management_tab(components)
    
    with tab3:
        analytics_tab(components)
    
    with tab4:
        settings_tab(components)

def verification_tab(components: Dict, model_info: Dict, settings: Dict):
    """Verification tab content"""
    
    st.header("📄 Document Verification")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Quran page (PDF/Image)", 
        type=["pdf", "jpg", "png", "tiff"],
        help="Upload a Quran page for verification"
    )
    
    if uploaded_file:
        # Page number input for CV comparison
        page_number = None
        if settings.get('enable_cv_comparison', False):
            st.subheader("📄 Page Information")
            page_number = st.number_input(
                "Enter Quran page number (1-604)",
                min_value=1,
                max_value=604,
                value=1,
                help="Required for pixel-perfect image comparison with reference"
            )
        
        # Process file
        with st.spinner("Processing document..."):
            try:
                # Load file with source type tracking
                # PDF inputs: high-quality, already clean, skip CV preprocessing
                # Image inputs: may need CV preprocessing for scanned/photographed pages
                # Read rendering params from session state with safe defaults
                _dpi = int(st.session_state.get("pdf_dpi_choice", 300))
                _max_pages = 1
                _first_n = 1
                images, source_type = load_file(
                    uploaded_file,
                    dpi=_dpi,
                    max_pages=_max_pages,
                    first_n_pages=_first_n
                )
                
                # Use cached database and OCR model from components
                db = components['db']
                ocr_model = components['ocr_model']
                
                # Process each page
                results = []
                for idx, img in enumerate(images, start=1):
                    st.subheader(f"Page {idx}")
                    
                    # Display images
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Original Image:**")
                        st.image(img, caption=f"Original Page {idx}", width='stretch')
                    
                    with col2:
                        # Only show preprocessing for scanned images (not PDFs)
                        if source_type == "image":
                            st.write("**Preprocessed Image:**")
                            preprocessed_img = preprocess_image(img)
                            st.image(preprocessed_img, caption=f"Preprocessed Page {idx}", width='stretch')
                            # Use preprocessed image for OCR on scanned images
                            ocr_input_img = preprocessed_img
                        else:
                            st.write("**PDF Source (No Preprocessing Needed):**")
                            st.info("✓ PDF pages are already high quality and don't require preprocessing")
                            # Use original image directly for PDFs
                            ocr_input_img = img
                    
                    # OCR extraction with source type flag
                    with st.spinner("Extracting text..."):
                        ocr_result = ocr_model.extract(ocr_input_img, source_type=source_type)
                    
                    # Display OCR Results with improved UI (from original app.py)
                    st.write("### 📝 OCR Extraction Results")
                    
                    # Get OCR results
                    qari_text = ocr_result.get("qari_text", ocr_result.get("text", ""))
                    method = ocr_result.get("method", "unknown")
                    
                    # Show QariOCR Fine-Tuned result
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                        <h4 style='color: #1f77b4; margin-top: 0;'>🤖 QariOCR Extracted Text (Fine-tuned Model):</h4>
                        <p style='font-size: 24px; direction: rtl; text-align: right; font-family: "Amiri", "Traditional Arabic", serif; line-height: 2; color: #1a1a1a;'>
                            {qari_text if qari_text else "No text extracted"}
                        </p>
                        <p style='color: #666; margin-bottom: 0;'>
                            <strong>Confidence:</strong> {ocr_result.get("confidences", [0])[0]:.1%} | 
                            <strong>Processing:</strong> {method}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    
                    # Image Comparison status - will be populated after comparison runs
                    # (Status box moved to after comparison results for proper image display)
                    
                    # Select which method to use for verification based on settings
                    verification_text = qari_text  # Default to QariOCR Fine-Tuned
                    if settings.get('ocr_mode') == "QariOCR Fine-Tuned (AI-based)":
                        verification_text = qari_text
                        st.info("ℹ️ Using QariOCR Fine-Tuned for verification")
                    elif settings.get('ocr_mode') == "CV Page-Layout Comparison (requires page number)":
                        verification_text = qari_text  # Still use OCR text for downstream processing
                        if settings.get('enable_cv_comparison', False) and page_number:
                            st.success("✅ Using CV Page-Layout Comparison for verification (structural analysis)")
                        else:
                            st.error("❌ CV Comparison selected but not enabled or page number missing")
                    else:  # Hybrid mode
                        verification_text = qari_text  # Use QariOCR as primary
                        st.info("ℹ️ Hybrid mode: Showing all verification methods for comparison")
                    
                    # Update ocr_result with selected text for downstream processing
                    ocr_result_for_verification = {
                        "text": verification_text,
                        "confidences": ocr_result.get("confidences", [0.9]),
                        "original_ocr_result": ocr_result
                    }
                    
                    # Text Quality Analysis
                    text_analysis = analyze_extracted_text(qari_text)
                    if text_analysis['has_issues']:
                        st.warning(f"""
                        🔍 **TEXT ANALYSIS DETECTED POTENTIAL ISSUES:**
                        
                        {text_analysis['issues']}
                        
                        **This analysis helps identify potential OCR quality issues.**
                        """)
                    else:
                        st.success("✅ Text analysis shows good quality extraction with no obvious issues.")
                    
                    # Verse segmentation and display
                    try:
                        verses = segment_verses(ocr_result_for_verification)
                        db_verses = db.get_verses(verses["surah"], verses["ayah_nums"])
                        
                        # Display detected surah information
                        st.write("### 📖 Detected Surah Information")
                        col_surah1, col_surah2, col_surah3 = st.columns(3)
                        with col_surah1:
                            st.metric("Surah Number", verses["surah"])
                        with col_surah2:
                            st.metric("Surah Title", verses.get("surah_title", "Unknown"))
                        with col_surah3:
                            st.metric("Detected Page", verses.get("page_num", "Unknown"))
                        
                        # Show confidence if available
                        if verses.get("confidence"):
                            confidence_emoji = "✅" if verses["confidence"] > 0.7 else "⚠️"
                            st.caption(f"{confidence_emoji} Detection confidence: {verses['confidence']:.1%}")
                        
                    except Exception as e:
                        st.error(f"Verse segmentation or DB lookup failed for page {idx}: {e}")
                        continue
                    
                    # Display extracted verses in rows for easy reading
                    if len(verses["verses"]) > 0:
                        st.write("### 📜 Extracted Verses (Line by Line)")
                        for i, verse in enumerate(verses["verses"], start=1):
                            if verse and verse.strip():  # Only show non-empty verses
                                st.markdown(f"""
                                <div style='background-color: #ffffff; padding: 15px; margin: 5px 0; border-left: 4px solid #667eea; border-radius: 5px;'>
                                    <div style='color: #666; font-size: 12px; margin-bottom: 5px;'>Verse {i}</div>
                                    <div style='font-size: 20px; direction: rtl; text-align: right; font-family: "Amiri", "Traditional Arabic", serif; color: #1a1a1a;'>
                                        {verse}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Triangulation verification
                    ocr_matches = compare_ocr(verses, db_verses)
                    cv_flags = compare_cv(preprocessed_img, verses)
                    hash_flags = compare_hash(verses, db_verses)
                    
                    # Missing Line Detection and Suggestions
                    missing_line_analysis = None
                    if verses and db_verses:
                        with st.spinner("🔍 Analyzing for missing lines..."):
                            try:
                                # Extract text from db_verses (they are dictionaries with 'text' key)
                                reference_texts = []
                                for verse in db_verses:
                                    if isinstance(verse, dict) and 'text' in verse:
                                        reference_texts.append(verse['text'])
                                    elif isinstance(verse, str):
                                        reference_texts.append(verse)
                                    else:
                                        # Handle other possible structures
                                        reference_texts.append(str(verse))
                                
                                st.write(f"🔍 **Debug Info:** Analyzing {len(reference_texts)} reference verses against extracted text")
                                
                                # Get actual surah from page_number if available
                                actual_surah = verses.get('surah', 1) if isinstance(verses, dict) else 1
                                if page_number:
                                    page_info = components['db'].get_page_info(page_number)
                                    if page_info:
                                        actual_surah = page_info.get('sura_start', actual_surah)
                                
                                # Detect and display surah mismatch with detailed info
                                detected_surah = verses.get('surah', 1) if isinstance(verses, dict) else 1
                                
                                if page_number and actual_surah and actual_surah != detected_surah:
                                    st.error(f"""
                                    ⚠️ **SURAH MISMATCH DETECTED**
                                    
                                    - **Expected:** Surah {actual_surah} (for page {page_number})
                                    - **Detected:** Surah {detected_surah}
                                    - **Impact:** Comparing against wrong verses may cause false positives
                                    - **Solution:** Using page number to correct surah
                                    """)
                                
                                missing_line_analysis = components['missing_line_detector'].detect_missing_lines(
                                    qari_text, 
                                    reference_texts,
                                    detected_surah,  # Use detected surah for RAG context
                                    page_number or 1,
                                    actual_surah=actual_surah  # Use actual surah for validation
                                )
                                
                                # Show comprehensive results
                                missing_count = len(missing_line_analysis.get('missing_indices', []))
                                anomaly_count = len(missing_line_analysis.get('anomaly_indices', []))
                                st.write(f"🔍 **Analysis Result:** {missing_count} missing lines, {anomaly_count} line anomalies detected")
                                
                            except Exception as e:
                                st.warning(f"⚠️ Missing line analysis failed: {e}")
                                missing_line_analysis = None
                    
                    # CV Page-Layout Comparison
                    cv_layout_result = None
                    if settings.get('enable_cv_comparison', False) and page_number:
                        with st.spinner("🔍 Performing CV page-layout comparison..."):
                            try:
                                # Check if cv_page_comparator is available
                                if 'cv_page_comparator' not in components or components['cv_page_comparator'] is None:
                                    st.error("❌ CV page comparator not initialized")
                                    cv_layout_result = {"success": False, "error": "CV page comparator not available"}
                                else:
                                    cv_layout_result = components['cv_page_comparator'].compare_page_layout(preprocessed_img, page_number)
                                
                                if cv_layout_result['success']:
                                    st.write("### 📐 CV Page-Layout Comparison Results")
                                    
                                    # Display layout analysis
                                    layout_analysis = cv_layout_result.get('layout_analysis', {})
                                    structural_diffs = cv_layout_result.get('structural_differences', {})
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Layout Analysis:**")
                                        st.write(f"• Text regions (uploaded): {layout_analysis.get('text_regions_uploaded', 0)}")
                                        st.write(f"• Text regions (reference): {layout_analysis.get('text_regions_reference', 0)}")
                                        st.write(f"• Region count difference: {layout_analysis.get('region_count_difference', 0)}")
                                        st.write(f"• Layout consistency: {'✅ Good' if layout_analysis.get('layout_consistency', False) else '❌ Issues detected'}")
                                    
                                    with col2:
                                        st.write("**Structural Differences:**")
                                        st.write(f"• Difference count: {structural_diffs.get('difference_count', 0)}")
                                        st.write(f"• Total difference area: {structural_diffs.get('total_difference_area', 0):.0f} pixels")
                                        st.write(f"• Similarity score: {cv_layout_result.get('similarity_score', 0):.3f}")
                                        st.write(f"• Layout match: {'✅ Yes' if cv_layout_result.get('is_layout_match', False) else '❌ No'}")
                                    
                                    # Visual comparison
                                    st.write("**Visual Comparison:**")
                                    cv_col1, cv_col2 = st.columns(2)
                                    
                                    with cv_col1:
                                        st.write("**Uploaded Page**")
                                        st.image(preprocessed_img, caption="Your uploaded page", use_column_width=True)
                                    
                                    with cv_col2:
                                        st.write("**Reference Page**")
                                        st.image(cv_layout_result['reference_image'], caption=f"Reference page {page_number}", use_column_width=True)
                                    
                                    # Show summary status box
                                    st.markdown(f"""
                                    <div style='background-color: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2196f3;'>
                                        <h4 style='color: #0d47a1; margin-top: 0;'>📐 CV Page-Layout Comparison Summary:</h4>
                                        <p style='font-size: 16px; color: #0d47a1; margin-bottom: 10px;'>
                                            <strong>Method:</strong> OpenCV + ORB Features + Layout Analysis<br>
                                            <strong>Reference:</strong> Page {page_number} from database<br>
                                            <strong>Result:</strong> {cv_layout_result['similarity_score']:.3f} similarity,
                                            {structural_diffs.get('difference_count', 0)} structural difference(s)<br>
                                            <strong>Alignment:</strong> {cv_layout_result['alignment_confidence']:.1%} confidence
                                        </p>
                                        <div style='background-color: #ffffff; padding: 10px; border-radius: 5px; border: 1px solid #bbdefb;'>
                                            <p style='margin: 0; font-size: 14px; color: #0d47a1;'>
                                                ✅ <strong>Advantage:</strong> Layout structure analysis |
                                                Text region detection and margin analysis
                                            </p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                else:
                                    st.error(f"❌ CV layout comparison failed: {cv_layout_result.get('error', 'Unknown error')}")
                                    
                                    # Show failed status box
                                    st.markdown(f"""
                                    <div style='background-color: #f8d7da; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #dc3545;'>
                                        <h4 style='color: #721c24; margin-top: 0;'>📐 CV Page-Layout Comparison (Failed):</h4>
                                        <p style='font-size: 16px; color: #721c24; margin-bottom: 0;'>
                                            Error: {cv_layout_result.get('error', 'Unknown error')}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                            except Exception as e:
                                st.error(f"❌ CV layout comparison error: {str(e)}")
                    
                    # Show disabled status if CV comparison not enabled
                    if not settings.get('enable_cv_comparison', False) or not page_number:
                        st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #6c757d;'>
                            <h4 style='color: #495057; margin-top: 0;'>📐 CV Page-Layout Comparison (Disabled):</h4>
                            <p style='font-size: 16px; color: #6c757d; margin-bottom: 0;'>
                                Enable "CV Page-Layout Comparison" in sidebar and enter page number to activate this method.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Missing Line Analysis Display
                    if missing_line_analysis:
                        st.write("### 🔍 Missing Line Analysis")
                        
                        # Show surah mismatch if detected
                        if missing_line_analysis.get('surah_mismatch'):
                            st.warning("⚠️ Analysis may be comparing against wrong surah. Consider providing page number for accuracy.")
                        
                        # Show analysis status with RAG + LLM info
                        rag_status = "🧠 RAG + LLM Enhanced" if any(s.get('rag_enhanced', False) for s in missing_line_analysis.get('suggestions', [])) else "📝 Basic Analysis"
                        st.info(f"ℹ️ **Missing Line Analysis** - {rag_status}")
                        
                        # Show missing line count
                        missing_count = len(missing_line_analysis.get('missing_indices', []))
                        anomaly_count = len(missing_line_analysis.get('anomaly_indices', []))
                        
                        if missing_count > 0 or anomaly_count > 0:
                            st.warning(f"⚠️ **{missing_count} missing line(s), {anomaly_count} anomaly/anomalies detected!**")
                        else:
                            st.success("✅ **No missing lines or anomalies detected**")
                        
                        # Display missing lines
                        for suggestion in missing_line_analysis.get('suggestions', []):
                            if suggestion['type'] == 'missing_line':
                                # Determine enhancement status
                                enhancement_badge = ""
                                if suggestion.get('rag_enhanced', False) and suggestion.get('llm_enhanced', False):
                                    enhancement_badge = "🧠 RAG + LLM Enhanced"
                                elif suggestion.get('rag_enhanced', False):
                                    enhancement_badge = "🔍 RAG Enhanced"
                                else:
                                    enhancement_badge = "📝 Basic Analysis"
                                
                                st.markdown(f"""
                                <div style='background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ffc107;'>
                                    <h4 style='color: #856404; margin-top: 0;'>❌ Missing Line {suggestion['verse_number']} - {enhancement_badge}</h4>
                                    <p style='color: #856404; margin-bottom: 10px;'><strong>Missing Text:</strong> {suggestion['missing_text']}</p>
                                    <p style='color: #856404; margin-bottom: 5px;'><strong>Position:</strong> {suggestion['position']}</p>
                                    <p style='color: #856404; margin-bottom: 5px;'><strong>Confidence:</strong> {suggestion['confidence']:.1f}%</p>
                                    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px;'>
                                        <p style='color: #495057; margin: 0; font-size: 14px;'><strong>Suggestion:</strong></p>
                                        <p style='color: #495057; margin: 5px 0 0 0; font-size: 13px;'>{suggestion['suggestion']}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Show summary
                        summary_suggestion = next((s for s in missing_line_analysis.get('suggestions', []) if s['type'] == 'summary'), None)
                        if summary_suggestion:
                            st.info(f"📋 **Summary:** {summary_suggestion['suggestion']}")
                        
                        # Show correction suggestions
                        correction_suggestions = components['missing_line_detector'].suggest_corrections(
                            qari_text, missing_line_analysis
                        )
                        if correction_suggestions:
                            st.write("**💡 Recommendations:**")
                            for suggestion in correction_suggestions:
                                st.write(f"• {suggestion}")
                    
                    # Comparison section
                    st.write("### 📊 Verification Results")
                    
                    # Create metrics row
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        avg_score = sum([m.get("score", 0) for m in ocr_matches]) / max(len(ocr_matches), 1)
                        st.metric("OCR Accuracy", f"{avg_score:.1f}%", 
                                 delta="Good" if avg_score >= 90 else "Needs Review",
                                 delta_color="normal" if avg_score >= 90 else "inverse")
                    with col_b:
                        anomaly_count = sum([1 for h in hash_flags if h.get("hash_mismatch", False)])
                        st.metric("Mismatches Found", anomaly_count,
                                 delta="None" if anomaly_count == 0 else f"{anomaly_count} issue(s)",
                                 delta_color="normal" if anomaly_count == 0 else "inverse")
                    with col_c:
                        cv_issues = sum([1 for c in cv_flags if c.get("cv_flag", False)])
                        st.metric("Visual Flags", cv_issues,
                                 delta="Clean" if cv_issues == 0 else "Check",
                                 delta_color="normal" if cv_issues == 0 else "inverse")
                    
                    # Quality Check: Compare with Database (for verification only)
                    with st.expander("🔍 Advanced: Database Verification (Optional)", expanded=False):
                        st.info("""
                        **What is this?** This section compares the OCR-extracted text with the correct Quranic text from our database. 
                        It helps verify if the OCR is working accurately by showing:
                        - **Match %**: How similar the extracted text is to the database (higher is better)
                        - **Status**: Whether the verse matches the database correctly
                        
                        ℹ️ This is mainly for quality assurance and debugging purposes.
                        """)
                        
                        if len(verses["verses"]) > 0:
                            table_html = """
                            <style>
                            .ocr-table { 
                                width: 100%; 
                                border-collapse: collapse; 
                                font-size: 1em;
                                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                border-radius: 8px;
                                overflow: hidden;
                            }
                            .ocr-table th { 
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                padding: 12px;
                                text-align: left;
                                font-weight: 600;
                            }
                            .ocr-table td { 
                                border: 1px solid #e0e0e0; 
                                padding: 12px;
                                vertical-align: top;
                            }
                            .ocr-table tr:hover {
                                background-color: #f5f5f5;
                            }
                            .anomaly { background-color: #ffe6e6 !important; }
                            .ok { background-color: #e6ffe6 !important; }
                            .arabic-text {
                                font-size: 18px;
                                direction: rtl;
                                text-align: right;
                                font-family: "Amiri", "Traditional Arabic", serif;
                                line-height: 1.8;
                                color: #1a1a1a;
                            }
                            .status-badge {
                                padding: 4px 12px;
                                border-radius: 12px;
                                font-weight: 600;
                                display: inline-block;
                            }
                            .status-ok {
                                background-color: #4caf50;
                                color: white;
                            }
                            .status-anomaly {
                                background-color: #f44336;
                                color: white;
                            }
                            </style>
                            <table class="ocr-table">
                            <thead>
                            <tr>
                                <th style="width: 5%;">#</th>
                                <th style="width: 35%;">OCR Extracted</th>
                                <th style="width: 35%;">Database Reference</th>
                                <th style="width: 10%;">Match %</th>
                                <th style="width: 15%;">Status</th>
                            </tr>
                            </thead>
                            <tbody>
                            """

                            for i, (v, ocr_m, cv_f, hash_f) in enumerate(zip(verses["verses"], ocr_matches, cv_flags, hash_flags), start=1):
                                anomaly = any([ocr_m.get("score", 100) < 90, cv_f.get("cv_flag", False), hash_f.get("hash_mismatch", False)])
                                row_class = "anomaly" if anomaly else "ok"
                                status_class = "status-anomaly" if anomaly else "status-ok"
                                status_text = "❌ Mismatch" if anomaly else "✅ Match"
                                score = ocr_m.get("score", 0)
                                
                                table_html += f"""
                                <tr class="{row_class}">
                                    <td style="text-align: center; font-weight: bold;">{i}</td>
                                    <td class="arabic-text">{v if v else "—"}</td>
                                    <td class="arabic-text">{ocr_m.get("db_verse", "—")}</td>
                                    <td style="text-align: center; font-weight: bold; color: {'#4caf50' if score >= 90 else '#f44336'};">{score:.1f}%</td>
                                    <td style="text-align: center;"><span class="status-badge {status_class}">{status_text}</span></td>
                                </tr>
                                """
                            table_html += "</tbody></table>"
                            st.markdown(table_html, unsafe_allow_html=True)
                        else:
                            st.info("No verses detected in this page.")
                    
                    # Store results for reporting
                    result = {
                        "page": idx,
                        "ocr": ocr_matches,
                        "cv": cv_flags,
                        "hash": hash_flags,
                        "confidences": ocr_result["confidences"],
                    }
                    results.append(result)
                
                # Export results
                if results and st.button("📊 Generate Report"):
                    try:
                        report_path = generate_report(results, format="pdf")
                        st.success(f"Report generated: {report_path}")
                    except Exception as e:
                        st.error(f"Failed to generate report: {e}")
                
            except Exception as e:
                st.error(f"Processing failed: {e}")
                logger.error(f"Processing error: {e}")

def perform_verification(image, ocr_result, components, settings):
    """Perform multi-layer verification"""
    verification_results = {}
    
    # Text verification
    if settings['enable_text']:
        with st.spinner("Performing text verification..."):
            # Get reference text (placeholder)
            reference_text = "الحمد لله رب العالمين"  # This would come from database
            text_results = components['text_verifier'].verify_text(
                ocr_result.get("text", ""), 
                reference_text
            )
            verification_results['text'] = text_results
    
    # Structural verification
    if settings['enable_structural']:
        with st.spinner("Performing structural verification..."):
            # Segment verses
            verses = segment_verses(ocr_result)
            structural_results = components['structural_verifier'].verify_structure(
                image, 
                ocr_result.get("text", ""), 
                page_number=1  # This would be extracted from image
            )
            verification_results['structural'] = structural_results
    
    # Semantic verification
    if settings['enable_semantic']:
        with st.spinner("Performing semantic verification..."):
            from verification.semantic_verifier import VerificationContext
            context = VerificationContext(
                surah_name="Al-Fatiha",
                ayah_number=1,
                page_number=1,
                surrounding_verses=[]
            )
            semantic_results = components['semantic_verifier'].verify_semantics(
                ocr_result.get("text", ""),
                "الحمد لله رب العالمين",  # Reference text
                context
            )
            verification_results['semantic'] = semantic_results
    
    return verification_results

def display_verification_results(verification_results, anomaly_display):
    """Display verification results with anomaly highlighting"""
    
    st.write("### 🔍 Verification Results")
    
    # Overall anomaly summary
    anomaly_display.display_anomaly_summary(verification_results)
    
    # Detailed results for each verification method
    for method, results in verification_results.items():
        with st.expander(f"{method.title()} Verification", expanded=False):
            if method == 'text':
                display_text_verification(results, anomaly_display)
            elif method == 'structural':
                display_structural_verification(results, anomaly_display)
            elif method == 'semantic':
                display_semantic_verification(results, anomaly_display)

def display_text_verification(results, anomaly_display):
    """Display text verification results"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Character Accuracy", f"{results.get('character_accuracy', 0):.1f}%")
        st.metric("Diacritic Accuracy", f"{results.get('diacritic_accuracy', 0):.1f}%")
        st.metric("Hash Match", "✅" if results.get('hash_match', False) else "❌")
    
    with col2:
        if results.get('character_anomalies'):
            anomaly_display.display_character_anomalies(results['character_anomalies'])
        
        if results.get('diacritic_anomalies'):
            anomaly_display.display_diacritic_anomalies(results['diacritic_anomalies'])
    
    if results.get('suggestions'):
        anomaly_display.display_suggestions(results['suggestions'])

def display_structural_verification(results, anomaly_display):
    """Display structural verification results"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Layout Compliance", f"{results.get('layout_verification', {}).get('margin_ratio', 0) * 100:.1f}%")
        st.metric("Verse Count", results.get('verse_segmentation', {}).get('ayah_count', 0))
        st.metric("Surah Match", "✅" if results.get('surah_identification', {}).get('surah_match', False) else "❌")
    
    with col2:
        # Display structural details
        if results.get('verse_segmentation'):
            verse_info = results['verse_segmentation']
            st.write(f"**Ayah Numbers:** {verse_info.get('ayah_numbers', [])}")
            st.write(f"**Has Bismillah:** {'✅' if verse_info.get('has_bismillah', False) else '❌'}")

def display_semantic_verification(results, anomaly_display):
    """Display semantic verification results"""
    anomaly_display.display_semantic_analysis(results)
    
    if results.get('anomaly_explanations'):
        st.write("### 🔍 Anomaly Explanations")
        for explanation in results['anomaly_explanations']:
            severity_color = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }.get(explanation.get('severity', 'low'), '⚪')
            
            st.write(f"{severity_color} **{explanation.get('type', 'Unknown')}:** {explanation.get('description', 'No description')}")

def model_management_tab(components):
    """Model management tab content"""
    st.header("🤖 Model Management")
    
    model_manager = components['model_manager']
    
    # Available models
    st.subheader("Available Models")
    models = model_manager.get_available_models()
    
    for model in models:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{model['name']}** (v{model['version']})")
                st.caption(f"Type: {model['type']} | Status: {model['status']}")
            
            with col2:
                st.metric("WER", f"{model['accuracy']['wer']:.3f}")
            
            with col3:
                st.metric("CER", f"{model['accuracy']['cer']:.3f}")
            
            with col4:
                if model['type'] == 'finetuned':
                    if st.button("Delete", key=f"delete_{model['name']}"):
                        if model_manager.delete_model(model['name']):
                            st.success("Model deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete model")
    
    # Start new training
    st.subheader("Start New Training")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_name = st.text_input("Model Name", value=f"qari-ocr-v{len([m for m in models if m['type'] == 'finetuned']) + 1}")
        platform = st.selectbox("Training Platform", ["colab", "kaggle"])
    
    with col2:
        if st.button("🚀 Start Training"):
            training_info = model_manager.start_training(
                platform=platform,
                model_name=model_name
            )
            
            st.success("Training started!")
            st.write("**Instructions:**")
            for instruction in training_info['instructions']:
                st.write(f"• {instruction}")
    
    # Training status
    st.subheader("Training Status")
    training_models = [m for m in models if m['type'] == 'finetuned']
    
    for model in training_models:
        status = model_manager.get_training_status(model['name'])
        if status.get('status') == 'preparing':
            st.info(f"**{model['name']}** - Preparing for training")
        elif status.get('status') == 'completed':
            st.success(f"**{model['name']}** - Training completed")

def analytics_tab(components):
    """Analytics tab content"""
    st.header("📈 Analytics & Performance")
    
    # Model performance comparison
    st.subheader("Model Performance Comparison")
    
    models = components['model_manager'].get_available_models()
    
    if len(models) > 1:
        # Create performance chart
        df = pd.DataFrame([
            {
                'Model': f"{m['name']} v{m['version']}",
                'WER': m['accuracy']['wer'],
                'CER': m['accuracy']['cer'],
                'Type': m['type']
            }
            for m in models
        ])
        
        fig = px.bar(
            df, 
            x='Model', 
            y=['WER', 'CER'],
            title="Model Performance Comparison",
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Training data statistics
    st.subheader("Training Data Statistics")
    
    training_data_info = components['model_manager'].get_training_data_info()
    
    if training_data_info['status'] == 'available':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Samples", training_data_info['total_samples'])
        
        with col2:
            st.metric("Training Samples", training_data_info['train_samples'])
        
        with col3:
            st.metric("Validation Samples", training_data_info['val_samples'])
        
        # Dataset composition
        if 'metadata' in training_data_info:
            metadata = training_data_info['metadata']
            if 'sources' in metadata:
                sources = metadata['sources']
                
                fig = px.pie(
                    values=list(sources.values()),
                    names=list(sources.keys()),
                    title="Dataset Composition"
                )
                st.plotly_chart(fig, use_container_width=True)

def settings_tab(components):
    """Settings tab content"""
    st.header("⚙️ System Settings")
    
    # Verification settings
    st.subheader("Verification Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Text Verification**")
        character_threshold = st.slider("Character Accuracy Threshold", 0.0, 100.0, 95.0)
        diacritic_threshold = st.slider("Diacritic Accuracy Threshold", 0.0, 100.0, 90.0)
    
    with col2:
        st.write("**Semantic Verification**")
        semantic_threshold = st.slider("Semantic Similarity Threshold", 0.0, 100.0, 80.0)
        contextual_threshold = st.slider("Contextual Accuracy Threshold", 0.0, 100.0, 75.0)
    
    # Model selection
    st.subheader("Model Version")
    try:
        model_manager: ModelManager = components.get('model_manager') if isinstance(components, dict) else ModelManager()
        available = model_manager.get_available_models()
        names = [m.get('name', m.get('path')) for m in available]
        versions = [m.get('version', '') for m in available]
        display = [f"{n} (v{v})" if v else n for n, v in zip(names, versions)]
        current = model_manager.get_current_model()
        current_display = f"{current.get('name', current.get('path'))} (v{current.get('version', '')})"
        selection = st.selectbox("Select OCR Model Adapter", options=display, index=(display.index(current_display) if current_display in display else 0))
        if st.button("Switch Model"):
            # Map selection back to version and set current
            idx = display.index(selection)
            sel_version = versions[idx]
            ok = model_manager.set_current_model(sel_version)
            if ok:
                st.success("Model selection saved. Please rerun app or new inferences will use the selected adapter.")
            else:
                st.error("Failed to switch model. Make sure the adapter folder exists under models/.")
    except Exception as e:
        st.warning(f"Model selection unavailable: {e}")

    # System settings
    st.subheader("System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_caching = st.checkbox("Enable Caching", value=True)
        max_file_size = st.number_input("Max File Size (MB)", value=50, min_value=1, max_value=500)
    
    with col2:
        enable_gpu = st.checkbox("Enable GPU", value=True)
        batch_size = st.number_input("Batch Size", value=1, min_value=1, max_value=8)
    
    if st.button("💾 Save Settings"):
        # Save settings to configuration file
        settings = {
            'verification': {
                'character_threshold': character_threshold,
                'diacritic_threshold': diacritic_threshold,
                'semantic_threshold': semantic_threshold,
                'contextual_threshold': contextual_threshold
            },
            'system': {
                'enable_caching': enable_caching,
                'max_file_size': max_file_size,
                'enable_gpu': enable_gpu,
                'batch_size': batch_size
            }
        }
        
        with open('config/user_settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        st.success("Settings saved!")

if __name__ == "__main__":
    main()
