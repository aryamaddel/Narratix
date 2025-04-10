import os
import json

class StoryGenerator:
    def __init__(self):
        # We're using a template-based approach only
        pass
    
    def generate(self, website_content, social_media_content, analysis):
        """Generate a brand story based on the analyzed content"""
        # Extract company name
        company_name = self._extract_company_name(website_content, social_media_content)
        
        # Compile data for story generation
        story_input = self._prepare_story_input(company_name, website_content, social_media_content, analysis)
        
        # Generate the story using template-based approach
        return self._generate_template_story(story_input)
    
    def _extract_company_name(self, website_content, social_media_content):
        """Extract the company name from content"""
        # Try to get company name from website title
        for page in website_content:
            if 'content' in page and 'title' in page['content']:
                title = page['content']['title']
                if title:
                    # Take the first part of the title as it often contains the company name
                    return title.split('|')[0].split('-')[0].strip()
        
        # Try social media profiles
        for platform, data in social_media_content.items():
            profile = data.get('profile', {})
            if 'name' in profile:
                return profile['name']
        
        # Fallback
        return "The Company"
    
    def _prepare_story_input(self, company_name, website_content, social_media_content, analysis):
        """Prepare a structured input for the story generator"""
        # Extract company description
        description = ""
        for page in website_content:
            if 'content' in page and 'meta_description' in page['content']:
                description = page['content']['meta_description']
                break
        
        # Get key insights
        sentiment = analysis.get('sentiment', {}).get('overall', 'neutral')
        top_keywords = analysis.get('keywords', {}).get('list', [])[:10]
        topics = analysis.get('topics', [])
        tones = analysis.get('tone', [])
        values = analysis.get('values', [])
        
        # Get social presence
        social_presence = list(social_media_content.keys())
        
        # Extract highlights from social media
        highlights = []
        engagement_stories = []
        for platform, data in social_media_content.items():
            posts = data.get('posts', [])
            profile = data.get('profile', {})
            
            if posts:
                # Get the post with highest engagement as a highlight
                if platform == 'twitter':
                    best_post = max(posts, key=lambda x: x.get('likes', 0) + x.get('retweets', 0))
                    highlights.append({
                        'platform': platform,
                        'text': best_post.get('text', ''),
                        'engagement': f"{best_post.get('likes', 0)} likes, {best_post.get('retweets', 0)} retweets"
                    })
                    followers = profile.get('followers_count', 0)
                    if followers:
                        engagement_stories.append(f"On Twitter, they engage with a community of {followers:,} followers, sharing updates that resonate with their audience.")
                elif platform == 'facebook':
                    best_post = max(posts, key=lambda x: x.get('reactions', 0))
                    highlights.append({
                        'platform': platform,
                        'text': best_post.get('content', ''),
                        'engagement': f"{best_post.get('reactions', 0)} reactions"
                    })
                    followers = profile.get('followers_count', 0)
                    if followers:
                        engagement_stories.append(f"Their Facebook presence connects with {followers:,} followers who regularly engage with their content.")
                elif platform == 'instagram':
                    best_post = max(posts, key=lambda x: x.get('likes', 0))
                    highlights.append({
                        'platform': platform,
                        'text': best_post.get('caption', ''),
                        'engagement': f"{best_post.get('likes', 0)} likes"
                    })
                    followers = profile.get('followers_count', 0)
                    if followers:
                        engagement_stories.append(f"On Instagram, they've built a visual identity that appeals to their {followers:,} followers, showcasing their brand through compelling imagery.")
                elif platform == 'linkedin':
                    best_post = max(posts, key=lambda x: x.get('reactions', 0))
                    highlights.append({
                        'platform': platform,
                        'text': best_post.get('content', ''),
                        'engagement': f"{best_post.get('reactions', 0)} reactions"
                    })
                    followers = profile.get('followers_count', 0) or profile.get('connections', '0+')
                    engagement_stories.append(f"Their LinkedIn presence emphasizes their professional expertise and industry leadership to {followers} connections.")
        
        # Extract full text content for context
        full_text = ""
        for page in website_content:
            if 'content' in page and 'full_text' in page['content']:
                full_text += page['content']['full_text'] + " "
        
        return {
            "company_name": company_name,
            "description": description,
            "full_text": full_text,
            "sentiment": sentiment,
            "keywords": top_keywords,
            "topics": topics,
            "tones": tones,
            "values": values,
            "social_presence": social_presence,
            "highlights": highlights,
            "engagement_stories": engagement_stories
        }
    
    def _generate_template_story(self, story_input):
        """Generate a more descriptive template-based brand story"""
        company = story_input['company_name']
        values = story_input.get('values', [])
        values_str = ', '.join(values) if values else "innovation, quality, and customer satisfaction"
        tones = story_input.get('tones', [])
        tone_str = ', '.join(tones) if tones else "professional and engaging"
        social_platforms = story_input.get('social_presence', [])
        social_str = ', '.join(social_platforms) if social_platforms else "various social platforms"
        
        # Create a more detailed brand essence
        brand_essence = self._create_brand_essence(company, values, tones, story_input.get('keywords', []))
        
        # Create a mission statement
        mission = self._create_mission_statement(company, story_input.get('description', ''), story_input.get('full_text', ''))
        
        # Create detailed values and personality section
        values_personality = self._create_values_personality(company, values, tones, story_input.get('sentiment', 'neutral'))
        
        # Create target audience section
        target_audience = self._create_target_audience(company, story_input.get('keywords', []), story_input.get('topics', []))
        
        # Create messaging themes section
        messaging_themes = self._create_messaging_themes(company, story_input.get('topics', []), story_input.get('keywords', []))
        
        # Create brand voice section
        brand_voice = self._create_brand_voice(company, tones, story_input.get('sentiment', 'neutral'))
        
        # Create social media highlights section
        social_highlights = self._create_social_highlights(company, story_input.get('highlights', []), story_input.get('engagement_stories', []), social_platforms)
        
        # Combine all sections into the final story
        story = f"""# Brand Story: {company}

## Brand Essence
{brand_essence}

## Origin and Mission
{mission}

## Values and Personality
{values_personality}

## Target Audience
{target_audience}

## Key Messaging Themes
{messaging_themes}

## Brand Voice
{brand_voice}

## Social Media Presence
{social_highlights}

## Conclusion
{self._create_conclusion(company, values, tones)}
"""
        
        return story
    
    def _create_brand_essence(self, company, values, tones, keywords):
        """Create a detailed brand essence section"""
        if not values:
            values = ["innovation", "quality", "customer satisfaction"]
        
        if not tones:
            tones = ["professional", "engaging"]
        
        essence_adjectives = ["distinctive", "authentic", "compelling", "innovative"]
        adjective = essence_adjectives[hash(company) % len(essence_adjectives)]
        
        keywords_str = ""
        if keywords and len(keywords) >= 3:
            top_keywords = keywords[:3]
            keywords_str = f" Through their digital presence, they consistently emphasize {', '.join(top_keywords)}, which forms the core of their brand identity."
        
        return f"{company} is a {adjective} brand that embodies {', '.join(values)}. Their online presence conveys a {', '.join(tones)} tone that creates a meaningful connection with their audience.{keywords_str} The brand distinguishes itself by focusing on what matters most to their customers while staying true to their core values."
    
    def _create_mission_statement(self, company, description, full_text):
        """Create a more detailed mission statement"""
        if description:
            return f"{description}\n\nThis mission drives {company}'s approach to their products, services, and customer interactions, establishing them as a purpose-driven organization focused on delivering meaningful value to their stakeholders."
        
        # If no description available, create a generic one based on company name
        industry_terms = ["innovation", "solutions", "services", "products", "experiences"]
        industry_term = industry_terms[hash(company) % len(industry_terms)]
        
        return f"{company} appears to be dedicated to delivering exceptional {industry_term} to their customers. Their digital presence suggests a commitment to excellence and a focus on solving real-world challenges through their offerings.\n\nTheir mission seems centered around creating meaningful impact in their industry while maintaining the highest standards of quality and customer satisfaction."
    
    def _create_values_personality(self, company, values, tones, sentiment):
        """Create detailed values and personality section"""
        if not values:
            values = ["innovation", "quality", "customer satisfaction"]
        
        values_descriptions = {
            "innovation": f"Innovation is central to {company}'s identity, as they constantly seek new ways to improve their offerings and stay ahead of industry trends.",
            "quality": f"Quality remains non-negotiable for {company}, evident in their attention to detail and commitment to excellence in everything they do.",
            "customer satisfaction": f"{company} places customers at the heart of their business, focusing on creating experiences that delight and provide genuine value.",
            "integrity": f"Integrity forms the foundation of {company}'s operations, building trust with stakeholders through transparent and ethical business practices.",
            "sustainability": f"{company} demonstrates a commitment to sustainability, considering environmental impact alongside business objectives.",
            "community": f"Community engagement is important to {company}, as they seek to make positive contributions to the societies they operate in.",
            "diversity": f"{company} values diversity and inclusion, recognizing that different perspectives drive innovation and better business outcomes."
        }
        
        # Create value descriptions for each value
        value_paragraphs = []
        for value in values:
            if value in values_descriptions:
                value_paragraphs.append(values_descriptions[value])
            else:
                value_paragraphs.append(f"{value.capitalize()} is a core value that drives {company}'s approach to business and relationship-building.")
        
        values_text = "\n\n".join(value_paragraphs)
        
        # Create personality description
        personality_text = f"Their brand personality can be described as {', '.join(tones)}, which helps them connect authentically with their audience. "
        
        if sentiment == "positive":
            personality_text += f"The consistently positive tone in their communications creates an uplifting brand experience that resonates with their customers."
        elif sentiment == "neutral":
            personality_text += f"Their balanced, measured tone establishes credibility and trustworthiness in their communications."
        else:
            personality_text += f"Their communication approach establishes a distinct voice in their industry."
            
        return f"{values_text}\n\n{personality_text}"
    
    def _create_target_audience(self, company, keywords, topics):
        """Create detailed target audience section"""
        audience_attributes = []
        
        if keywords and len(keywords) >= 3:
            attributes = keywords[:3]
            audience_attributes = [a.replace('-', ' ') for a in attributes]
        else:
            audience_attributes = ["quality", "innovation", "reliability"]
        
        industry_focus = ""
        if topics:
            industry_focus = f" particularly in the {', '.join(topics)} sector(s),"
        
        return f"Based on their content and messaging, {company} appears to target individuals and organizations who value {', '.join(audience_attributes)}.{industry_focus} Their ideal customers likely appreciate thorough information and seek meaningful relationships with the brands they choose.\n\nTheir communication style suggests they connect best with an audience that values expertise and authenticity, looking for solutions that address specific needs rather than generic offerings."
    
    def _create_messaging_themes(self, company, topics, keywords):
        """Create detailed messaging themes section"""
        themes_intro = f"The recurring themes in {company}'s communication reveal their priorities and strengths:"
        
        # Use topics if available, otherwise use keywords
        themes = topics if topics else (keywords[:5] if keywords else ["Product excellence", "Customer satisfaction", "Industry expertise"])
        
        themes_content = ""
        for theme in themes:
            theme_title = theme.capitalize()
            themes_content += f"\n\n### {theme_title}\n"
            
            # Generate description based on theme
            if theme.lower() in ["technology", "innovation", "digital"]:
                themes_content += f"{company} positions themselves at the forefront of technological advancement, emphasizing how their solutions leverage cutting-edge capabilities to solve problems in new ways."
            elif theme.lower() in ["business", "enterprise", "industry"]:
                themes_content += f"A focus on business outcomes and enterprise solutions shows how {company} understands the complex challenges organizations face and provides targeted solutions to address them."
            elif theme.lower() in ["customer", "service", "support", "satisfaction"]:
                themes_content += f"Customer-centricity is evident throughout {company}'s messaging, highlighting their commitment to exceptional service and support that goes beyond the initial transaction."
            elif theme.lower() in ["quality", "excellence", "premium"]:
                themes_content += f"{company} consistently emphasizes the quality and reliability of their offerings, positioning themselves as a premium choice for discerning customers."
            else:
                themes_content += f"This theme appears consistently throughout {company}'s communications, underlining its importance to their brand identity and value proposition."
        
        return f"{themes_intro}{themes_content}"
    
    def _create_brand_voice(self, company, tones, sentiment):
        """Create detailed brand voice section"""
        voice_description = ""
        if "formal" in tones:
            voice_description = f"{company} employs a formal, authoritative voice that establishes expertise and credibility. Their communications are structured, precise, and professionally crafted, which helps build trust with their audience."
        elif "casual" in tones:
            voice_description = f"{company} uses a conversational, approachable voice that makes complex topics accessible. Their friendly tone creates a sense of connection while still maintaining professional credibility."
        
        if "enthusiastic" in tones:
            voice_description += f" Their enthusiasm shines through in their messaging, creating energy and excitement around their brand and offerings."
        
        if "professional" in tones:
            voice_description += f" The professional tone they maintain helps position {company} as a serious, reliable partner committed to delivering value."
        
        if not voice_description:
            tone_str = ', '.join(tones) if tones else "professional and engaging"
            voice_description = f"{company}'s brand voice can be characterized as {tone_str}, which helps them connect with their audience effectively."
        
        competitive_edge = f"\n\nThis distinctive voice helps {company} differentiate themselves in a crowded marketplace. By maintaining consistency in tone across platforms, they create a cohesive brand experience that customers can recognize and relate to, regardless of the touchpoint."
        
        return f"{voice_description}{competitive_edge}"
    
    def _create_social_highlights(self, company, highlights, engagement_stories, platforms):
        """Create detailed social media highlights section"""
        if not platforms:
            return f"{company} maintains a limited social media presence. Developing a more robust social strategy could help them connect with their audience and amplify their brand message."
        
        intro = f"{company} has established a presence across {len(platforms)} social media platforms, each serving a distinct purpose in their overall communication strategy:"
        
        platform_details = []
        
        # Add engagement stories
        for story in engagement_stories:
            platform_details.append(story)
        
        # Add specific highlight examples
        if highlights:
            intro += "\n\nSome notable highlights from their social presence include:"
            for highlight in highlights:
                platform = highlight.get('platform', '').capitalize()
                text = highlight.get('text', '')
                engagement = highlight.get('engagement', '')
                
                if text and platform:
                    platform_details.append(f"\n- **{platform}:** \"{text}\" ({engagement})")
        
        if not platform_details:
            for platform in platforms:
                platform_details.append(f"{platform.capitalize()} is used to share updates and connect with their audience.")
        
        details = "\n\n".join(platform_details)
        
        strategy_recommendation = f"\n\nTheir social media strategy demonstrates how {company} uses different platforms to highlight various aspects of their brand identity while maintaining a consistent overall message."
        
        return f"{intro}\n\n{details}{strategy_recommendation}"
    
    def _create_conclusion(self, company, values, tones):
        """Create a meaningful conclusion"""
        values_str = ', '.join(values) if values else "innovation, quality, and customer satisfaction"
        tone_str = ', '.join(tones) if tones else "professional and engaging"
        
        return f"{company}'s brand story reveals an organization with a clear sense of purpose and identity. Their commitment to {values_str} forms the foundation of their brand, while their {tone_str} voice creates meaningful connections with their audience.\n\nBy consistently communicating their key messages across digital channels, {company} has developed a cohesive brand image that resonates with their target audience. This strong foundation positions them well for continued growth and deeper customer engagement in the future."
