import os
import logging

logger = logging.getLogger(__name__)

# Try to import the Google Generative AI libraries
try:
    import google.generativeai as genai
    from google.generativeai import types
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Set the specific model that's known to work
        DEFAULT_MODEL = "gemini-2.5-pro-exp-03-25"
        try:
            # Still check available models for logging purposes
            models = genai.list_models()
            available_models = [m.name for m in models]
            logger.debug(f"Available Gemini models: {available_models}")
            
            # Check if our specific model is in the available models
            if f"models/{DEFAULT_MODEL}" in available_models or DEFAULT_MODEL in available_models:
                logger.info(f"Specified model {DEFAULT_MODEL} is available")
                GEMINI_AVAILABLE = True
            else:
                logger.warning(f"Specified model {DEFAULT_MODEL} not found in available models, but will try to use it anyway")
                GEMINI_AVAILABLE = True
        except Exception as e:
            # If we can't list models, still try to use the specified model
            logger.warning(f"Could not list Gemini models: {str(e)}, assuming {DEFAULT_MODEL} is available")
            GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
        DEFAULT_MODEL = None
        logger.warning("Gemini API key not found in environment variables")
except ImportError:
    GEMINI_AVAILABLE = False
    DEFAULT_MODEL = None
    logger.warning("Gemini libraries not installed")
