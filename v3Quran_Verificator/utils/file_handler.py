# PDF/image loading, conversion

from pdf2image import convert_from_bytes
from PIL import Image
import io

def load_file(file):
    if file.type.startswith("image"):
        return Image.open(file)
    elif file.type == "application/pdf":
        return convert_pdf_to_images(file)
    else:
        raise ValueError("Unsupported file type")

def convert_pdf_to_images(pdf_file):
    images = convert_from_bytes(pdf_file.read())
    return images