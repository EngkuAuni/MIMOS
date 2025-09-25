import streamlit as st
import sqlite3
import tempfile
import unicodedata
import re
import hashlib
from PIL import Image
import cv2
import numpy as np
from kraken import binarization, pageseg, rpred
from pdf2image import convert_from_path
from pathlib import Path

# --- Constants ---
DB_PATH = "quran_ref.db"
KR_MODEL = "default"  # Use "default" or replace with your custom model path

# --- Normalization Rules ---
WAQF_SIGNS = ''.join([
    '\u06d6', '\u06d7', '\u06d8', '\u06d9', '\u06da', '\u06db', '\u06dc',
    '\u06dd', '\u06de', '\u06df', '\u06e0', '\u06e1', '\u06e2', '\u06e3',
    '\u06e4', '\u06e5', '\u06e6', '\u06e7', '\u06e8', '\u06e9', '\u06ea',
    '\u06eb', '\u06ec', '\u06ed'
])
ZERO_WIDTH = '\u200c\u200d\ufeff'
TATWEEL = '\u0640'

WAQF_RE = re.compile(f"[{re.escape(WAQF_SIGNS)}]")
ZW_RE = re.compile(f"[{re.escape(ZERO_WIDTH)}]")
TATWEEL_RE = re.compile(f"[{re.escape(TATWEEL)}]")

def normalize_uthmani(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = ZW_RE.sub("", text)
    text = TATWEEL_RE.sub("", text)
    text = WAQF_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def hash_norm(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# --- OCR with Kraken (FIXED) ---
def run_ocr_kraken(img_pil: Image.Image) -> str:
    try:
        bin_img = binarization.nlbin(img_pil)
        seg = pageseg.segment(bin_img)
        
        # Get the bounds from segmentation result
        bounds = seg['boxes']
        
        # Pass bounds to rpred properly
        preds = rpred.rpred(KR_MODEL, bin_img, bounds)
        
        return ''.join([r.prediction for r in preds])
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"[OCR ERROR] {str(e)}\n{trace}"

# --- DB Lookup ---
def lookup_hash(hash_val: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT sura, aya FROM ayah WHERE sha256_norm = ?", (hash_val,)
        ).fetchone()
        conn.close()
        return row
    except Exception as e:
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Quran Verification Engine", layout="wide")
st.title("📜 Quran Verification Engine (Uthmani Edition)")

st.markdown("""
Upload a scanned image or PDF page of the Quran, and this engine will verify its integrity
against a canonical Uthmani database.
""")

uploaded_file = st.file_uploader("📤 Upload Image or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Handle PDF → image conversion
    if uploaded_file.type == "application/pdf":
        st.info("📄 PDF detected. Converting first page to image...")
        pages = convert_from_path(tmp_path, dpi=350)
        img_pil = pages[0]
    else:
        img_pil = Image.open(tmp_path).convert("RGB")

    st.image(img_pil, caption="🖼 Uploaded Image", use_container_width=True)

    with st.spinner("🔍 Running OCR and verifying..."):
        ocr_text = run_ocr_kraken(img_pil)
        norm_text = normalize_uthmani(ocr_text)
        hash_val = hash_norm(norm_text)
        result = lookup_hash(hash_val)

    st.markdown("---")
    st.subheader("📜 OCR Output")
    st.code(ocr_text or "[No text detected]")

    st.subheader("🧼 Normalized Text")
    st.code(norm_text or "[Normalization failed]")

    st.subheader("🔐 SHA-256 Hash")
    st.code(hash_val)

    st.subheader("✅ Verification Result")
    if result:
        sura, aya = result
        st.success(f"✅ **Verified (Uthmani)** – Surah {sura}, Ayah {aya}")
    else:
        st.warning("⚠️ **No exact match found.** This might be due to OCR noise, different edition, or a real textual difference.")

    st.markdown("---")
    if st.button("🔁 Try Another File"):
        # FIXED: Use st.rerun() instead of st.experimental_rerun()
        st.rerun()