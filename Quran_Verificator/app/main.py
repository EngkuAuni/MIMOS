import streamlit as st
import sqlite3
import tempfile
import os
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path

# Engine Modules
from modules.normalizer import ArabicNormalizer
from modules.verifier import TextVerifier
from modules.ocr_engine import OCREngine

# Constants 
DB_PATH = "Data/Tanzil_quran-uthmani.sql"

class QuranVerificator:
    """Main application class for Quran Verification Engine."""
    
    def __init__(self):
        """Initialize components."""
        self.normalizer = ArabicNormalizer()
        self.verifier = TextVerifier()
        self.ocr_engine = OCREngine()
    
    def process_file(self, uploaded_file):
        """Process an uploaded file (image or PDF)."""
        # Create a temporary file to work with
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        try:
            # Handle PDF → image conversion
            if uploaded_file.type == "application/pdf":
                st.info("📄 PDF detected. Converting first page to image...")
                pages = convert_from_path(tmp_path, dpi=350)
                img_pil = pages[0]
            else:
                img_pil = Image.open(tmp_path).convert("RGB")
            
            # Run OCR
            ocr_text = self.ocr_engine.recognize(img_pil)
            
            # Normalize and hash the text
            norm_text = self.normalizer.normalize(ocr_text)
            hash_val = self.verifier.compute_hash(norm_text)
            
            # Look up the hash in the database
            result = self.lookup_hash(hash_val)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return {
                "image": img_pil,
                "ocr_text": ocr_text,
                "norm_text": norm_text,
                "hash_val": hash_val,
                "result": result
            }
        except Exception as e:
            # Clean up on error
            os.unlink(tmp_path)
            raise e
    
    def lookup_hash(self, hash_val):
        """Look up a hash value in the database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT sura, aya FROM ayah_hash WHERE hash_full = ?", (hash_val,)
            ).fetchone()
            conn.close()
            return row
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return None

# Initialize application
verificator = QuranVerificator()

# Streamlit UI setup
st.set_page_config(page_title="Quran Verification Engine", layout="wide")
st.title("📜 Quran Verification Engine (Uthmani Edition)")

st.markdown("""
Upload a scanned image or PDF page of the Quran, and this engine will verify its integrity
against a canonical Uthmani database.
""")

uploaded_file = st.file_uploader("📤 Upload Image or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    try:
        # Process the file
        result = verificator.process_file(uploaded_file)
        
        # Display the image
        st.image(result["image"], caption="🖼 Uploaded Image", use_container_width=True)
        
        # Display OCR and verification results
        with st.spinner("🔍 Running OCR and verifying..."):
            st.markdown("---")
            st.subheader("📜 OCR Output")
            st.code(result["ocr_text"] or "[No text detected]")
            
            st.subheader("🧼 Normalized Text")
            st.code(result["norm_text"] or "[Normalization failed]")
            
            st.subheader("🔐 SHA-256 Hash")
            st.code(result["hash_val"])
            
            st.subheader("✅ Verification Result")
            if result["result"]:
                sura, aya = result["result"]
                st.success(f"✅ **Verified (Uthmani)** – Surah {sura}, Ayah {aya}")
            else:
                st.warning("⚠️ **No exact match found.** This might be due to OCR noise, different edition, or a real textual difference.")
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# Add reset button
st.markdown("---")
if st.button("🔁 Try Another File"):
    st.rerun()