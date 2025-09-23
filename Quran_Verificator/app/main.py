import os
import tempfile
import streamlit as st
from PIL import Image
import cv2
import numpy as np

# Import modules
from src.database import QuranDatabase
from src.preprocessing import ImagePreprocessor
from src.matching import PageMatcher
from src.ocr_engine import OCREngine
from src.normalizer import ArabicNormalizer
from src.verifier import TextVerifier
from src.diff_engine import DiffGenerator
from src.llm_explainer import LLMExplainer
from src.pdf_generator import PDFGenerator

# Set page config
st.set_page_config(
    page_title="Quran Verificator",
    page_icon="📚",
    layout="wide"
)

# Initialize components
@st.cache_resource
def load_components():
    db = QuranDatabase()
    preprocessor = ImagePreprocessor()
    matcher = PageMatcher()
    ocr = OCREngine()
    normalizer = ArabicNormalizer()
    verifier = TextVerifier()
    diff_generator = DiffGenerator()
    llm_explainer = LLMExplainer()
    pdf_generator = PDFGenerator()
    
    return {
        'db': db,
        'preprocessor': preprocessor,
        'matcher': matcher,
        'ocr': ocr,
        'normalizer': normalizer,
        'verifier': verifier,
        'diff_generator': diff_generator,
        'llm_explainer': llm_explainer,
        'pdf_generator': pdf_generator
    }

components = load_components()

# Initialize session state
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'verification_result' not in st.session_state:
    st.session_state.verification_result = None
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = None
if 'diff_html' not in st.session_state:
    st.session_state.diff_html = None
if 'explanation' not in st.session_state:
    st.session_state.explanation = None
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'temp_image_path' not in st.session_state:
    st.session_state.temp_image_path = None

# Title and description
st.title("Quran Verificator")
st.markdown("""
This tool verifies Quran text from images against canonical references.
Upload an image of a Quran page to verify its integrity.
""")

# Sidebar
st.sidebar.header("Settings")
verification_mode = st.sidebar.radio(
    "Verification Mode",
    ["Automatic", "Edition-Locked", "Manual OCR"]
)

if verification_mode == "Edition-Locked":
    edition = st.sidebar.selectbox(
        "Edition",
        ["madani", "indo-pak", "tajweed"]
    )

use_llm = st.sidebar.checkbox("Use LLM for Explanation", value=True)

# File uploader
uploaded_file = st.file_uploader("Upload an image of Quran text", type=["jpg", "jpeg", "png"])

# Main workflow
if uploaded_file is not None:
    # Save uploaded image to a temporary file
    if st.session_state.temp_image_path is None or uploaded_file.name != os.path.basename(st.session_state.temp_image_path):
        # New file uploaded, reset state
        st.session_state.processed_image = None
        st.session_state.verification_result = None
        st.session_state.ocr_text = None
        st.session_state.diff_html = None
        st.session_state.explanation = None
        st.session_state.pdf_path = None
        
        # Save the new file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp:
            temp.write(uploaded_file.getvalue())
            st.session_state.temp_image_path = temp.name
    
    # Display original image
    image = Image.open(st.session_state.temp_image_path)
    st.image(image, caption="Original Image", use_container_width=True)
    
    # Process button
    if st.button("Process Image") or st.session_state.processed_image is not None:
        # Process the image
        if st.session_state.processed_image is None:
            with st.spinner("Processing image..."):
                # Preprocess image
                preprocessed = components['preprocessor'].process_image(st.session_state.temp_image_path)
                st.session_state.processed_image = preprocessed
        
        # Display preprocessed image
        st.subheader("Preprocessed Image")
        st.image(st.session_state.processed_image['binary'], caption="Preprocessed Image", use_container_width=True)
        
        # Process according to selected mode
        if verification_mode == "Automatic":
            # Try page matching first
            match_result = components['matcher'].match_page(st.session_state.processed_image['binary'])
            
            if match_result:
                # Page matched
                edition, page, similarity = match_result
                st.success(f"Page matched: Edition {edition}, Page {page} (Similarity: {similarity:.2%})")
                
                # Use edition-locked verification
                if st.session_state.ocr_text is None:
                    with st.spinner("Performing OCR..."):
                        st.session_state.ocr_text = components['ocr'].recognize(
                            st.session_state.processed_image['pil_image']
                        )
                
                # Display OCR text
                st.subheader("Extracted Text")
                st.text_area("OCR Text", st.session_state.ocr_text, height=150)
                
                # Verify against known page
                if st.session_state.verification_result is None:
                    with st.spinner("Verifying text..."):
                        st.session_state.verification_result = components['verifier'].verify_page(
                            page, edition, st.session_state.ocr_text, components['db']
                        )
            else:
                # No page match, fall back to OCR and open verification
                if st.session_state.ocr_text is None:
                    with st.spinner("Performing OCR..."):
                        st.session_state.ocr_text = components['ocr'].recognize(
                            st.session_state.processed_image['pil_image']
                        )
                
                # Display OCR text
                st.subheader("Extracted Text")
                st.text_area("OCR Text", st.session_state.ocr_text, height=150)
                
                # Verify text
                if st.session_state.verification_result is None:
                    with st.spinner("Verifying text..."):
                        st.session_state.verification_result = components['verifier'].verify_text(
                            st.session_state.ocr_text, components['db']
                        )
        
        elif verification_mode == "Edition-Locked":
            # Manual page entry
            page = st.number_input("Page Number", min_value=1, max_value=604, value=1)
            
            # Perform OCR
            if st.session_state.ocr_text is None:
                with st.spinner("Performing OCR..."):
                    st.session_state.ocr_text = components['ocr'].recognize(
                        st.session_state.processed_image['pil_image']
                    )
            
            # Display OCR text
            st.subheader("Extracted Text")
            st.text_area("OCR Text", st.session_state.ocr_text, height=150)
            
            # Verify against known page
            if st.button("Verify") or st.session_state.verification_result is not None:
                if st.session_state.verification_result is None:
                    with st.spinner("Verifying text..."):
                        st.session_state.verification_result = components['verifier'].verify_page(
                            page, edition, st.session_state.ocr_text, components['db']
                        )
        
        else:  # Manual OCR
            # Draw a region selector
            st.subheader("Select Region for OCR (Optional)")
            
            # For simplicity, we'll just use the whole image for now
            # In a real app, you'd implement a region selector
            
            # Perform OCR
            if st.session_state.ocr_text is None:
                with st.spinner("Performing OCR..."):
                    st.session_state.ocr_text = components['ocr'].recognize(
                        st.session_state.processed_image['pil_image']
                    )
            
            # Display OCR text
            st.subheader("Extracted Text")
            st.text_area("OCR Text", st.session_state.ocr_text, height=150)
            
            # Manual verification
            if st.button("Verify") or st.session_state.verification_result is not None:
                if st.session_state.verification_result is None:
                    with st.spinner("Verifying text..."):
                        st.session_state.verification_result = components['verifier'].verify_text(
                            st.session_state.ocr_text, components['db']
                        )
        
        # Display verification results
        if st.session_state.verification_result:
            st.subheader("Verification Results")
            
            # Display status badge
            if st.session_state.verification_result['status'] == 'exact':
                st.success("✅ Verified")
            elif st.session_state.verification_result['status'] == 'near':
                st.warning("⚠️ Near Match")
            else:
                st.error("❌ No Match")
            
            # Show details based on verification mode
            if verification_mode == "Automatic" or verification_mode == "Manual OCR":
                # Open verification
                if 'ayah' in st.session_state.verification_result and st.session_state.verification_result['ayah']:
                    sura, aya = st.session_state.verification_result['ayah']
                    st.info(f"Matched to Surah {sura}, Ayah {aya}")
                
                if 'similarity' in st.session_state.verification_result:
                    st.metric("Similarity", f"{st.session_state.verification_result['similarity']:.2%}")
                
                if 'text' in st.session_state.verification_result and st.session_state.verification_result['text']:
                    st.subheader("Reference Text")
                    st.text_area("Canonical Text", st.session_state.verification_result['text'], height=150)
                    
                    # Generate diff
                    if st.session_state.diff_html is None:
                        st.session_state.diff_html = components['diff_generator'].generate_html_diff(
                            st.session_state.verification_result['text'],
                            st.session_state.ocr_text
                        )
                    
                    # Display diff
                    st.subheader("Differences")
                    st.markdown(st.session_state.diff_html, unsafe_allow_html=True)
                    
                    # Generate explanation if requested
                    if use_llm and st.session_state.explanation is None:
                        with st.spinner("Generating explanation..."):
                            char_diff = components['diff_generator'].generate_character_diff(
                                st.session_state.verification_result['text'],
                                st.session_state.ocr_text
                            )
                            
                            st.session_state.explanation = components['llm_explainer'].explain_difference(
                                st.session_state.verification_result['text'],
                                st.session_state.ocr_text,
                                char_diff
                            )
                    
                    # Display explanation
                    if use_llm and st.session_state.explanation:
                        st.subheader("Explanation")
                        st.info(st.session_state.explanation)
            else:
                # Edition-locked verification
                st.info(f"Edition: {edition}, Page: {st.session_state.verification_result['page']}")
                
                # Display matches
                for match in st.session_state.verification_result['matches']:
                    if match['status'] == 'exact':
                        st.success(f"Surah {match['sura']}, Ayah {match['aya']}: Exact Match")
                    elif match['status'] == 'near':
                        st.warning(f"Surah {match['sura']}, Ayah {match['aya']}: Near Match ({match['similarity']:.2%})")
                    else:
                        st.error(f"Surah {match['sura']}, Ayah {match['aya']}: No Match")
            
            # Generate PDF report
            if st.button("Generate PDF Report") or st.session_state.pdf_path:
                if st.session_state.pdf_path is None:
                    with st.spinner("Generating PDF report..."):
                        st.session_state.pdf_path = components['pdf_generator'].generate_report(
                            st.session_state.temp_image_path,
                            st.session_state.ocr_text,
                            st.session_state.verification_result,
                            st.session_state.diff_html,
                            st.session_state.explanation
                        )
                
                # Provide download link
                with open(st.session_state.pdf_path, "rb") as file:
                    st.download_button(
                        label="Download PDF Report",
                        data=file,
                        file_name="quran_verification_report.pdf",
                        mime="application/pdf"
                    )
    
    # Reset button
    if st.button("Reset"):
        # Clean up temporary files
        if st.session_state.temp_image_path and os.path.exists(st.session_state.temp_image_path):
            os.unlink(st.session_state.temp_image_path)
        
        if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
            os.unlink(st.session_state.pdf_path)
        
        # Reset session state
        st.session_state.processed_image = None
        st.session_state.verification_result = None
        st.session_state.ocr_text = None
        st.session_state.diff_html = None
        st.session_state.explanation = None
        st.session_state.pdf_path = None
        st.session_state.temp_image_path = None
        
        # Rerun to clear the UI
        st.rerun()

# Display instructions if no file is uploaded
else:
    st.info("Please upload an image to begin verification.")