import os
from dotenv import load_dotenv
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Load .env file
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


class EnhancedMetaExtractor:
    def __init__(self):
        self.session = requests.Session()

    def extract_youtube_id(self, url):
        """
        Extract YouTube VIDEO_ID from standard, short, embed URLs.
        Returns None if not a valid YouTube video URL.
        """
        parsed = urlparse(url)
        if 'youtube' in parsed.netloc or 'youtu.be' in parsed.netloc:
            # Standard /watch?v=VIDEO_ID
            if parsed.path == '/watch':
                query = parse_qs(parsed.query)
                return query.get('v', [None])[0]
            # Short link youtu.be/VIDEO_ID
            elif parsed.netloc == 'youtu.be':
                return parsed.path.lstrip('/')
            # Embed link /embed/VIDEO_ID
            elif parsed.path.startswith('/embed/'):
                return parsed.path.split('/')[2]
        return None

    def fetch_youtube_metadata(self, video_id, api_key):
        api_url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={video_id}&key={api_key}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            if "items" in data and data["items"]:
                snippet = data["items"][0]["snippet"]
                statistics = data["items"][0].get("statistics", {})
                contentDetails = data["items"][0].get("contentDetails", {})
                return {
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                    "thumbnails": snippet.get("thumbnails", {}),
                    "channelTitle": snippet.get("channelTitle"),
                    "statistics": statistics,
                    "contentDetails": contentDetails,
                    "video_id": video_id
                }
        return {"error": "Video not found or API error"}

    def get_social_crawler_headers(self, platform='facebook'):
        base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        if platform == 'facebook':
            base_headers.update({
                'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
                'From': 'facebookexternalhit@facebook.com'
            })
        elif platform == 'twitter':
            base_headers.update({'User-Agent': 'Twitterbot/1.0'})
        elif platform == 'whatsapp':
            base_headers.update({'User-Agent': 'WhatsApp/2.23.24.70'})
        elif platform == 'bot':
            base_headers.update({'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
        
        return base_headers
    
    def fetch_meta_data(self, url):

        # Check if YouTube URL
        video_id = self.extract_youtube_id(url)
        if video_id:
            return self.fetch_youtube_metadata(video_id, YOUTUBE_API_KEY)

        platforms = ['whatsapp', 'facebook', 'twitter', 'bot']
        
        for platform in platforms:
            try:
                headers = self.get_social_crawler_headers(platform)
                response = requests.get(
                    url, headers=headers,
                    timeout=8, allow_redirects=True, verify=False
                )
                if response.status_code == 200:
                    return self.extract_meta_tags(response.text, url, platform)
            except Exception as e:
                print(f"Failed with {platform} crawler: {e}")
                continue
                
        return {"url": url, "error": "All crawler methods failed"}
    
    def extract_meta_tags(self, html, url, crawler_type):
        soup = BeautifulSoup(html, 'html.parser')
        
        meta_data = {
            'url': url,
            'crawler_used': crawler_type,
            'title': '',
            'description': '',
            'og_tags': {},
            'twitter_tags': {},
            'favicons': []
        }
        
        title_tag = soup.find('title')
        if title_tag:
            meta_data['title'] = title_tag.get_text().strip()
        
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            prop = meta.get('property', '').lower()
            content = meta.get('content', '').strip() if meta.get('content') else ''
            
            if not content:
                continue
                
            if name == 'description':
                meta_data['description'] = content
            elif prop.startswith('og:'):
                meta_data['og_tags'][prop.replace('og:', '')] = content
            elif name.startswith('twitter:'):
                meta_data['twitter_tags'][name.replace('twitter:', '')] = content
        
        for link in soup.find_all('link', rel=lambda r: r and 'icon' in r.lower()):
            href = link.get('href')
            if href:
                meta_data['favicons'].append(urljoin(url, href))

        return meta_data
