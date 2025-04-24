import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("story2map.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Ensure data directory exists
data_dir = os.path.join(os.getcwd(), "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    logger.info(f"Created data directory: {data_dir}")

# Import modules
from .text_extractor import TextExtractor
from .location_extractor import LocationExtractor
from .map_generator import MapGenerator

__all__ = ["TextExtractor", "LocationExtractor", "MapGenerator"] 