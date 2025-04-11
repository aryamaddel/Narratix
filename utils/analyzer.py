import re
from collections import Counter

# Core lists for analysis
POSITIVE_WORDS = {"good", "great", "excellent", "amazing", "best", "love", "quality", "reliable", "trusted"}
NEGATIVE_WORDS = {"bad", "poor", "terrible", "awful", "worst", "hate", "sorry", "negative", "problem", "failure"}
VALUE_INDICATORS = {"quality", "innovation", "excellence", "integrity", "service", "customer", "solution", "expert"}
DEFAULT_KEYWORDS = ["professional", "service", "quality", "experience", "solution", "innovation", "customer"]
DEFAULT_KEY_VALUES = ["Quality", "Innovation", "Customer Focus", "Excellence", "Integrity"]
DEFAULT_TONES = {
    "professional": 0.7,
    "friendly": 0.4,
    "informative": 0.6,
    "enthusiastic": 0.3,
    "formal": 0.5,
}

def simple_tokenize(text):
    """Simple tokenization for text analysis"""
    text = text.lower()
    # Remove punctuation and split
    text = re.sub(r'[^\w\s]', ' ', text)
    return [word for word in text.split() if len(word) > 2]

def simple_sentiment_analysis(text):
    """Simple sentiment analysis based on word counting"""
    words = simple_tokenize(text)
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    total_words = len(words)
    if total_words > 0:
        polarity = (positive_count - negative_count) / max(total_words, 1)
        subjectivity = (positive_count + negative_count) / max(total_words, 1)
    else:
        polarity = 0
        subjectivity = 0
        
    # Scale to standard ranges
    polarity = max(-1.0, min(1.0, polarity * 5))
    subjectivity = min(1.0, subjectivity * 5)
    
    return {"polarity": polarity, "subjectivity": subjectivity}

def extract_keywords(tokens, top_n=10):
    """Extract most common meaningful words as keywords"""
    # Count word frequencies and get common words
    word_freq = Counter(tokens)
    keywords = [word for word, _ in word_freq.most_common(top_n*2) 
                if word in VALUE_INDICATORS or len(word) > 3][:top_n]
    
    # Add default keywords if needed
    while len(keywords) < top_n:
        for word in DEFAULT_KEYWORDS:
            if word not in keywords:
                keywords.append(word)
            if len(keywords) >= top_n:
                break
                
    return keywords[:top_n]

def analyze_content(website_content, social_content):
    """Simplified content analysis that extracts basic insights"""
    try:
        # Extract content
        website_text = website_content.get("content", "")
        
        # Add social content
        social_texts = [social.get("content", "") for social in social_content if "content" in social]
        all_text = website_text + " " + " ".join(social_texts)
        
        # If content is too short, use defaults
        if len(all_text) < 50:
            return {
                "keywords": DEFAULT_KEYWORDS[:10],
                "tone_analysis": DEFAULT_TONES,
                "key_values": DEFAULT_KEY_VALUES,
                "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
            }
            
        # Analyze sentiment
        sentiment = simple_sentiment_analysis(all_text)
        
        # Tokenize and extract keywords
        tokens = simple_tokenize(all_text)
        keywords = extract_keywords(tokens)
        
        # Use default values for key_values and tones
        key_values = DEFAULT_KEY_VALUES
        tone_analysis = DEFAULT_TONES
        
        # Slightly adjust tone based on sentiment
        if sentiment["polarity"] > 0.2:
            tone_analysis["friendly"] = min(0.8, tone_analysis["friendly"] + 0.2)
            tone_analysis["enthusiastic"] = min(0.8, tone_analysis["enthusiastic"] + 0.2)
        elif sentiment["polarity"] < -0.1:
            tone_analysis["formal"] = min(0.8, tone_analysis["formal"] + 0.2)
            
        return {
            "keywords": keywords,
            "tone_analysis": tone_analysis,
            "key_values": key_values,
            "sentiment": sentiment,
        }
    except Exception:
        # Return defaults on error
        return {
            "keywords": DEFAULT_KEYWORDS[:10],
            "tone_analysis": DEFAULT_TONES,
            "key_values": DEFAULT_KEY_VALUES,
            "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
        }
