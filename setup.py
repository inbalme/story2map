"""
Setup script for Story2Map application.
This script helps users set up the environment by:
1. Installing required Python packages
2. Creating necessary directories
3. Setting up environment variables
4. Downloading spaCy model
"""

import os
import sys
import subprocess
import shutil
import platform

def main():
    print("Setting up Story2Map application...")
    
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created data directory.")
    
    # Create .env file from template if it doesn't exist
    if not os.path.exists(".env") and os.path.exists(".env.template"):
        shutil.copy(".env.template", ".env")
        print("Created .env file from template. Please edit it to add your API keys.")
    
    # Install Python packages
    print("Installing required Python packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Download spaCy model
    print("Downloading spaCy language model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])
    
    # Check for Tesseract OCR installation
    print("Checking for Tesseract OCR installation...")
    
    if platform.system() == "Windows":
        print("On Windows: Please download and install Tesseract OCR from:")
        print("https://github.com/UB-Mannheim/tesseract/wiki")
    elif platform.system() == "Darwin":  # macOS
        print("On macOS: Install Tesseract OCR using Homebrew:")
        print("brew install tesseract")
    else:  # Linux
        print("On Linux: Install Tesseract OCR using your package manager:")
        print("sudo apt-get install tesseract-ocr")
    
    print("\nSetup completed! To run the application:")
    print("1. Edit the .env file to add your API keys")
    print("2. Install Tesseract OCR if not already installed")
    print("3. Run the application with: streamlit run app.py")

if __name__ == "__main__":
    main() 