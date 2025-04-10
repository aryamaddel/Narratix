import argparse
from website_crawler import WebsiteCrawler
from social_media_fetcher import SocialMediaFetcher
from content_analyzer import ContentAnalyzer
from story_generator import StoryGenerator

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a brand story from a website URL')
    parser.add_argument('--url', help='The URL of the company website', default=None)
    parser.add_argument('--output', '-o', help='Output file path for the brand story', default='brand_story.md')
    args = parser.parse_args()
    
    # Get URL from user input if not provided as command-line argument
    url = args.url
    if url is None:
        url = input("Please enter the company website URL: ")
    
    print(f"Starting brand story generation for {url}")
    
    # Step 1: Crawl website to find social media links
    crawler = WebsiteCrawler(url)
    website_content, social_links = crawler.crawl()
    print(f"Found {len(social_links)} social media links")
    
    # Step 2: Fetch/simulate content from social media platforms
    fetcher = SocialMediaFetcher()
    social_media_content = fetcher.fetch_all(social_links)
    
    # Step 3: Analyze content
    analyzer = ContentAnalyzer()
    analysis = analyzer.analyze(website_content, social_media_content)
    
    # Step 4: Generate brand story
    generator = StoryGenerator()
    brand_story = generator.generate(website_content, social_media_content, analysis)
    
    # Save the brand story to file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(brand_story)
    
    print(f"Brand story generated successfully and saved to {args.output}")

if __name__ == '__main__':
    main()
