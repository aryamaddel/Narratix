import re
import string
from collections import Counter

# Default lists - used when NLP libraries fail
DEFAULT_STOPWORDS = {
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "you're",
    "you've",
    "you'll",
    "you'd",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "she's",
    "her",
    "hers",
    "herself",
    "it",
    "it's",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "that'll",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "don't",
    "should",
    "should've",
    "now",
    "d",
    "ll",
    "m",
    "o",
    "re",
    "ve",
    "y",
    "ain",
    "aren",
    "aren't",
    "couldn",
    "couldn't",
    "didn",
    "didn't",
    "doesn",
    "doesn't",
    "hadn",
    "hadn't",
    "hasn",
    "hasn't",
    "haven",
    "haven't",
    "isn",
    "isn't",
    "ma",
    "mightn",
    "mightn't",
    "mustn",
    "mustn't",
    "needn",
    "needn't",
    "shan",
    "shan't",
    "shouldn",
    "shouldn't",
    "wasn",
    "wasn't",
    "weren",
    "weren't",
    "won",
    "won't",
    "wouldn",
    "wouldn't",
}

POSITIVE_WORDS = {
    "good",
    "great",
    "excellent",
    "amazing",
    "wonderful",
    "best",
    "love",
    "happy",
    "positive",
    "success",
    "successful",
    "innovative",
    "quality",
    "reliable",
    "trusted",
    "leading",
    "premium",
    "outstanding",
    "perfect",
    "impressive",
    "exceptional",
    "fantastic",
    "fabulous",
    "brilliant",
    "delightful",
    "helpful",
    "favorable",
    "superior",
    "pleasant",
    "remarkable",
    "satisfying",
    "skilled",
    "stunning",
    "supportive",
    "terrific",
    "thriving",
    "valuable",
    "versatile",
    "vibrant",
    "worthy",
    "abundant",
    "accomplished",
    "achieving",
    "active",
    "adept",
    "admirable",
    "adorable",
    "adored",
    "advanced",
    "advantageous",
    "appealing",
    "appreciated",
    "authentic",
    "beautiful",
    "beneficial",
    "blissful",
    "bountiful",
    "brave",
    "bright",
    "brilliant",
    "capable",
    "celebrated",
    "champion",
    "charming",
    "cherished",
    "choice",
    "classic",
    "clean",
    "clear",
    "clever",
    "collaborative",
    "committed",
    "competent",
    "complete",
    "comprehensive",
    "confident",
    "consistent",
    "convenient",
    "creative",
    "credible",
    "customer-focused",
    "dazzling",
    "dedicated",
    "delicious",
    "delightful",
    "dependable",
    "deserving",
    "desirable",
    "determined",
    "devoted",
    "diligent",
    "distinguished",
    "dreamy",
    "driven",
    "dynamic",
    "easy",
    "economical",
    "educated",
    "effective",
    "efficient",
    "effortless",
    "elegant",
    "elite",
    "empowering",
    "enchanting",
    "encouraging",
    "endorsed",
    "energetic",
    "engaging",
    "enhanced",
    "enjoyable",
    "enlightened",
    "enriching",
    "enthusiastic",
    "essential",
    "esteemed",
    "ethical",
    "excellent",
    "exclusive",
    "exemplary",
    "exquisite",
    "extraordinary",
    "exuberant",
}

NEGATIVE_WORDS = {
    "bad",
    "poor",
    "terrible",
    "awful",
    "worst",
    "hate",
    "sorry",
    "negative",
    "difficult",
    "problem",
    "failure",
    "concern",
    "disappointing",
    "disappointed",
    "fail",
    "failed",
    "failing",
    "poor",
    "poorly",
    "subpar",
    "mediocre",
    "inferior",
    "useless",
    "broken",
    "abysmal",
    "adverse",
    "alarming",
    "angry",
    "annoying",
    "anxious",
    "appalling",
    "atrocious",
    "awful",
    "banal",
    "boring",
    "broken",
    "callous",
    "clumsy",
    "coarse",
    "cold",
    "confused",
    "contradictory",
    "contrary",
    "corrosive",
    "corrupt",
    "crazy",
    "creepy",
    "criminal",
    "cruel",
    "damaging",
    "daunting",
    "dead",
    "decaying",
    "deformed",
    "denied",
    "deplorable",
    "depressed",
    "deprived",
    "despicable",
    "detrimental",
    "dirty",
    "disgusting",
    "dishonest",
    "dishonorable",
    "dismal",
    "distress",
    "disturbed",
    "dreadful",
    "dreary",
    "enraged",
    "eroding",
    "evil",
    "faulty",
    "feeble",
    "filthy",
    "foul",
    "frightful",
    "frustrating",
    "ghastly",
    "grave",
    "greedy",
    "grim",
    "grimace",
    "gross",
    "grotesque",
    "gruesome",
    "guilty",
    "haggard",
    "hard",
    "harmful",
    "harsh",
    "hideous",
    "horrendous",
    "horrible",
    "hostile",
    "hurt",
    "hurtful",
    "icky",
    "ignorant",
    "ill",
    "immature",
    "imperfect",
    "impossible",
    "inaccurate",
    "inadequate",
    "incomplete",
    "incorrect",
    "ineffective",
    "inefficient",
    "inferior",
    "injurious",
    "insane",
    "insidious",
    "insipid",
    "intimidating",
    "irrational",
    "irritating",
    "lackadaisical",
    "lazy",
}

VALUE_INDICATORS = {
    "mission",
    "vision",
    "values",
    "believe",
    "committed",
    "dedication",
    "quality",
    "innovation",
    "excellence",
    "integrity",
    "sustainability",
    "responsibility",
    "trust",
    "community",
    "service",
    "customer",
    "passion",
    "creativity",
    "diversity",
    "inclusion",
    "empowerment",
    "care",
    "caring",
    "authentic",
    "authenticity",
    "accountable",
    "accountability",
    "transparent",
    "transparency",
    "ethical",
    "ethics",
    "respect",
    "respectful",
    "honesty",
    "honest",
    "reliable",
    "reliability",
    "teamwork",
    "collaboration",
    "collaborative",
    "people",
    "performance",
    "solution",
    "solutions",
    "driven",
    "focus",
    "focused",
    "future",
    "forward",
    "growth",
    "leading",
    "leader",
    "leadership",
    "expert",
    "expertise",
    "professional",
    "professionalism",
    "standard",
    "standards",
    "results",
    "pride",
    "proud",
    "commitment",
    "deliver",
    "delivering",
    "success",
    "successful",
    "support",
    "supporting",
    "satisfaction",
    "satisfying",
    "value",
    "valued",
    "develop",
    "developing",
    "development",
    "partner",
    "partnership",
}

BRAND_ATTRIBUTES = {
    "reliable",
    "innovative",
    "premium",
    "quality",
    "affordable",
    "luxury",
    "sustainable",
    "eco-friendly",
    "cutting-edge",
    "traditional",
    "modern",
    "trusted",
    "authentic",
    "responsive",
    "personal",
    "professional",
    "expert",
    "specialized",
    "global",
    "local",
    "fast",
    "efficient",
    "friendly",
    "approachable",
    "exclusive",
    "inclusive",
    "comprehensive",
    "seamless",
    "intuitive",
    "flexible",
    "adaptable",
    "customized",
    "custom",
    "personalized",
    "accessible",
    "secure",
    "safe",
    "reliable",
    "consistent",
    "dynamic",
    "energetic",
    "passionate",
    "creative",
    "innovative",
    "forward-thinking",
    "visionary",
    "established",
    "experienced",
    "knowledgeable",
    "respected",
    "renowned",
    "acclaimed",
    "award-winning",
    "advanced",
    "sophisticated",
    "elegant",
    "simple",
    "minimalist",
    "practical",
    "effective",
    "powerful",
    "robust",
    "versatile",
    "comprehensive",
    "complete",
    "holistic",
    "integrated",
    "streamlined",
    "optimized",
    "enhanced",
    "superior",
    "exceptional",
    "extraordinary",
    "distinctive",
    "unique",
    "original",
    "genuine",
    "authentic",
    "natural",
    "organic",
    "fresh",
    "clean",
}

DEFAULT_KEYWORDS = [
    "professional",
    "service",
    "quality",
    "experience",
    "solution",
    "innovation",
    "customer",
    "product",
    "industry",
    "leadership",
    "expertise",
    "excellence",
    "value",
    "team",
    "performance",
]

DEFAULT_KEY_VALUES = [
    "Quality",
    "Innovation",
    "Customer Focus",
    "Excellence",
    "Integrity",
]

DEFAULT_TONES = {
    "professional": 0.7,
    "friendly": 0.4,
    "informative": 0.6,
    "enthusiastic": 0.3,
    "formal": 0.5,
}

# Try to import NLTK (but continue without it if not available)
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords

    # Initialize NLTK resources with robust error handling
    nltk_resources_available = True

    try:
        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)
        except Exception as e:
            nltk_resources_available = False
except ImportError:
    nltk_resources_available = False

# Try to import TextBlob (but continue without it if not available)
try:
    from textblob import TextBlob

    # Try to use TextBlob to see if it works properly
    test_blob = TextBlob("Test sentence.")
    textblob_available = True
except:
    textblob_available = False


def simple_tokenize(text):
    """Simple tokenization function for when NLTK is not available"""
    # Convert to lowercase
    text = text.lower()

    # Replace punctuation with spaces
    for char in string.punctuation:
        text = text.replace(char, " ")

    # Split on whitespace and filter out short words
    return [word for word in text.split() if len(word) > 2]


def simple_sentence_tokenize(text):
    """Simple sentence tokenization for when NLTK is not available"""
    # Split on common sentence terminators
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Filter out empty sentences
    return [s.strip() for s in sentences if s.strip()]


def simple_sentiment_analysis(text):
    """Simple sentiment analysis without TextBlob"""
    # Convert to lowercase and tokenize
    words = re.findall(r"\b\w+\b", text.lower())

    # Count occurrences
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)

    # Calculate sentiment
    total_words = len(words)
    if total_words > 0:
        polarity = (positive_count - negative_count) / max(total_words, 1)
        subjectivity = (positive_count + negative_count) / max(total_words, 1)
    else:
        polarity = 0
        subjectivity = 0

    # Scale to similar ranges as TextBlob
    polarity = max(-1.0, min(1.0, polarity * 5))  # Scale to -1 to 1 range
    subjectivity = min(1.0, subjectivity * 5)  # Scale to 0 to 1 range

    return {"polarity": polarity, "subjectivity": subjectivity}


def extract_keywords(tokens, top_n=15):
    """Extract keywords from tokens"""
    # Count word frequencies
    word_freq = Counter(tokens)

    # Get the most common words
    top_words = [word for word, freq in word_freq.most_common(top_n * 2)]

    # Prioritize words that are in our brand attributes or value indicators
    priority_words = [
        word
        for word in top_words
        if word in BRAND_ATTRIBUTES or word in VALUE_INDICATORS
    ]

    # Add priority words first, then add other frequent words until we have enough
    keywords = []
    keywords.extend(priority_words)

    # Add remaining top words until we reach desired count
    for word in top_words:
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= top_n:
            break

    # Make sure we have enough keywords
    while len(keywords) < top_n:
        for word in DEFAULT_KEYWORDS:
            if word not in keywords:
                keywords.append(word)
            if len(keywords) >= top_n:
                break

    # Limit to top_n
    return keywords[:top_n]


def extract_key_values(content, keywords):
    """Extract key brand values from content"""
    key_values = []

    # First, try to find explicit value statements
    if nltk_resources_available:
        try:
            # Tokenize into sentences
            sentences = sent_tokenize(content)

            # Find sentences that might contain values
            value_sentences = []
            for sentence in sentences:
                lower_sentence = sentence.lower()
                if any(indicator in lower_sentence for indicator in VALUE_INDICATORS):
                    value_sentences.append(sentence)

            # Extract values from sentences containing value indicators
            for sentence in value_sentences[:5]:  # Limit to top 5 sentences
                # Look for attribute words near value indicators
                words = sentence.lower().split()
                for indicator in VALUE_INDICATORS:
                    if indicator in words:
                        idx = words.index(indicator)
                        # Check words near the indicator (window of 5 words)
                        start = max(0, idx - 2)
                        end = min(len(words), idx + 3)
                        for i in range(start, end):
                            if i < len(words) and words[i] in BRAND_ATTRIBUTES:
                                key_values.append(words[i].title())

                # If TextBlob available, try noun phrase extraction
                if textblob_available:
                    try:
                        sentence_blob = TextBlob(sentence)
                        for phrase in sentence_blob.noun_phrases:
                            if (
                                len(phrase.split()) <= 3
                            ):  # Keep phrases reasonably short
                                key_values.append(phrase.title())
                    except:
                        pass
        except Exception as e:
            # Silently ignore errors if NLTK fails
            pass
    else:
        # Simpler approach if NLTK not available
        sentences = simple_sentence_tokenize(content)

        # Find sentences with value indicators
        for sentence in sentences:
            lower_sentence = sentence.lower()
            for indicator in VALUE_INDICATORS:
                if indicator in lower_sentence:
                    # Find nearby words
                    for attr in BRAND_ATTRIBUTES:
                        if attr in lower_sentence:
                            key_values.append(attr.title())

    # If we still don't have enough values, extract from keywords
    if len(key_values) < 3:
        for word in keywords:
            if word in VALUE_INDICATORS or word in BRAND_ATTRIBUTES:
                key_values.append(word.title())

    # Add compound values based on keywords
    if len(key_values) < 5:
        for word in keywords:
            if word not in [v.lower() for v in key_values]:
                for prefix in ["Customer", "Quality", "Professional"]:
                    compound = f"{prefix} {word.title()}"
                    if compound not in key_values:
                        key_values.append(compound)
                        break
                if len(key_values) >= 5:
                    break

    # If still not enough, use default values
    if len(key_values) < 3:
        for value in DEFAULT_KEY_VALUES:
            if value not in key_values:
                key_values.append(value)
            if len(key_values) >= 5:
                break

    # Remove duplicates while preserving order
    unique_values = []
    seen = set()
    for value in key_values:
        if value.lower() not in seen:
            seen.add(value.lower())
            unique_values.append(value)

    # Return top 5 values
    return unique_values[:5]


def analyze_tone(sentiment):
    """Analyze tone based on sentiment"""
    # Map polarity to tones
    tones = {
        "professional": 0.0,
        "friendly": 0.0,
        "informative": 0.0,
        "enthusiastic": 0.0,
        "formal": 0.0,
    }

    try:
        polarity = sentiment.get("polarity", 0)
        subjectivity = sentiment.get("subjectivity", 0)

        # Determine the dominant tones based on sentiment analysis
        if polarity > 0.2:
            tones["enthusiastic"] = min(0.8, polarity + 0.4)
            tones["friendly"] = min(0.7, polarity + 0.3)
        elif polarity < -0.1:
            tones["formal"] = min(0.8, abs(polarity) + 0.3)
            tones["professional"] = min(0.7, abs(polarity) + 0.2)
        else:
            tones["informative"] = 0.6
            tones["professional"] = 0.5

        # Adjust based on subjectivity
        if subjectivity > 0.5:
            tones["friendly"] = min(0.8, tones["friendly"] + 0.2)
            tones["enthusiastic"] = min(0.8, tones["enthusiastic"] + 0.1)
        else:
            tones["professional"] = min(0.8, tones["professional"] + 0.2)
            tones["formal"] = min(0.8, tones["formal"] + 0.1)

        # Ensure some minimum values
        for tone in tones:
            tones[tone] = max(0.2, tones[tone])

        return tones
    except Exception as e:
        return DEFAULT_TONES


def analyze_content(website_content, social_content):
    """Analyze the content to extract keywords, tone, and values"""

    # Default values in case of failure
    defaults = {
        "keywords": DEFAULT_KEYWORDS,
        "tone_analysis": DEFAULT_TONES,
        "key_values": DEFAULT_KEY_VALUES,
        "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
    }

    try:
        # Extract content
        website_text = website_content.get("content", "")
        brand_name = website_content.get("brand_name", "")

        # Add social content
        social_texts = []
        for social in social_content:
            if "content" in social and social["content"]:
                social_texts.append(social["content"])

        # Combine all text
        all_text = website_text + " " + " ".join(social_texts)

        # If content is too short, use defaults
        if len(all_text) < 50:
            return defaults

        # Analyze sentiment
        sentiment = None
        if textblob_available:
            try:
                blob = TextBlob(all_text)
                sentiment = {
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity,
                }
            except Exception as e:
                sentiment = simple_sentiment_analysis(all_text)
        else:
            sentiment = simple_sentiment_analysis(all_text)

        # Tokenize text
        tokens = []
        if nltk_resources_available:
            try:
                # Use NLTK for tokenization
                tokens = word_tokenize(all_text.lower())

                # Remove stopwords and punctuation
                stop_words = set(stopwords.words("english"))
                tokens = [
                    word
                    for word in tokens
                    if word not in stop_words
                    and word not in string.punctuation
                    and len(word) > 2
                ]
            except Exception as e:
                tokens = simple_tokenize(all_text)
        else:
            tokens = simple_tokenize(all_text)

        # Extract keywords
        keywords = extract_keywords(tokens)

        # Extract key values
        key_values = extract_key_values(all_text, keywords)

        # Analyze tone
        tone_analysis = analyze_tone(sentiment)

        # Include brand name in key values if not already present
        if brand_name and len(brand_name.split()) == 1 and len(key_values) < 5:
            brand_value = f"{brand_name} Excellence"
            if brand_value not in key_values:
                key_values.append(brand_value)
                key_values = key_values[:5]  # Keep top 5

        # Return analysis results
        return {
            "keywords": keywords,
            "tone_analysis": tone_analysis,
            "key_values": key_values,
            "sentiment": sentiment,
        }

    except Exception as e:
        return defaults
