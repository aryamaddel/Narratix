# Narratix

Narratix is a brand story generator tool that analyzes websites and social media profiles to create comprehensive brand stories, visual identity recommendations, and consistency scores.

## Features

- Website content analysis
- Social media profile detection and analysis
- Brand story generation
- Visual identity recommendations
- Brand consistency scoring
- AI-powered content analysis (optional with Gemini)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/narratix.git
   cd narratix
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) Configure Gemini API:
   - Create a `.env` file in the project root
   - Add your Gemini API key: `GEMINI_API_KEY=your_api_key_here`

## Usage

1. Start the Flask development server:
   ```
   flask run
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. Enter a website URL to analyze

## Project Structure

- `app.py` - Main Flask application
- `utils/` - Utility modules
  - `brand_analyzer.py` - Main brand analysis functions
  - `core/` - Core infrastructure (HTTP, platforms)
  - `extractors/` - Platform-specific content extractors
  - `analysis/` - Content analysis tools
  - `generation/` - Content generation functions
  - `word_lists/` - Word lists for analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
