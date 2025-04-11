import os
import google.generativeai as genai

# Configure Gemini API if environment variable is set
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_AVAILABLE = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception:
        pass

def is_available():
    """Check if Gemini API is available"""
    return GEMINI_AVAILABLE

def generate_with_gemini(prompt):
    """Generate content using Google's Gemini AI model"""
    if not is_available():
        return None

    try:
        # Try with different model versions in order of preference
        for model_name in ["gemini-2.5-pro-exp-03-25", "models/gemini-2.5-pro-exp-03-25", "gemini-pro"]:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and hasattr(response, "text"):
                    return response.text
            except Exception:
                continue  # Try next model name
        
        return None  # All models failed
    except Exception:
        return None
