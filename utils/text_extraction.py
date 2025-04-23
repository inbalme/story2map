"""
Utility functions for extracting text from various sources:
- Clipboard text
- Clipboard images (using OCR)
- URLs (web scraping)
"""

import io
import requests
import pyperclip
from PIL import Image, ImageGrab
import pytesseract
from bs4 import BeautifulSoup
import streamlit as st

def get_clipboard_text():
    """
    Get text from clipboard
    """
    try:
        return pyperclip.paste()
    except Exception as e:
        st.error(f"Error getting text from clipboard: {e}")
        return ""

def get_text_from_image():
    """
    Extract text from clipboard image using OCR
    """
    try:
        # Get image from clipboard
        image = ImageGrab.grabclipboard()
        
        if image is None:
            st.error("No image found in clipboard")
            return ""
        
        # Convert PIL Image to bytes
        if isinstance(image, Image.Image):
            # Run OCR on the image
            text = pytesseract.image_to_string(image)
            return text
        else:
            st.error("Clipboard content is not an image")
            return ""
    except Exception as e:
        st.error(f"Error extracting text from image: {e}")
        return ""

def get_text_from_url(url):
    """
    Scrape text content from a URL
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Send a GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        st.error(f"Error getting text from URL: {e}")
        return "" 