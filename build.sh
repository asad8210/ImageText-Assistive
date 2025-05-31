#!/usr/bin/env bash

set -e  # Exit on any error
set -o pipefail  # Catch errors in piped commands

# Update package list and install required dependencies
apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Confirm successful installation
echo "✅ Installed Tesseract version:"
tesseract --version

echo "✅ All required dependencies installed successfully."
