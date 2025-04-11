import os
from groq import Groq

# Configure Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")

groq_client = Groq(api_key=GROQ_API_KEY)


def generate_with_groq(prompt):
    """Generate content using Groq API"""
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional brand storyteller",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_completion_tokens=2048,
            top_p=1,
        )
        return completion.choices[0].message.content
    except Exception:
        return None
