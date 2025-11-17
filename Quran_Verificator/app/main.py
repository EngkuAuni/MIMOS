import streamlit as st
import sqlite3
import tempfile
import os
import sys
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
import cv2
import numpy as np

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Engine Modules
from modules.normalizer import ArabicNormalizer
from modules.verifier import TextVerifier
from modules.ocr_engine import OCREngine
from modules.matching import PageMatcher
from modules.database import QuranDatabase

# Constants
db_path = "Data/quran.db"

class QuranVerificator:
    """Main application class for Quran Verification Engine (ORB+SIFT preferred, OCR fallback)."""

    def __init__(self):
        self.normalizer = ArabicNormalizer()
        self.verifier = TextVerifier()
        self.ocr_engine = OCREngine()
        self.page_matcher = PageMatcher(descriptors_dir="Data/assets/orb_sift")
        self.db = QuranDatabase(db_path)

    def process_file(self, uploaded_file):
        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            # Convert PDF to image (first page) or load image directly
            if uploaded_file.type == "application/pdf":
                st.info("📄 PDF detected. Converting first page to image...")
                pages = convert_from_path(tmp_path, dpi=350)
                img_pil = pages[0]
            else:
                img_pil = Image.open(tmp_path).convert("RGB")

            # Convert PIL to OpenCV format for matching
            cv_image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2GRAY)
            
            # Enhance image for better feature detection
            # 1. Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            cv_image = clahe.apply(cv_image)
            
            # 2. Minimal denoising to preserve text details
            cv_image = cv2.fastNlMeansDenoising(cv_image, None, h=10, searchWindowSize=21)
            
            # 3. Sharpen to enhance edges
            kernel = np.array([[-0.5,-0.5,-0.5], [-0.5,5,-0.5], [-0.5,-0.5,-0.5]])
            cv_image = cv2.filter2D(cv_image, -1, kernel)
            
            st.image(cv_image, caption="Preprocessed Image", width=300)  # Debug: show preprocessed image

            # Preferred method: ORB + SIFT page matching
            match_result = self.page_matcher.match_page(cv_image)
            if match_result:
                edition, page, similarity, method = match_result
                page_ayahs = self.db.get_page_ayahs(page, edition)
                os.unlink(tmp_path)
                return {
                    "image": img_pil,
                    "method": method,
                    "edition": edition,
                    "page": page,
                    "similarity": similarity,
                    "ayahs": page_ayahs
                }
            # Fallback: OCR and hash-based verification
            ocr_text = self.ocr_engine.recognize(img_pil)
            norm_text = self.normalizer.normalize(ocr_text)
            hash_val = self.verifier.compute_hash(norm_text)
            result = self.db.get_ayah_by_hash(hash_val)
            os.unlink(tmp_path)
            return {
                "image": img_pil,
                "method": "OCR",
                "ocr_text": ocr_text,
                "norm_text": norm_text,
                "hash_val": hash_val,
                "result": result
            }
        except Exception as e:
            os.unlink(tmp_path)
            raise e

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
        verificator = QuranVerificator()
        result = verificator.process_file(uploaded_file)

        # Image display
        st.image(result["image"], caption="🖼 Uploaded Image", width="stretch")
        st.markdown("---")

        if result["method"] in ("ORB", "SIFT"):
            st.subheader(f"🔍 Page Match ({result['method']})")
            st.success(f"Edition: **{result['edition']}**, Page: **{result['page']}** (Similarity: {result['similarity']:.2f})")
            st.subheader("📖 Verses on this Page")
            if result["ayahs"]:
                for ayah in result["ayahs"]:
                    sura, aya, text = ayah
                    st.markdown(f"**Surah {sura}, Ayah {aya}**: {text}")
            else:
                st.warning("No ayahs found for this page in the database.")
        else:
            st.subheader("📝 OCR Fallback")
            st.subheader("📜 OCR Output")
            st.code(result["ocr_text"] or "[No text detected]")
            st.subheader("Normalized Text")
            st.code(result["norm_text"] or "[Normalization failed]")
            st.subheader("SHA-256 Hash")
            st.code(result["hash_val"])
            st.subheader("✅ Verification Result")
            if result["result"]:
                sura, aya = result["result"]
                st.success(f"✅ **Verified (Uthmani)** – Surah {sura}, Ayah {aya}")
            else:
                st.warning("⚠️ **No exact match found.** This might be due to OCR noise, different edition, or a real textual difference.")

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

st.markdown("---")
if st.button("🔁 Try Another File"):
    st.rerun()