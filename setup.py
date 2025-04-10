#!/usr/bin/env python
"""
Setup script to download required NLTK and TextBlob resources.
Run this before starting the application.
"""

import nltk
import sys
import os
import subprocess

def main():
    print("Setting up NLTK and TextBlob resources...")
    
    # Create directories for NLTK data if they don't exist
    nltk_data_dir = os.path.expanduser("~/nltk_data")
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir, exist_ok=True)
    
    # Download NLTK resources
    try:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', quiet=True)
        print("Downloading NLTK stopwords...")
        nltk.download('stopwords', quiet=True)
        print("Downloading NLTK brown corpus...")
        nltk.download('brown', quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK resources: {str(e)}")
        print("You may need to manually download these resources.")
    
    # Download TextBlob resources
    try:
        print("Downloading TextBlob corpora...")
        subprocess.run([sys.executable, "-m", "textblob.download_corpora"], check=True)
    except Exception as e:
        print(f"Error downloading TextBlob corpora: {str(e)}")
        print("You may need to manually download these resources with: python -m textblob.download_corpora")
    
    print("\nSetup complete! You can now run the application with: python app.py")

if __name__ == "__main__":
    main()