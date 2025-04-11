import os

# Attempt to import Groq
try:
    from groq import Groq
    GROQ_IMPORTABLE = True
except ImportError:
    GROQ_IMPORTABLE = False

# Configure Groq API if environment variable is set
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_AVAILABLE = False
groq_client = None

if GROQ_API_KEY and GROQ_IMPORTABLE:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
    except Exception:
        pass

def is_available():
    """Check if Groq API is available"""
    return GROQ_AVAILABLE

def generate_with_groq(prompt):
    """Generate content using Groq API"""
    if not is_available():
        return None
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional brand storyteller who creates comprehensive, well-structured brand narratives."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_completion_tokens=2048,
            top_p=1,
        )
        
        return chat_completion.choices[0].message.content
    except Exception:
        return None
