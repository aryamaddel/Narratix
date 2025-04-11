document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const analyzeBtn = document.getElementById('analyzeBtn');
    const websiteUrl = document.getElementById('websiteUrl');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const progressBar = document.getElementById('progressBar');
    const progressBarFill = progressBar.querySelector('div');
    const resultSection = document.getElementById('resultSection');
    
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Deactivate all tabs
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.classList.remove('border-primary');
                btn.classList.add('border-transparent', 'text-gray-400');
            });
            
            // Activate clicked tab
            this.classList.add('active', 'border-primary');
            this.classList.remove('border-transparent', 'text-gray-400');
            
            // Hide all content
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.add('hidden');
                pane.classList.remove('active');
            });
            
            // Show selected content
            const targetId = this.getAttribute('data-tab');
            const targetPane = document.getElementById(targetId);
            targetPane.classList.remove('hidden');
            targetPane.classList.add('active');
        });
    });
    
    // Set up Markdown converter
    const converter = new showdown.Converter({
        tables: true,
        tasklists: true,
        strikethrough: true,
        simpleLineBreaks: true
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
        loadingSpinner.classList.remove('hidden');
        progressBar.classList.remove('hidden');
        
        // Update progress bar
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += 8;
            progressBarFill.style.width = `${Math.min(progress, 95)}%`;
            
            if (progress >= 95) {
                clearInterval(progressInterval);
            }
        }, 300);
        
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
            progressBarFill.style.width = '100%';
            setTimeout(() => {
                progressBar.classList.add('hidden');
            }, 500);
            
            // Process and display results
            displayResults(data);
            
            // Reset loading state
            analyzeBtn.disabled = false;
            loadingSpinner.classList.add('hidden');
            
            // Show results section
            resultSection.classList.remove('hidden');
            
            // Scroll to results
            resultSection.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error analyzing the website. Please try again.');
            
            // Reset loading state
            analyzeBtn.disabled = false;
            loadingSpinner.classList.add('hidden');
            progressBar.classList.add('hidden');
        });
    });
    
    // Function to display results
    function displayResults(data) {
        // Brand info
        document.getElementById('brandName').textContent = data.brand_name || 'Brand Name';
        document.getElementById('brandDescription').textContent = data.brand_description || 'No description available.';
        
        // Consistency score
        const score = data.consistency_score || 75;
        document.getElementById('consistencyScore').textContent = score;
        
        // Set score color
        const scoreCircle = document.getElementById('scoreCircle');
        
        if (score >= 85) {
            scoreCircle.className = 'w-20 h-20 rounded-full border-4 border-cyan-500 flex items-center justify-center mx-auto';
        } else if (score >= 70) {
            scoreCircle.className = 'w-20 h-20 rounded-full border-4 border-teal-500 flex items-center justify-center mx-auto';
        } else if (score >= 50) {
            scoreCircle.className = 'w-20 h-20 rounded-full border-4 border-yellow-500 flex items-center justify-center mx-auto';
        } else {
            scoreCircle.className = 'w-20 h-20 rounded-full border-4 border-red-500 flex items-center justify-center mx-auto';
        }
        
        // Key values
        const keyValues = document.getElementById('keyValues');
        keyValues.innerHTML = '';
        
        if (data.key_values && data.key_values.length > 0) {
            data.key_values.forEach(value => {
                const badge = document.createElement('span');
                badge.className = 'bg-opacity-20 bg-primary text-white px-3 py-1 rounded-full text-sm';
                badge.textContent = value;
                keyValues.appendChild(badge);
            });
        } else {
            keyValues.innerHTML = '<span class="text-gray-500">No key values available</span>';
        }
        
        // Social links
        const socialLinks = document.getElementById('socialLinks');
        socialLinks.innerHTML = '';
        
        if (data.social_links && data.social_links.length > 0) {
            data.social_links.forEach(social => {
                const badge = document.createElement('a');
                badge.href = social.url;
                badge.target = '_blank';
                badge.className = `social-badge flex items-center bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 rounded-full text-sm transition ${social.platform}`;
                
                const icon = document.createElement('i');
                
                // Set icon class based on platform
                switch(social.platform) {
                    case 'facebook': icon.className = 'fab fa-facebook-f mr-2'; break;
                    case 'twitter': icon.className = 'fab fa-twitter mr-2'; break;
                    case 'instagram': icon.className = 'fab fa-instagram mr-2'; break;
                    case 'linkedin': icon.className = 'fab fa-linkedin-in mr-2'; break;
                    case 'youtube': icon.className = 'fab fa-youtube mr-2'; break;
                    case 'tiktok': icon.className = 'fab fa-tiktok mr-2'; break;
                    case 'pinterest': icon.className = 'fab fa-pinterest-p mr-2'; break;
                    default: icon.className = 'fas fa-link mr-2';
                }
                
                badge.appendChild(icon);
                badge.appendChild(document.createTextNode(social.platform));
                socialLinks.appendChild(badge);
            });
        } else {
            socialLinks.innerHTML = '<span class="text-gray-500">No social media links detected</span>';
        }
        
        // Brand story content - Fix markdown rendering
        const brandStoryContent = document.getElementById('brandStoryContent');
        
        if (data.brand_story) {
            // Clean up markdown before rendering
            let cleanMarkdown = data.brand_story
                .replace(/\\n/g, '\n')
                .replace(/\n{3,}/g, '\n\n');
            
            // Convert markdown to HTML
            brandStoryContent.innerHTML = converter.makeHtml(cleanMarkdown);
            
            // Fix any links to open in new tab
            brandStoryContent.querySelectorAll('a').forEach(link => {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener');
            });
        } else {
            brandStoryContent.innerHTML = '<p class="text-gray-500">No brand story available.</p>';
        }
        
        // Keywords
        const keyKeywords = document.getElementById('keyKeywords');
        keyKeywords.innerHTML = '';
        
        if (data.keywords && data.keywords.length > 0) {
            data.keywords.forEach(keyword => {
                const badge = document.createElement('span');
                badge.className = 'bg-gray-800 text-white px-3 py-1 rounded-full text-sm';
                badge.textContent = keyword;
                keyKeywords.appendChild(badge);
            });
        } else {
            keyKeywords.innerHTML = '<span class="text-gray-500">No keywords available</span>';
        }
        
        // Tone analysis
        const toneAnalysis = document.getElementById('toneAnalysis');
        toneAnalysis.innerHTML = '';
        
        if (data.visual_profile && data.visual_profile.tone_indicators) {
            data.visual_profile.tone_indicators.forEach(tone => {
                const container = document.createElement('div');
                container.className = 'mb-3';
                
                const labelContainer = document.createElement('div');
                labelContainer.className = 'flex justify-between text-sm mb-1';
                
                const nameLabel = document.createElement('span');
                nameLabel.textContent = tone.name;
                
                const valueLabel = document.createElement('span');
                valueLabel.textContent = `${Math.round(tone.value * 100)}%`;
                
                labelContainer.appendChild(nameLabel);
                labelContainer.appendChild(valueLabel);
                
                const toneBar = document.createElement('div');
                toneBar.className = 'tone-bar';
                
                const fillBar = document.createElement('div');
                fillBar.className = 'tone-bar-fill';
                fillBar.style.width = `${tone.value * 100}%`;
                
                toneBar.appendChild(fillBar);
                
                container.appendChild(labelContainer);
                container.appendChild(toneBar);
                toneAnalysis.appendChild(container);
            });
        } else {
            toneAnalysis.innerHTML = '<p class="text-gray-500">No tone analysis available</p>';
        }
        
        // Color palette
        const colorPalette = document.getElementById('colorPalette');
        colorPalette.innerHTML = '';
        
        if (data.visual_profile && data.visual_profile.color_palette) {
            const colors = data.visual_profile.color_palette;
            
            for (const [name, color] of Object.entries(colors)) {
                const colorContainer = document.createElement('div');
                colorContainer.className = 'text-center';
                
                const swatch = document.createElement('div');
                swatch.className = 'w-8 h-8 rounded';
                swatch.style.backgroundColor = color;
                swatch.style.border = '1px solid rgba(255,255,255,0.2)';
                
                const colorName = document.createElement('div');
                colorName.className = 'text-xs mt-1';
                colorName.textContent = `${name}: ${color}`;
                
                colorContainer.appendChild(swatch);
                colorContainer.appendChild(colorName);
                colorPalette.appendChild(colorContainer);
            }
        } else {
            colorPalette.innerHTML = '<p class="text-gray-500">No color palette available</p>';
        }
        
        // Typography
        const typography = document.getElementById('typography');
        
        if (data.visual_profile && data.visual_profile.font_style) {
            const fontStyle = data.visual_profile.font_style;
            typography.innerHTML = `
                <p class="mb-2"><strong>Heading Font:</strong> ${fontStyle.heading}</p>
                <p><strong>Body Font:</strong> ${fontStyle.body}</p>
            `;
        } else {
            typography.innerHTML = '<p class="text-gray-500">No typography information available</p>';
        }
        
        // Image style
        const imageStyle = document.getElementById('imageStyle');
        
        if (data.visual_profile && data.visual_profile.image_style) {
            imageStyle.textContent = data.visual_profile.image_style;
            imageStyle.className = '';
        } else {
            imageStyle.textContent = 'No image style recommendations available';
            imageStyle.className = 'text-gray-500';
        }
        
        // Social analytics
        const socialAnalytics = document.getElementById('socialAnalytics');
        socialAnalytics.innerHTML = '';
        
        if (data.social_analytics && data.social_analytics.length > 0) {
            data.social_analytics.forEach((social, index) => {
                const row = document.createElement('tr');
                row.className = index % 2 === 0 ? 'bg-gray-800' : '';
                
                const platformCell = document.createElement('td');
                platformCell.className = 'py-3 px-4';
                platformCell.innerHTML = `<strong>${social.platform}</strong>`;
                
                const followersCell = document.createElement('td');
                followersCell.className = 'py-3 px-4';
                followersCell.textContent = social.followers || 'N/A';
                
                const engagementCell = document.createElement('td');
                engagementCell.className = 'py-3 px-4';
                engagementCell.textContent = social.engagement || 'N/A';
                
                const frequencyCell = document.createElement('td');
                frequencyCell.className = 'py-3 px-4';
                frequencyCell.textContent = social.frequency || 'N/A';
                
                row.appendChild(platformCell);
                row.appendChild(followersCell);
                row.appendChild(engagementCell);
                row.appendChild(frequencyCell);
                
                socialAnalytics.appendChild(row);
            });
        } else {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 4;
            cell.className = 'py-3 px-4 text-center text-gray-500';
            cell.textContent = 'No social analytics available.';
            row.appendChild(cell);
            socialAnalytics.appendChild(row);
        }
    }
});
