#### TO BE EDITED


# Quran Verificator

![Python](https://img.shields.io/badge/python-3.10-green)

A comprehensive system for verifying Quran text integrity in digital and printed materials. This tool helps government bodies, publishers, and researchers ensure that mass-produced Quran mushafs stay true to canonical texts.

## Overview

Quran Verificator is a locally-running application that verifies Quran text against canonical references using computer vision, OCR, and text analysis techniques. It processes images and PDFs containing Quran text, extracts the content, and compares it against verified reference texts from Tanzil.

![System Screenshot](https://via.placeholder.com/800x450.png?text=Quran+Verificator+Screenshot)

## Features

- **Multiple Verification Methods**:
  - Edition-locked verification (specific page/edition matching)
  - Open-edition verification (any text against canonical sources)
  - Hash-based exact matching
  - Fuzzy matching with similarity scoring

- **Advanced Image Processing**:
  - Automatic deskew and rotation correction
  - Noise reduction and binarization
  - Page detection and feature extraction

- **OCR Optimization**:
  - Arabic/Uthmani script recognition
  - Support for both Kraken OCR
  - Extensible OCR engine architecture

- **Detailed Difference Analysis**:
  - Visual HTML diff highlighting
  - Character-level difference detection
  - Optional LLM-based explanation (using local models)

- **Rich User Interface**:
  - Interactive Streamlit web interface
  - PDF document navigation
  - Real-time verification feedback

- **Comprehensive Reporting**:
  - Exportable PDF verification reports
  - Verification badges and confidence scores
  - Original/processed image inclusion

## System Requirements

- Docker Desktop (for containerized deployment)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- Internet connection (for initial setup only)

## Installation

### Using Docker (Recommended)

1. Clone the repository:

2. Build the Docker image:
   ```bash
   docker build -t quran-verificator .
   ```

3. Run the container:
   ```bash
   docker run -p 8501:8501 -v $(pwd)/data:/app/data quran-verificator
   ```

4. Access the application at http://localhost:8501

### Importing Tanzil Data
1. Place your Tanzil SQL dump in the `data` directory:
   ```bash
   cp /path/to/Tanzil_quran-uthmani.sql data/
   ```

2. Create and run the import script:
   ```bash
   # Create the import_tanzil.py script as described in documentation
   docker exec -it $(docker ps -q --filter ancestor=quran-verificator) python import_tanzil.py
   ```

## Usage
1. Open the application in your browser at http://localhost:8501

2. Select verification mode:
   - **Automatic**: Attempts page matching first, falls back to OCR
   - **Edition-Locked**: Verifies against a specific edition and page
   - **Manual OCR**: Performs OCR on user-selected regions

3. Upload a Quran image or PDF file

4. Click "Process Image" to start verification

5. Review the results:
   - ✅ Green badge: Exact match
   - ⚠️ Amber badge: Near match (with similarity percentage)
   - ❌ Red badge: No match

6. Examine the differences highlighted in the diff view

7. Generate and download a PDF report if needed

## Project Structure
```
quran_verificator/
├── app.py                      # Main Streamlit application
├── Dockerfile                  # Docker configuration
├── requirements.txt           # Dependencies
├── data/
│   ├── quran_ref.db           # SQLite database
│   └── assets/
│       ├── images/            # Reference page images
│       └── orb/               # Pre-computed ORB descriptors
└── modules/
    ├── __init__.py
    ├── preprocessing.py       # Image preprocessing
    ├── matching.py            # Page matching
    ├── ocr_engine.py          # OCR integration
    ├── normalizer.py          # Text normalization
    ├── verifier.py            # Verification logic
    ├── diff_engine.py         # Diff generation
    ├── llm_explainer.py       # LLM explanation
    ├── pdf_generator.py       # Report generation
    └── database.py            # Database operations
```

## System Pipeline
1. **Upload**
   - User uploads an image or PDF of a Quran page
   - Backend preprocesses the image (deskew, denoise, crop, binarize)

2. **Process & Match**
   - **Page-Match**: Extract ORB features → match against known editions
   - **OCR**: Run OCR on the image → extract Arabic text

3. **Verify**
   - **Edition-Locked**: Compare to known page/edition
   - **Open-Edition**: Hash lookup or fuzzy match

4. **Explain & Display**
   - Show verification badge (✅/⚠️/❌)
   - Generate HTML diff highlighting differences
   - Optionally explain differences with LLM

5. **Review & Report**
   - Generate PDF report with verification results
   - Export for regulatory review

## Acknowledgments
- [Tanzil.net](https://tanzil.net) for providing canonical Quran text
- [Kraken OCR](https://kraken.re) for OCR technology
- [Streamlit](https://streamlit.io) for the web interface framework