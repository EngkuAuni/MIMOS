# PDF/image loading, conversion

from pdf2image import convert_from_bytes
from PIL import Image, ImageOps
import io
import hashlib
from typing import List, Tuple, Optional, Literal

# Optional fallback backend
try:
    import fitz  # PyMuPDF
    _HAVE_PYMUPDF = True
except Exception:
    _HAVE_PYMUPDF = False

# Simple in-process cache keyed by (sha256, dpi, pages)
_page_cache = {}

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_file(
    file,
    dpi: int = 300,
    max_pages: int = 1,
    first_n_pages: Optional[int] = 1,
    image_max_megapixels: int = 12,
) -> Tuple[List[Image.Image], Literal["pdf", "image"]]:
    """
    Load file and convert to PIL Images with safety checks.
    
    Args:
        file: UploadedFile-like object
        dpi: PDF rendering DPI
        max_pages: hard cap for rendered pages (PDF)
        first_n_pages: if set, only render first N pages
        image_max_megapixels: cap decoded image resolution (in MP)
    Returns:
        (list of PIL Images, source_type)
    """
    # Streamlit UploadedFile exposes .type and .read(), but reading consumes the buffer.
    # We read into memory once for consistent handling and caching.
    file_bytes = file.read()

    # Basic magic sniff
    is_pdf = file_bytes[:5] == b"%PDF-"
    if file.type == "application/pdf" or is_pdf:
        images = convert_pdf_bytes_to_images(
            file_bytes, dpi=dpi, max_pages=1, first_n_pages=1
        )
        return images, "pdf"

    if file.type.startswith("image"):
        img = Image.open(io.BytesIO(file_bytes))
        # Normalize EXIF orientation and color space
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Safety: cap resolution
        mp = (img.width * img.height) / 1_000_000.0
        if mp > image_max_megapixels:
            scale = (image_max_megapixels / mp) ** 0.5
            new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            img = img.resize(new_size)
        return [img], "image"

    raise ValueError(f"Unsupported file type: {file.type}")

def convert_pdf_bytes_to_images(
    pdf_bytes: bytes,
    dpi: int = 300,
    max_pages: int = 1,
    first_n_pages: Optional[int] = 1,
) -> List[Image.Image]:
    """
    Convert PDF bytes to list of PIL Images with dual backends and caching.
    """
    # Safety: rough size limit (e.g., 100 MB)
    if len(pdf_bytes) > 100 * 1024 * 1024:
        raise ValueError("PDF too large. Please upload a smaller document or reduce DPI.")

    h = _sha256(pdf_bytes)
    cache_key = (h, dpi, 1)
    if cache_key in _page_cache:
        return _page_cache[cache_key]

    # Primary backend: pdf2image/poppler
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
    except Exception:
        # Fallback: PyMuPDF
        if not _HAVE_PYMUPDF:
            raise
        images = _convert_pdf_with_pymupdf(pdf_bytes, dpi=dpi)

    # Page limiting
    # Enforce single-page PDFs: always take only the first page
    images = images[:1]

    # Ensure RGB and sanitize
    rgb_images = []
    for img in images:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        rgb_images.append(img)

    _page_cache[cache_key] = rgb_images
    return rgb_images

def _convert_pdf_with_pymupdf(pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pages = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(img)
    return pages

def convert_pdf_to_images(pdf_file, dpi: int = 300) -> List[Image.Image]:
    """
    Backwards-compatible wrapper for older call sites.
    """
    pdf_bytes = pdf_file.read()
    return convert_pdf_bytes_to_images(pdf_bytes, dpi=dpi)