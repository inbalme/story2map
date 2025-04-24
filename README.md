# Story2Map

A Streamlit application that extracts place names from text and maps them on Google Maps. This tool is perfect for travel planning, research, and visualizing location-based information from textual content.

## Features

- **Multiple Text Input Methods:**
  - Copy/paste from clipboard
  - Extract text from clipboard screenshots using OCR
  - Extract text from URLs (web scraping)

- **Location Extraction:**
  - Uses spaCy NER for basic place extraction
  - Uses Google Gemini AI for enhanced place extraction with sentiment analysis

- **Mapping Features:**
  - Display extracted locations on maps with two visualization options:
    - Basic map view with Folium
    - Full-featured Google Maps with all standard Google Maps annotations
  - Choose Google Maps type (roadmap, satellite, hybrid, terrain)
  - Save maps for future reference
  - Add new locations to existing maps
  - Calculate optimal routes between selected locations (walking/driving/public transit/bicycling)
  - Add notes to locations with sentiment indicators (positive/negative/neutral)
  - Download maps as HTML files for offline viewing

## Setup

### Prerequisites

- Python 3.8+
- Google Maps API key
- Google Gemini API key
- Tesseract OCR (for image text extraction)

### Installation

#### Option 1: Using pip (standard)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/story2map.git
   cd story2map
   ```

2. Run the setup script to install dependencies and set up the environment:
   ```
   python setup.py
   ```

3. Set up API keys:
   - Create a `.env` file in the root directory based on the `.env.template` file
   - Add your Google Maps API key and Google Gemini API key

   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key
   ```

4. Install Tesseract OCR:
   - On macOS: `brew install tesseract`
   - On Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - On Linux: `sudo apt-get install tesseract-ocr`

#### Option 2: Using Conda (recommended)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/story2map.git
   cd story2map
   ```

2. Run the conda setup script to create and configure the environment:
   - On macOS/Linux:
     ```
     ./setup_conda.sh
     ```
   - On Windows:
     ```
     setup_conda.bat
     ```

3. Activate the conda environment:
   ```
   conda activate story2map
   ```

4. Set up API keys:
   - Create a `.env` file in the root directory based on the `.env.template` file
   - Add your Google Maps API key and Google Gemini API key

5. Install Tesseract OCR as instructed by the setup script

## Running the Application

Start the Streamlit app:

```
streamlit run app.py
```

This will open the application in your default web browser.

## Usage Guide

### 1. Input Text

The application offers three ways to input text:

- **Clipboard**: Copy text from anywhere and paste it directly or use the "Get Text from Clipboard" button
- **Screenshot**: Copy an image containing text to your clipboard and let the app extract text using OCR
- **URL**: Enter a webpage URL and the app will scrape and extract the text content

### 2. Extract Places

After inputting text:

1. Choose extraction method(s):
   - spaCy for basic extraction
   - Google Gemini for enhanced extraction with sentiment
2. Click "Extract Places" button
3. View the list of extracted places

### 3. Map View

- Choose your preferred map type:
  - **Folium (Basic)**: A simpler, lightweight map
  - **Google Maps (Full)**: Full Google Maps experience with all standard annotations and features
- When using Google Maps, you can select the map type: roadmap, satellite, hybrid, or terrain
- All extracted places will be displayed on the selected map
- Markers are color-coded by sentiment (green = positive, red = negative, blue = neutral)
- Click on markers to view place details
- Add notes and update sentiment for any place
- Save maps for future reference
- Load previously saved maps

### 4. Route Planning

1. Select a starting point and destination from extracted places
2. Optionally add waypoints
3. Choose a travel mode (driving, walking, transit, bicycling)
4. Click "Calculate Route" to see:
   - Route displayed on the map
   - Distance and duration information
   - Step-by-step directions

## Troubleshooting

- **API Key Issues**: Ensure your API keys are correctly entered in the `.env` file
- **OCR Problems**: Make sure Tesseract OCR is properly installed on your system
- **Geocoding Failures**: Some place names may be ambiguous or not found by Google Maps

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web app framework
- [spaCy](https://spacy.io/) for NLP and entity recognition
- [Google Maps Platform](https://developers.google.com/maps) for geocoding and mapping
- [Google Gemini API](https://ai.google.dev/gemini-api) for enhanced place extraction
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for image text extraction 