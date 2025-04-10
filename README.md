# Brand Story Generator

A tool that generates a comprehensive brand story by analyzing a company's website and social media presence.

## Features

- Crawls websites to extract content and find social media links
- Simulates content from various social media platforms (Twitter, Facebook, Instagram, LinkedIn, YouTube, TikTok)
- Analyzes content for tone, keywords, values, and audience engagement
- Generates a human-readable brand story that reflects the company's voice and identity

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

Note: No API keys are required as the program uses simulated data for demonstration purposes.

## Usage

Run the program with a website URL:

```
python brand_story_generator.py https://example.com
```

Optional arguments:
- `--output` or `-o`: Output file path for the brand story (default: brand_story.md)

Example:
```
python brand_story_generator.py https://example.com --output my_brand_story.md
```

## How It Works

1. **Web Crawling**: The program crawls the given website to extract content and find social media links.
2. **Social Media Simulation**: It simulates content from detected social media platforms for demonstration purposes.
3. **Content Analysis**: All gathered content is analyzed using NLP techniques to identify tone, sentiment, keywords, topics, values, and engagement metrics.
4. **Story Generation**: Based on the analysis, the program generates a comprehensive brand story using a template-based approach.

## Output

The program generates a markdown file with the following sections:
- Brand Essence
- Origin and Mission
- Values and Personality
- Target Audience
- Key Messaging Themes
- Brand Voice
- Social Media Highlights
- Conclusion

## Limitations

- The program uses simulated social media data for demonstration purposes
- Website crawling has a default limit of 10 pages to avoid excessive requests
