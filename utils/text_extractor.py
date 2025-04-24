import logging
import io
import re
import requests
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import pyperclip
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextExtractor:
    """Class to extract text from different sources."""
    
    @staticmethod
    def from_clipboard() -> str:
        """
        Extract text from clipboard.
        
        Returns:
            Extracted text as string
        """
        try:
            text = pyperclip.paste()
            if not text:
                logger.warning("Clipboard is empty")
                return ""
            logger.info(f"Extracted {len(text)} characters from clipboard")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from clipboard: {e}")
            return ""
    
    @staticmethod
    def from_image(image) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image: PIL Image or bytes or file-like object
            
        Returns:
            Extracted text as string
        """
        try:
            # Convert to PIL Image if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            elif hasattr(image, 'read'):  # file-like object
                image = Image.open(image)
                
            # Perform OCR
            text = pytesseract.image_to_string(image)
            if not text:
                logger.warning("No text found in the image")
                return ""
            logger.info(f"Extracted {len(text)} characters from image")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    @staticmethod
    def from_url(url: str) -> str:
        """
        Extract text from a webpage.
        
        Args:
            url: URL of the webpage
            
        Returns:
            Extracted text as string
        """
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
                
            # Download the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.extract()
            
            # Get text and clean it
            text = soup.get_text(separator=' ')
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            if not text:
                logger.warning("No text found on the webpage")
                return ""
                
            logger.info(f"Extracted {len(text)} characters from URL: {url}")
            return text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting URL {url}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from URL {url}: {e}")
            return "" 