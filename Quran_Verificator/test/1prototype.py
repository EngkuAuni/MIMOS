# --------------------------------------------------------------
# Quran Text Verification Engine – Streamlit MVP
# --------------------------------------------------------------

import os, json, hashlib, re, tempfile, shutil, itertools
from pathlib import Path
from typing import List, Tuple, Dict, Any

import streamlit as st
import numpy as np
import cv2
from pdf2image import convert_from_path
from PIL import Image
import easyocr
from rapidfuzz import process, fuzz
from difflib import HtmlDiff
from modules.normalizer import ArabicNormalizer
normalizer = ArabicNormalizer()

# ------------------------------------------------------------------
# 1️⃣ Load / initialise the verified Qur’an database
# ------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
DB_JSON = DATA_DIR / "tanzil_quran_uthmani.json"
CACHE_DB = DATA_DIR / "quran_cache.json"  # optional serialized dict

# --------------------------------------------------------------
# Helper – normalise Arabic text (remove tatweel, unify hamza, strip diacritics)
# --------------------------------------------------------------
ARABIC_NORMALIZATION_TABLE = str.maketrans({
    "آ": "ا", "إ": "ا", "أ": "ا", "ؤ": "و", "ئ": "ي",
    "ة": "ه", "ﻻ": "لا", "ﻹ": "لي", "ﻷ": "لا", "ﻵ": "لا",  # ligatures
    "ـ": "",       # tatweel
})
DIACRITICS_REGEX = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]")  # Arabic diacritics range

def normalize_arabic(text: str, drop_diacritics: bool = False) -> str:
    return normalizer.normalize(text, drop_diacritics=drop_diacritics)

def sha256_checksum(text: str) -> str:
    """SHA‑256 hash of the UTF‑8 encoded text."""
    return hashlib.sha256(text.encode("utf‑8")).hexdigest()

# --------------------------------------------------------------
# Load the verified Qur’an verses into an in‑memory dict:
#   key   -> (surah, ayah)
#   value -> {"text": <Uthmani>, "checksum": <sha256>, "page": <int>}
# --------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_verified_quran() -> Dict[Tuple[int, int], Dict[str, Any]]:
    if not DB_JSON.is_file():
        st.error(f"Verified Qur’an JSON not found at {DB_JSON}. Please download from Tanzil.")
        return {}

    with open(DB_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Build dict
    db = {}
    for entry in raw:
        surah = int(entry["surah"])
        ayah = int(entry["ayah"])
        text = entry["text"]
        checksum = sha256_checksum(text)
        page = int(entry.get("page", 0))  # some sources provide page numbers
        db[(surah, ayah)] = {
            "text": text,
            "checksum": checksum,
            "page": page,
        }

    # Cache a lightweight JSON for fast reload (optional)
    with open(CACHE_DB, "w", encoding="utf-8") as cf:
        json.dump(db, cf, ensure_ascii=False)
    return db

VERIFIED_DB = load_verified_quran()

# ------------------------------------------------------------------
# 2️⃣ OCR and Pre‑processing utilities
# ------------------------------------------------------------------
import easyocr
from io import BytesIO
import base64
from difflib import HtmlDiff
from weasyprint import HTML  # optional – if unavailable, ReportLab will be used

# ──────────────────────────────────────────────────────────────────
# Helper: convert between Pillow and OpenCV formats
# ──────────────────────────────────────────────────────────────────
def pil_to_cv2(img: Image.Image) -> np.ndarray:
    """Pillow → BGR OpenCV array."""
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def cv2_to_pil(arr: np.ndarray) -> Image.Image:
    """BGR OpenCV array → Pillow."""
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

# ──────────────────────────────────────────────────────────────────
# Denoising, deskewing, contrast‑enhancement
# ──────────────────────────────────────────────────────────────────
def denoise_image(cv_img: np.ndarray) -> np.ndarray:
    """Bilateral filter – preserves edges while removing noise."""
    return cv2.bilateralFilter(cv_img, d=9, sigmaColor=75, sigmaSpace=75)

def enhance_contrast(cv_img: np.ndarray) -> np.ndarray:
    """Histogram equalisation on the luminance channel."""
    if len(cv_img.shape) == 3:
        ycrcb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    else:  # grayscale
        return cv2.equalizeHist(cv_img)

def deskew_image(cv_img: np.ndarray) -> np.ndarray:
    """Detect the dominant text angle and rotate the image to upright."""
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    # Invert – text should be white on black for better moments
    gray = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) == 0:  # nothing detected → return original
        return cv_img
    angle = cv2.minAreaRect(coords)[-1]
    # The `minAreaRect` angle is in the range [-90, 0); we adjust it
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = cv_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(cv_img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """Full pipeline: denoise → enhance → deskew."""
    cv_img = pil_to_cv2(pil_img)
    cv_img = denoise_image(cv_img)
    cv_img = enhance_contrast(cv_img)
    cv_img = deskew_image(cv_img)
    return cv2_to_pil(cv_img)

# ──────────────────────────────────────────────────────────────────
# OCR – EasyOCR (fallback to Tesseract if needed)
# ──────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_ocr_reader() -> easyocr.Reader:
    """Create a single EasyOCR reader for Arabic (supports Latin fallback)."""
    return easyocr.Reader(["ar"], gpu=False)  # set gpu=True if a CUDA‑GPU is available

def ocr_image(pil_img: Image.Image) -> str:
    """Run OCR on a pre‑processed image and return a single Unicode string."""
    reader = get_ocr_reader()
    # EasyOCR expects a numpy array (RGB)
    np_img = np.array(pil_img.convert("RGB"))
    result = reader.readtext(np_img, detail=0, paragraph=True)
    # Join all lines, remove stray spaces, and normalise
    raw_text = " ".join(result)
    # Normalisation (see section 1)
    norm_text = normalize_arabic(raw_text, drop_diacritics=False)
    return norm_text

# ------------------------------------------------------------------
# 3️⃣ Matching & Diff Engine
# ------------------------------------------------------------------
def find_best_match(ocr_text: str, drop_diacritics: bool = False) -> Tuple[Tuple[int, int], float, str]:
    """
    Returns:
        (surah, ayah) – reference of the best matching verse
        score          – similarity score (0‑100)
        ref_text       – the verified verse text (raw, not normalised)
    """
    # Normalise both sides the same way for a fair comparison
    query = normalize_arabic(ocr_text, drop_diacritics=drop_diacritics)

    # Build a simple list of reference strings (already normalised)
    refs = []
    keys = []  # parallel list of (surah, ayah)
    for (s, a), meta in VERIFIED_DB.items():
        ref_norm = normalize_arabic(meta["text"], drop_diacritics=drop_diacritics)
        refs.append(ref_norm)
        keys.append((s, a))

    # Use RapidFuzz to get the top match
    best, score, idx = process.extractOne(query, refs, scorer=fuzz.ratio)
    best_key = keys[idx]
    return best_key, score, VERIFIED_DB[best_key]["text"]

def generate_html_diff(ocr_text: str, ref_text: str) -> str:
    """
    Produce an HTML table highlighting insertions (green) and deletions (red)
    while preserving Arabic RTL direction.
    """
    # Ensure the diff works on the original Unicode strings (with diacritics)
    diff = HtmlDiff(wrapcolumn=120, linejunk=lambda x: False, charjunk=lambda x: False)
    html = diff.make_table(
        ref_text.split(),
        ocr_text.split(),
        fromdesc="Verified (Reference)",
        todesc="Scanned (OCR)",
        context=True,
        numlines=3,
    )
    # Inject small CSS tweaks for RTL and colors
    style = """
    <style>
        table.diff {font-family: "Amiri", serif; direction: rtl; text-align: right;}
        .diff_header {background-color: #f0f0f0;}
        .diff_next {background-color: #e0e0e0;}
        .diff_add {background-color:#c8e6c9;}
        .diff_sub {background-color:#ffccbc;}
    </style>
    """
    return style + html

def compute_checksum(text: str) -> str:
    """Convenient wrapper around sha256_checksum for the UI."""
    return sha256_checksum(text)

# ------------------------------------------------------------------
# 4️⃣ Report Generation
# ------------------------------------------------------------------
def build_report_html(
    filename: str,
    page_num: int,
    ocr_text: str,
    ref_text: str,
    diff_html: str,
    match_score: float,
    ref_meta: Dict[str, Any],
) -> str:
    """
    Returns a full HTML document that can be displayed in Streamlit
    and optionally turned into a PDF.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Qur’an Verification – {filename} – Page {page_num}</title>
        <style>
            body {{font-family: "Amiri", serif; direction: rtl; margin: 2em;}}
            h1 {{text-align:center;}}
            .meta {{margin: 1em 0;}}
            .diff-container {{margin-top:1.5em;}}
        </style>
    </head>
    <body>
        <h1>Qur’an Verification Report</h1>
        <div class="meta">
            <strong>File:</strong> {filename}<br>
            <strong>Page:</strong> {page_num}<br>
            <strong>Matched Surah/Ayah:</strong> {ref_meta["surah"]}:{ref_meta["ayah"]}<br>
            <strong>Reference Page (Mushaf):</strong> {ref_meta.get("page", "N/A")}<br>
            <strong>Similarity Score:</strong> {match_score:.1f}%<br>
            <strong>Checksum (OCR text):</strong> {compute_checksum(ocr_text)}<br>
            <strong>Checksum (Reference):</strong> {ref_meta["checksum"]}
        </div>
        <h2>Reference Verse</h2>
        <p>{ref_text}</p>
        <h2>Extracted OCR Text</h2>
        <p>{ocr_text}</p>
        <h2>Differences</h2>
        <div class="diff-container">
            {diff_html}
        </div>
    </body>
    </html>
    """
    return html

def html_to_pdf(html: str, output_path: str):
    """Render HTML to PDF using WeasyPrint; fall back to ReportLab if missing."""
    try:
        HTML(string=html).write_pdf(output_path)
    except Exception as e:
        # Very small fallback using ReportLab (no CSS support)
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.lib.pagesizes import A4

        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30)
        styles = getSampleStyleSheet()
        arabic_style = ParagraphStyle(
            name="Arabic",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
            fontName="Amiri",  # system must have Amiri or fallback to Helvetica
            leading=16,
        )
        story = []
        for line in html.splitlines():
            if line.strip().startswith("<p>") and line.strip().endswith("</p>"):
                txt = re.sub(r"</?p>", "", line).strip()
                story.append(Paragraph(txt, arabic_style))
                story.append(Spacer(1, 6))
        doc.build(story)

# ------------------------------------------------------------------
# 5️⃣ Streamlit UI
# ------------------------------------------------------------------
st.set_page_config(page_title="Qur’an Text Verification", layout="wide")
st.title("🕮 Qur’an Text Verification Engine")
st.markdown(
    """
    Upload a scanned **image** (JPEG/PNG) or a **PDF** containing pages of a printed Qur’an.  
    The engine will:
    1️⃣ Run OCR tuned for Arabic.  
    2️⃣ Match each extracted snippet to the correct **Surah‑Ayah** from the verified Tanzil corpus.  
    3️⃣ Highlight any letter‑, word‑ or diacritic‑level differences.  
    4️⃣ Produce a downloadable PDF
    """
)