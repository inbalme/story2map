"""
Utility functions for extracting place names from text.
Uses spaCy NER for basic extraction and Google Gemini API for enhanced extraction.
"""

import os
import spacy
import streamlit as st
import json
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load spaCy model
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_lg")
    except:
        st.warning("Downloading spaCy model. This may take a while...")
        spacy.cli.download("en_core_web_lg")
        return spacy.load("en_core_web_lg")

# Configure Google Gemini API
def configure_gemini():
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        st.error("Google Gemini API key not found in environment variables.")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def extract_places_with_spacy(text: str) -> List[Dict[str, Any]]:
    """
    Extract place names from text using spaCy's named entity recognition.
    
    Args:
        text: The input text to analyze
        
    Returns:
        A list of dictionaries containing place names and their positions in the text
    """
    if not text:
        return []
    
    nlp = load_spacy_model()
    doc = nlp(text)
    
    places = []
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            places.append({
                "name": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "type": ent.label_
            })
    
    return places

def extract_places_with_gemini(text: str) -> List[Dict[str, Any]]:
    """
    Extract place names from text using Google Gemini API.
    
    Args:
        text: The input text to analyze
        
    Returns:
        A list of dictionaries containing place names and their types
    """
    if not text:
        return []
    
    model = configure_gemini()
    if not model:
        return []
    
    # Prepare prompt for Gemini
    prompt = f"""
    Extract all geographical locations from the following text. Return ONLY a JSON array of objects.
    Each object should have:
    - "name": the full place name as mentioned in the text
    - "type": the type of location (country, city, landmark, etc.)
    - "sentiment": (if present) positive, negative, or neutral based on how the location is described
    
    Text to analyze:
    {text}
    
    Return valid JSON only, no other text.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON if it's embedded in markdown code block
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        places = json.loads(response_text)
        return places
    except Exception as e:
        st.error(f"Error extracting places with Gemini: {e}")
        return []

def combine_place_extractions(spacy_places: List[Dict], gemini_places: List[Dict]) -> List[Dict]:
    """
    Combine and deduplicate places extracted from both methods
    """
    combined_places = {}
    
    # Add spaCy places
    for place in spacy_places:
        name = place["name"].strip()
        if name.lower() not in combined_places:
            combined_places[name.lower()] = {
                "name": name,
                "type": place.get("type", "Unknown"),
                "sentiment": "neutral",
                "mentions": 1
            }
        else:
            combined_places[name.lower()]["mentions"] += 1
    
    # Add Gemini places
    for place in gemini_places:
        name = place["name"].strip()
        if name.lower() not in combined_places:
            combined_places[name.lower()] = {
                "name": name,
                "type": place.get("type", "Unknown"),
                "sentiment": place.get("sentiment", "neutral"),
                "mentions": 1
            }
        else:
            # Update with Gemini's sentiment if available
            if "sentiment" in place and place["sentiment"] != "neutral":
                combined_places[name.lower()]["sentiment"] = place["sentiment"]
            combined_places[name.lower()]["mentions"] += 1
    
    return list(combined_places.values()) 