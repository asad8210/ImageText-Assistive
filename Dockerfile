# Use official slim Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Tesseract and image processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-hin \
        libgl1 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port for Flask
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py", "--threaded"]
