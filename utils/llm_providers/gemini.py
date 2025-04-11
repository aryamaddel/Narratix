import os
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

def generate_with_gemini(prompt):
    """Generate content using Google's Gemini AI model"""
    model_options = ["gemini-2.5-pro-exp-03-25", "models/gemini-2.5-pro-exp-03-25", "gemini-pro"]
    
    for model_name in model_options:
        try:
            response = genai.GenerativeModel(model_name).generate_content(prompt)
            if response and hasattr(response, "text"):
                return response.text
        except Exception:
            continue
    
    return None
