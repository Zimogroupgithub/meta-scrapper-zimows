#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class EnhancedMetaExtractor:
    def __init__(self):
        self.session = requests.Session()
        
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
        
        return base_headers
    
    def fetch_meta_data(self, url):
        platforms = ['whatsapp', 'facebook', 'twitter']
        
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
