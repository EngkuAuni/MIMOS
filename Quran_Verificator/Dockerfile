# Python slim base image compatible with ARM (M1/Apple Silicon) and x86
FROM --platform=linux/amd64 python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Install system dependencies (including JP2 support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    tesseract-ocr \
    git \
    curl \
    libopenjp2-7 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first (for better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p data/assets/images data/assets/orb models/ocr

# Copy project files into container
COPY . .

# Download default OCR model if needed (you may need to adjust URL)
RUN if [ ! -f models/ocr/default.mlmodel ]; then \
    curl -L https://github.com/mittagessen/kraken/raw/master/kraken/lib/models/default.mlmodel -o models/ocr/default.mlmodel; \
    fi

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]