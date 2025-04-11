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

    # Create directories for NLTK data in the current directory
    nltk_data_dir = os.path.join(os.getcwd(), "nltk_data")
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir, exist_ok=True)

    # Set the NLTK data path to the current directory
    nltk.data.path.append(nltk_data_dir)

    # Download NLTK resources
    try:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download("punkt", download_dir=nltk_data_dir, quiet=True)
        print("Downloading NLTK stopwords...")
        nltk.download("stopwords", download_dir=nltk_data_dir, quiet=True)
        print("Downloading NLTK brown corpus...")
        nltk.download("brown", download_dir=nltk_data_dir, quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK resources: {str(e)}")
        print("You may need to manually download these resources.")

    # Download TextBlob resources
    try:
        print("Downloading TextBlob corpora...")
        subprocess.run([sys.executable, "-m", "textblob.download_corpora"], check=True)
    except Exception as e:
        print(f"Error downloading TextBlob corpora: {str(e)}")
        print(
            "You may need to manually download these resources with: python -m textblob.download_corpora"
        )

    print("\nSetup complete! You can now run the application with: python app.py")


if __name__ == "__main__":
    main()
