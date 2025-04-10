from collections import Counter
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string

class ContentAnalyzer:
    def __init__(self):
        # Download necessary NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('sentiment/vader_lexicon.zip')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt')
            nltk.download('vader_lexicon')
            nltk.download('stopwords')
            nltk.download('wordnet')
        
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.sia = SentimentIntensityAnalyzer()
    
    def analyze(self, website_content, social_media_content):
        """Analyze all content to extract insights"""
        all_text = self._combine_all_text(website_content, social_media_content)
        
        # Perform various analyses
        sentiment = self._analyze_sentiment(all_text)
        keywords = self._extract_keywords(all_text)
        topics = self._extract_topics(all_text)
        tone = self._analyze_tone(all_text)
        values = self._extract_values(all_text)
        engagement = self._analyze_engagement(social_media_content)
        
        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "topics": topics,
            "tone": tone,
            "values": values,
            "engagement": engagement
        }
    
    def _combine_all_text(self, website_content, social_media_content):
        """Combine all text content into a single string for analysis"""
        all_text = ""
        
        # Add website content
        for page in website_content:
            if 'content' in page:
                content = page['content']
                all_text += f"{content.get('title', '')} "
                all_text += f"{content.get('meta_description', '')} "
                all_text += " ".join(content.get('headings', [])) + " "
                all_text += content.get('full_text', '') + " "
        
        # Add social media content
        for platform, data in social_media_content.items():
            # Add profile information
            profile = data.get('profile', {})
            for key, value in profile.items():
                if isinstance(value, str):
                    all_text += f"{value} "
            
            # Add posts content
            for post in data.get('posts', []):
                for key, value in post.items():
                    if isinstance(value, str) and key in ['text', 'content', 'caption', 'description', 'title']:
                        all_text += f"{value} "
        
        return all_text
    
    def _preprocess_text(self, text):
        """Clean and preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove mentions and hashtags for cleaner analysis
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove punctuation and stopwords
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                  if token not in string.punctuation and token not in self.stop_words and len(token) > 2]
        
        return tokens
    
    def _analyze_sentiment(self, text):
        """Analyze the overall sentiment of the content"""
        sentiment_scores = self.sia.polarity_scores(text)
        
        # Determine overall sentiment
        if sentiment_scores['compound'] >= 0.05:
            overall = "positive"
        elif sentiment_scores['compound'] <= -0.05:
            overall = "negative"
        else:
            overall = "neutral"
            
        return {
            "overall": overall,
            "compound_score": sentiment_scores['compound'],
            "positive": sentiment_scores['pos'],
            "negative": sentiment_scores['neg'],
            "neutral": sentiment_scores['neu']
        }
    
    def _extract_keywords(self, text, top_n=20):
        """Extract the most important keywords"""
        tokens = self._preprocess_text(text)
        frequency = Counter(tokens)
        
        # Get most common words
        keywords = [word for word, count in frequency.most_common(top_n)]
        
        # Calculate relevance score (simplified)
        total = sum(frequency.values())
        keyword_scores = {word: count/total for word, count in frequency.most_common(top_n)}
        
        return {
            "list": keywords,
            "scores": keyword_scores
        }
    
    def _extract_topics(self, text):
        """Extract main topics from content"""
        # In a real implementation, this would use topic modeling like LDA
        # For simplicity, we'll use a keyword-based approach here
        tokens = self._preprocess_text(text)
        frequency = Counter(tokens)
        
        # Simplified topic detection based on keyword clusters
        technology_words = set(['technology', 'innovation', 'digital', 'software', 'app', 'data', 'ai', 'platform'])
        business_words = set(['business', 'company', 'service', 'solution', 'customer', 'client', 'industry', 'market'])
        lifestyle_words = set(['lifestyle', 'health', 'wellness', 'fashion', 'travel', 'food', 'fitness', 'beauty'])
        
        tech_count = sum(frequency[word] for word in tokens if word in technology_words)
        business_count = sum(frequency[word] for word in tokens if word in business_words)
        lifestyle_count = sum(frequency[word] for word in tokens if word in lifestyle_words)
        
        topics = []
        if tech_count > 5:
            topics.append("Technology")
        if business_count > 5:
            topics.append("Business")
        if lifestyle_count > 5:
            topics.append("Lifestyle")
            
        return topics
    
    def _analyze_tone(self, text):
        """Analyze the tone of the content"""
        sentences = sent_tokenize(text)
        
        # Check for various tone indicators
        formal_indicators = ['therefore', 'consequently', 'furthermore', 'thus', 'hence']
        casual_indicators = ['hey', 'cool', 'awesome', 'yeah', 'btw', 'check out']
        enthusiastic_indicators = ['!', 'amazing', 'excited', 'love', 'incredible', 'awesome']
        professional_indicators = ['professional', 'expertise', 'solution', 'industry-leading', 'certified']
        
        formal_count = sum(1 for s in sentences if any(ind in s.lower() for ind in formal_indicators))
        casual_count = sum(1 for s in sentences if any(ind in s.lower() for ind in casual_indicators))
        enthusiastic_count = sum(1 for s in sentences if any(ind in s.lower() for ind in enthusiastic_indicators))
        professional_count = sum(1 for s in sentences if any(ind in s.lower() for ind in professional_indicators))
        exclamation_count = text.count('!')
        
        tones = []
        if formal_count > casual_count:
            tones.append("formal")
        else:
            tones.append("casual")
            
        if enthusiastic_count > 5 or exclamation_count > 10:
            tones.append("enthusiastic")
            
        if professional_count > 5:
            tones.append("professional")
            
        # Sentiment can also inform tone
        sentiment = self._analyze_sentiment(text)
        if sentiment['overall'] == 'positive':
            tones.append("positive")
        elif sentiment['overall'] == 'negative':
            tones.append("negative")
        
        return tones
    
    def _extract_values(self, text):
        """Extract company values from content"""
        values_dict = {
            "innovation": ['innovation', 'innovative', 'cutting-edge', 'pioneer', 'revolutionary', 'disrupt'],
            "quality": ['quality', 'excellence', 'premium', 'best-in-class', 'superior', 'exceptional'],
            "customer-focus": ['customer', 'client', 'satisfaction', 'experience', 'service', 'support'],
            "integrity": ['integrity', 'honest', 'transparent', 'ethical', 'trust', 'reliable'],
            "sustainability": ['sustainable', 'environment', 'green', 'eco', 'responsible', 'planet'],
            "community": ['community', 'social', 'give back', 'volunteer', 'impact', 'responsibility'],
            "diversity": ['diversity', 'inclusion', 'equal', 'inclusive', 'diverse', 'representation']
        }
        
        values_scores = {}
        for value, keywords in values_dict.items():
            score = sum(1 for keyword in keywords if keyword in text.lower())
            if score > 0:
                values_scores[value] = score
        
        # Return top values
        sorted_values = sorted(values_scores.items(), key=lambda x: x[1], reverse=True)
        return [value for value, score in sorted_values[:3]]
    
    def _analyze_engagement(self, social_media_content):
        """Analyze engagement across social platforms"""
        engagement = {}
        
        for platform, data in social_media_content.items():
            platform_engagement = {
                "follower_count": 0,
                "post_count": len(data.get('posts', [])),
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_shares": 0,
                "total_engagement": 0
            }
            
            # Get follower count
            profile = data.get('profile', {})
            for key in profile:
                if 'follower' in key.lower() and isinstance(profile[key], (int, float)):
                    platform_engagement["follower_count"] = profile[key]
            
            # Calculate engagement metrics
            likes_total = 0
            comments_total = 0
            shares_total = 0
            
            for post in data.get('posts', []):
                # Different platforms use different terms for engagement
                if platform == 'twitter':
                    likes_total += post.get('likes', 0)
                    comments_total += post.get('replies', 0)
                    shares_total += post.get('retweets', 0)
                elif platform == 'facebook':
                    likes_total += post.get('reactions', 0)
                    comments_total += post.get('comments', 0)
                    shares_total += post.get('shares', 0)
                elif platform == 'instagram':
                    likes_total += post.get('likes', 0)
                    comments_total += post.get('comments', 0)
                elif platform == 'linkedin':
                    likes_total += post.get('reactions', 0)
                    comments_total += post.get('comments', 0)
                    shares_total += post.get('shares', 0)
            
            post_count = platform_engagement["post_count"]
            if post_count > 0:
                platform_engagement["avg_likes"] = likes_total / post_count
                platform_engagement["avg_comments"] = comments_total / post_count
                platform_engagement["avg_shares"] = shares_total / post_count
                platform_engagement["total_engagement"] = (likes_total + comments_total + shares_total) / post_count
            
            engagement[platform] = platform_engagement
        
        return engagement
