import re
import os
import json
import string
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Try to import TextBlob for sentiment analysis
try:
    from textblob import TextBlob
    TextBlob("Test").sentiment  # Test if sentiment analysis works
    textblob_available = True
except Exception:
    textblob_available = False

# Word lists path
WORD_LISTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'word_lists')

def load_word_list(filename, default_list):
    """Load a word list from a JSON file with fallback to defaults"""
    try:
        file_path = os.path.join(WORD_LISTS_PATH, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
    except Exception:
        pass
    return set(default_list)

# Define default lists for fallback
DEFAULT_POSITIVE = ["good", "great", "excellent", "amazing", "quality", "best"]
DEFAULT_NEGATIVE = ["bad", "poor", "terrible", "worst", "problem", "difficult"]
DEFAULT_VALUES = ["quality", "innovation", "service", "integrity", "excellence"]
DEFAULT_BRAND_ATTRS = ["reliable", "innovative", "trusted", "professional", "expert"]
DEFAULT_KEYWORDS = ["professional", "service", "quality", "solution", "experience"]

# Load word lists with fallback to defaults
POSITIVE_WORDS = load_word_list('positive_words.json', DEFAULT_POSITIVE)
NEGATIVE_WORDS = load_word_list('negative_words.json', DEFAULT_NEGATIVE)
VALUE_INDICATORS = load_word_list('value_indicators.json', DEFAULT_VALUES)
BRAND_ATTRIBUTES = load_word_list('brand_attributes.json', DEFAULT_BRAND_ATTRS)

# Default analysis results for fallback
DEFAULT_ANALYSIS = {
    "keywords": DEFAULT_KEYWORDS,
    "tone_analysis": {
        "professional": 0.7,
        "friendly": 0.4,
        "informative": 0.6,
        "enthusiastic": 0.3,
        "formal": 0.5,
    },
    "key_values": ["Quality", "Innovation", "Customer Focus", "Excellence", "Integrity"],
    "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
}

def tokenize_text(text):
    """Tokenize text using simple approach without NLTK"""
    if not text:
        return []
    
    # Simple tokenization
    text = text.lower()
    for char in string.punctuation:
        text = text.replace(char, " ")
    
    # Basic stop words list (most common English stop words)
    stop_words = {"the", "and", "is", "in", "it", "to", "that", "of", "for", "on", "with", 
                 "as", "this", "by", "at", "an", "are", "was", "were", "be", "have", "has"}
    
    return [word for word in text.split() if len(word) > 2 and word not in stop_words]

def get_sentiment(text):
    """Analyze sentiment using TextBlob if available, otherwise use simple approach"""
    if not text:
        return {"polarity": 0, "subjectivity": 0}
        
    if textblob_available:
        try:
            blob = TextBlob(text)
            return {"polarity": blob.sentiment.polarity, "subjectivity": blob.sentiment.subjectivity}
        except Exception:
            pass
    
    # Simple sentiment analysis as fallback
    words = re.findall(r"\b\w+\b", text.lower())
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    total_count = len(words) or 1  # Avoid division by zero
    polarity = (positive_count - negative_count) / total_count
    subjectivity = (positive_count + negative_count) / total_count
    
    # Scale to similar ranges as TextBlob
    polarity = max(-1.0, min(1.0, polarity * 5))
    subjectivity = min(1.0, subjectivity * 5)
    
    return {"polarity": polarity, "subjectivity": subjectivity}

def extract_keywords(tokens, top_n=15):
    """Extract most frequent and relevant keywords from tokens"""
    if not tokens:
        return DEFAULT_KEYWORDS
        
    # Count word frequencies
    word_freq = Counter(tokens)
    
    # Get the most common words
    common_words = [word for word, _ in word_freq.most_common(top_n * 2)]
    
    # Prioritize words in brand attributes or value indicators
    priority_words = [
        word for word in common_words
        if word in BRAND_ATTRIBUTES or word in VALUE_INDICATORS
    ]
    
    # Combine priority words with other common words
    keywords = list(priority_words)
    for word in common_words:
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= top_n:
            break
    
    # Fill with defaults if needed
    while len(keywords) < top_n:
        for word in DEFAULT_KEYWORDS:
            if word not in keywords:
                keywords.append(word)
            if len(keywords) >= top_n:
                break
    
    return keywords[:top_n]

def extract_key_values(text, keywords, brand_name=""):
    """Extract key brand values from content without NLTK"""
    if not text:
        return DEFAULT_ANALYSIS["key_values"]
        
    key_values = []
    
    # Find sentences containing value indicators - simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    
    # Analyze sentences for value mentions
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for indicator in VALUE_INDICATORS:
            if indicator in sentence_lower:
                # Look for brand attributes in the sentence
                for attr in BRAND_ATTRIBUTES:
                    if attr in sentence_lower and attr.title() not in key_values:
                        key_values.append(attr.title())
    
    # Add values from keywords
    for word in keywords:
        if (word in VALUE_INDICATORS or word in BRAND_ATTRIBUTES) and word.title() not in key_values:
            key_values.append(word.title())
    
    # Create compound values if needed
    if len(key_values) < 5:
        prefixes = ["Customer", "Quality", "Professional"]
        for word in keywords:
            if len(key_values) >= 5:
                break
            for prefix in prefixes:
                compound = f"{prefix} {word.title()}"
                if compound not in key_values:
                    key_values.append(compound)
                    break
    
    # Include brand name in values if provided
    if brand_name and len(brand_name.split()) == 1 and len(key_values) < 5:
        brand_value = f"{brand_name} Excellence"
        if brand_value not in key_values:
            key_values.append(brand_value)
    
    # Fill with defaults if needed
    while len(key_values) < 5:
        for value in DEFAULT_ANALYSIS["key_values"]:
            if value not in key_values:
                key_values.append(value)
            if len(key_values) >= 5:
                break
    
    return key_values[:5]  # Return top 5

def analyze_tone(sentiment):
    """Determine tone profile based on sentiment analysis"""
    tones = DEFAULT_ANALYSIS["tone_analysis"].copy()
    
    try:
        polarity = sentiment.get("polarity", 0)
        subjectivity = sentiment.get("subjectivity", 0)
        
        # Adjust tone based on sentiment values
        if polarity > 0.2:
            tones["enthusiastic"] = min(0.8, 0.4 + polarity)
            tones["friendly"] = min(0.7, 0.3 + polarity)
        elif polarity < -0.1:
            tones["formal"] = min(0.8, 0.3 + abs(polarity))
            tones["professional"] = min(0.7, 0.2 + abs(polarity))
        else:
            tones["informative"] = 0.6
            tones["professional"] = 0.5
        
        # Adjust based on subjectivity
        if subjectivity > 0.5:
            tones["friendly"] = min(0.8, tones["friendly"] + 0.2)
            tones["enthusiastic"] = min(0.8, tones["enthusiastic"] + 0.1)
        else:
            tones["professional"] = min(0.8, tones["professional"] + 0.2)
            tones["formal"] = min(0.8, tones["formal"] + 0.1)
        
        # Ensure minimum values
        for tone in tones:
            tones[tone] = max(0.2, tones[tone])
            
        return tones
    except Exception:
        return DEFAULT_ANALYSIS["tone_analysis"]

def analyze_content(website_content, social_content):
    """
    Analyze website and social content to extract key brand attributes.
    
    Args:
        website_content (dict): Extracted content from website
        social_content (list): Content from social media profiles
        
    Returns:
        dict: Analysis results including keywords, tone, values, and sentiment
    """
    try:
        # Default values in case extraction fails
        default_keywords = ["professional", "service", "quality", "experience", "solution"]
        default_values = ["Quality", "Innovation", "Service", "Excellence", "Integrity"]
        default_tone = {
            "professional": 0.7,
            "friendly": 0.4,
            "informative": 0.6,
            "enthusiastic": 0.3,
            "formal": 0.5,
        }
        default_sentiment = {"polarity": 0.1, "subjectivity": 0.3}
        
        # Start with defaults
        analysis = {
            "keywords": default_keywords.copy(),
            "key_values": default_values.copy(),
            "tone_analysis": default_tone.copy(),
            "sentiment": default_sentiment.copy()
        }
        
        # Extract keywords and values from website content if possible
        if website_content:
            # Try to extract keywords from description or content
            description = website_content.get("description", "")
            if description and len(description) > 10:
                # Simple extraction by splitting and filtering
                words = description.lower().split()
                # Filter to keep only 4+ letter words that aren't common stopwords
                stopwords = ["this", "that", "with", "from", "their", "about", "have", "will"]
                potential_keywords = [word for word in words if len(word) >= 4 and word not in stopwords]
                
                # Take up to 5 unique keywords
                unique_keywords = []
                for word in potential_keywords:
                    if word not in unique_keywords:
                        unique_keywords.append(word)
                    if len(unique_keywords) >= 5:
                        break
                
                if unique_keywords:
                    analysis["keywords"] = unique_keywords
            
        # Analyze tone from social content if available
        if social_content:
            # Simple example of tone adjustment based on social platforms
            for platform in social_content:
                platform_name = platform.get("platform", "").lower()
                
                # Different platforms might suggest different brand tones
                if platform_name == "linkedin":
                    analysis["tone_analysis"]["professional"] += 0.1
                    analysis["tone_analysis"]["formal"] += 0.1
                elif platform_name in ["instagram", "tiktok"]:
                    analysis["tone_analysis"]["friendly"] += 0.1
                    analysis["tone_analysis"]["enthusiastic"] += 0.15
                    analysis["tone_analysis"]["formal"] -= 0.05
        
            # Normalize tone values to be between 0 and 1
            for tone in analysis["tone_analysis"]:
                analysis["tone_analysis"][tone] = max(0, min(analysis["tone_analysis"][tone], 1))
                
        return analysis
        
    except Exception as e:
        # Return default analysis if processing fails
        return {
            "keywords": default_keywords,
            "key_values": default_values,
            "tone_analysis": default_tone,
            "sentiment": default_sentiment
        }
