import re
from collections import Counter

# Simplified word lists
POSITIVE_WORDS = {"good", "great", "excellent", "amazing", "best", "love", "quality", "reliable"}
NEGATIVE_WORDS = {"bad", "poor", "terrible", "awful", "worst", "hate", "problem"}
VALUE_WORDS = {"quality", "innovation", "excellence", "integrity", "service", "customer", "solution"}

def analyze_content(website_content, social_content):
    """Simplified content analysis"""
    try:
        # Combine text from website and social
        website_text = website_content.get("content", "")
        social_texts = [s.get("content", "") for s in social_content if s.get("content")]
        all_text = website_text + " " + " ".join(social_texts)
        
        # Default values if text is too short
        if len(all_text) < 50:
            return {
                "keywords": ["professional", "service", "quality", "innovation", "customer"],
                "key_values": ["Quality", "Innovation", "Customer Focus", "Excellence"],
                "tone_analysis": {"professional": 0.7, "friendly": 0.4, "informative": 0.6},
                "sentiment": {"polarity": 0.1, "subjectivity": 0.3}
            }
        
        # Tokenize
        text = all_text.lower()
        words = [word for word in re.sub(r'[^\w\s]', ' ', text).split() if len(word) > 2]
        
        # Simple sentiment analysis
        pos_count = sum(1 for word in words if word in POSITIVE_WORDS)
        neg_count = sum(1 for word in words if word in NEGATIVE_WORDS)
        
        polarity = (pos_count - neg_count) / max(len(words), 1)
        subjectivity = (pos_count + neg_count) / max(len(words), 1)
        
        # Scale values
        polarity = max(-0.5, min(0.5, polarity * 3))
        subjectivity = min(0.6, subjectivity * 3)
        
        # Extract keywords
        word_counts = Counter(words)
        keywords = [word for word, _ in word_counts.most_common(15) if len(word) > 3 or word in VALUE_WORDS][:10]
        
        # Ensure we have at least 5 keywords
        if len(keywords) < 5:
            for word in ["professional", "quality", "service", "innovation", "customer"]:
                if word not in keywords:
                    keywords.append(word)
                if len(keywords) >= 5:
                    break
        
        # Key values and tone (simplified)
        key_values = ["Quality", "Innovation", "Customer Focus", "Excellence"]
        tone = {"professional": 0.7, "friendly": 0.4, "informative": 0.6}
        
        # Adjust tone based on sentiment
        if polarity > 0.2:
            tone["friendly"] = min(0.8, tone["friendly"] + 0.2)
        
        return {
            "keywords": keywords,
            "key_values": key_values,
            "tone_analysis": tone,
            "sentiment": {"polarity": polarity, "subjectivity": subjectivity}
        }
    except Exception:
        # Simple default values
        return {
            "keywords": ["professional", "service", "quality", "innovation", "customer"],
            "key_values": ["Quality", "Innovation", "Customer Focus", "Excellence"],
            "tone_analysis": {"professional": 0.7, "friendly": 0.4, "informative": 0.6},
            "sentiment": {"polarity": 0.1, "subjectivity": 0.3}
        }
