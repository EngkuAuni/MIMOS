# Use Python 3.9 with CUDA support for better PyTorch compatibility
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgcc-s1 \
    libfontconfig1 \
    libice6 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-docker.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Install PyTorch with CPU support (more stable than CUDA for this use case)
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy the application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p database models QariOCR_Finetuning/models QariOCR_Finetuning/training_data QariOCR_Finetuning/scripts uploads reports && \
    chmod -R 777 database models QariOCR_Finetuning uploads reports

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD ["streamlit", "run", "app_enhanced.py", "--server.port=8501", "--server.address=0.0.0.0"]