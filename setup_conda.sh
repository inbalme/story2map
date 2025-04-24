#!/bin/bash

echo "Setting up conda environment for Story2Map..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "conda could not be found. Please install Anaconda or Miniconda first."
    exit 1
fi

# Create conda environment from environment.yml
echo "Creating conda environment from environment.yml..."
conda env create -f environment.yml

# Activate the environment
echo "To activate the environment, run:"
echo "conda activate story2map"

# Install tesseract OCR based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "You're on macOS. To install Tesseract OCR, run:"
    echo "brew install tesseract"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "You're on Linux. To install Tesseract OCR, run:"
    echo "sudo apt-get install tesseract-ocr"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "You're on Windows. Please download and install Tesseract OCR from:"
    echo "https://github.com/UB-Mannheim/tesseract/wiki"
fi

echo ""
echo "After activating the environment and installing Tesseract OCR,"
echo "run the application with: streamlit run app.py" 