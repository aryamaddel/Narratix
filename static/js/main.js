document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const analyzeBtn = document.getElementById('analyzeBtn');
    const websiteUrl = document.getElementById('websiteUrl');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const progressBar = document.getElementById('progressBar');
    const resultSection = document.getElementById('resultSection');
    
    // Brand elements
    const brandName = document.getElementById('brandName');
    const brandDescription = document.getElementById('brandDescription');
    const keyValues = document.getElementById('keyValues');
    const socialLinks = document.getElementById('socialLinks');
    const brandStoryContent = document.getElementById('brandStoryContent');
    const toneAnalysis = document.getElementById('toneAnalysis');
    const keyKeywords = document.getElementById('keyKeywords');
    const colorPalette = document.getElementById('colorPalette');
    const typography = document.getElementById('typography');
    const imageStyle = document.getElementById('imageStyle');
    const socialAnalytics = document.getElementById('socialAnalytics');
    const consistencyScore = document.getElementById('consistencyScore');
    const scoreCircle = document.getElementById('scoreCircle');
    
    // Set up Markdown converter
    const converter = new showdown.Converter({
        tables: true,
        tasklists: true,
        strikethrough: true,
        emoji: true
    });
    
    // Handle analyze button click
    analyzeBtn.addEventListener('click', function() {
        const url = websiteUrl.value.trim();
        
        if (!url) {
            alert('Please enter a website URL');
            return;
        }
        
        // Show loading state
        analyzeBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        progressBar.classList.remove('d-none');
        
        // Update progress bar (simulated progress)
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += 5;
            progressBar.querySelector('.progress-bar').style.width = `${Math.min(progress, 95)}%`;
            
            if (progress >= 95) {
                clearInterval(progressInterval);
            }
        }, 500);
        
        // Send request to backend
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Complete progress bar
            progressBar.querySelector('.progress-bar').style.width = '100%';
            setTimeout(() => {
                progressBar.classList.add('d-none');
            }, 500);
            
            // Process and display results
            displayResults(data);
            
            // Reset loading state
            analyzeBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
            
            // Show results section
            resultSection.classList.remove('d-none');
            
            // Scroll to results
            resultSection.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error analyzing the website. Please try again.');
            
            // Reset loading state
            analyzeBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
            progressBar.classList.add('d-none');
        });
    });
    
    // Function to display results
    function displayResults(data) {
        // Display brand info
        brandName.textContent = data.brand_name;
        brandDescription.textContent = data.brand_description;
        
        // Display key values
        keyValues.innerHTML = '';
        data.key_values.forEach(value => {
            const badge = document.createElement('span');
            badge.className = 'value-badge';
            badge.textContent = value;
            keyValues.appendChild(badge);
        });
        
        // Display social links
        socialLinks.innerHTML = '';
        data.social_links.forEach(social => {
            const badge = document.createElement('a');
            badge.className = `social-badge ${social.platform}`;
            badge.href = social.url;
            badge.target = '_blank';
            
            const icon = document.createElement('i');
            
            // Set appropriate icon class based on platform
            if (social.platform === 'facebook') {
                icon.className = 'fab fa-facebook-f';
            } else if (social.platform === 'twitter') {
                icon.className = 'fab fa-twitter';
            } else if (social.platform === 'instagram') {
                icon.className = 'fab fa-instagram';
            } else if (social.platform === 'linkedin') {
                icon.className = 'fab fa-linkedin-in';
            } else if (social.platform === 'youtube') {
                icon.className = 'fab fa-youtube';
            } else if (social.platform === 'tiktok') {
                icon.className = 'fab fa-tiktok';
            } else if (social.platform === 'pinterest') {
                icon.className = 'fab fa-pinterest-p';
            } else if (social.platform === 'github') {
                icon.className = 'fab fa-github';
            } else if (social.platform === 'medium') {
                icon.className = 'fab fa-medium-m';
            } else {
                icon.className = 'fas fa-link';
            }
            
            badge.appendChild(icon);
            badge.appendChild(document.createTextNode(` ${social.platform.charAt(0).toUpperCase() + social.platform.slice(1)}`));
            socialLinks.appendChild(badge);
        });
        
        // If no social links found
        if (data.social_links.length === 0) {
            const noBadge = document.createElement('span');
            noBadge.className = 'social-badge';
            noBadge.innerHTML = '<i class="fas fa-info-circle"></i> No social media links detected';
            socialLinks.appendChild(noBadge);
        }
        
        // Display brand story (convert markdown to HTML)
        brandStoryContent.innerHTML = converter.makeHtml(data.brand_story);
        
        // Display tone analysis
        toneAnalysis.innerHTML = '';
        for (const tone of data.visual_profile.tone_indicators) {
            const toneContainer = document.createElement('div');
            toneContainer.className = 'mb-3';
            
            const toneBar = document.createElement('div');
            toneBar.className = 'tone-bar';
            toneBar.style.width = '100%';
            toneBar.style.backgroundColor = getColorForTone(tone.name.toLowerCase());
            
            // Inner bar showing percentage
            const innerBar = document.createElement('div');
            innerBar.style.width = `${tone.value * 100}%`;
            innerBar.style.height = '100%';
            innerBar.style.backgroundColor = getColorForTone(tone.name.toLowerCase());
            innerBar.style.borderRadius = '15px';
            
            const toneLabel = document.createElement('div');
            toneLabel.className = 'tone-label';
            toneLabel.textContent = tone.name;
            
            const toneValue = document.createElement('div');
            toneValue.className = 'tone-value';
            toneValue.textContent = `${Math.round(tone.value * 100)}%`;
            
            toneBar.appendChild(innerBar);
            toneBar.appendChild(toneLabel);
            toneBar.appendChild(toneValue);
            toneContainer.appendChild(toneBar);
            
            toneAnalysis.appendChild(toneContainer);
        }
        
        // Display keywords
        keyKeywords.innerHTML = '';
        data.keywords.forEach(keyword => {
            const badge = document.createElement('span');
            badge.className = 'keyword-badge';
            badge.textContent = keyword;
            keyKeywords.appendChild(badge);
        });
        
        // Display color palette
        colorPalette.innerHTML = '';
        const colors = data.visual_profile.color_palette;
        
        for (const [name, color] of Object.entries(colors)) {
            const colorContainer = document.createElement('div');
            colorContainer.className = 'd-inline-block me-3 mb-3 text-center';
            
            const swatch = document.createElement('div');
            swatch.className = 'color-swatch';
            swatch.style.backgroundColor = color;
            
            const colorName = document.createElement('small');
            colorName.textContent = `${name.charAt(0).toUpperCase() + name.slice(1)}: ${color}`;
            
            colorContainer.appendChild(swatch);
            colorContainer.appendChild(colorName);
            colorPalette.appendChild(colorContainer);
        }
        
        // Display typography
        typography.innerHTML = `
            <p><strong>Heading Font:</strong> ${data.visual_profile.font_style.heading}</p>
            <p><strong>Body Font:</strong> ${data.visual_profile.font_style.body}</p>
            <p><strong>Style Notes:</strong> ${data.visual_profile.font_style.style}</p>
        `;
        
        // Display image style
        imageStyle.textContent = data.visual_profile.image_style;
        
        // Display social analytics
        socialAnalytics.innerHTML = '';
        data.social_analytics.forEach(social => {
            const row = document.createElement('tr');
            
            const platformCell = document.createElement('td');
            platformCell.innerHTML = `<strong>${social.platform}</strong>`;
            
            const followersCell = document.createElement('td');
            followersCell.textContent = social.followers;
            
            const engagementCell = document.createElement('td');
            engagementCell.textContent = social.engagement;
            
            const frequencyCell = document.createElement('td');
            frequencyCell.textContent = social.frequency;
            
            row.appendChild(platformCell);
            row.appendChild(followersCell);
            row.appendChild(engagementCell);
            row.appendChild(frequencyCell);
            
            socialAnalytics.appendChild(row);
        });
        
        // Display consistency score
        consistencyScore.textContent = data.consistency_score;
        
        // Set score circle color
        if (data.consistency_score >= 85) {
            scoreCircle.className = 'score-circle excellent';
        } else if (data.consistency_score >= 70) {
            scoreCircle.className = 'score-circle good';
        } else if (data.consistency_score >= 50) {
            scoreCircle.className = 'score-circle average';
        } else {
            scoreCircle.className = 'score-circle needs-work';
        }
    }
    
    // Helper function to get color for tone
    function getColorForTone(tone) {
        const toneColors = {
            'professional': '#0A3D62',
            'friendly': '#5E8C61',
            'informative': '#3A6EA5',
            'enthusiastic': '#E63946',
            'formal': '#2D3142'
        };
        
        return toneColors[tone] || '#4361ee';
    }
});
