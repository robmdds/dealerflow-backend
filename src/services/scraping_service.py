"""
Website Scraping Service for DealerFlow Pro
Automatically scrapes vehicle images from dealership websites
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
from services.image_service import ImageService
from models.image import Image
from extensions import db
import json
from datetime import datetime, timedelta

class ScrapingService:
    
    def __init__(self):
        self.image_service = ImageService()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def detect_website_platform(self, url):
        """Detect the platform/CMS used by the dealership website"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Common dealership website platforms
            platforms = {
                'autotrader': ['autotrader', 'at-inventory'],
                'cars.com': ['cars.com', 'cars-inventory'],
                'dealerfire': ['dealerfire', 'df-inventory'],
                'dealersocket': ['dealersocket', 'ds-inventory'],
                'autorevolution': ['autorevolution', 'ar-inventory'],
                'cobalt': ['cobalt', 'cobalt-inventory'],
                'dealer.com': ['dealer.com', 'ddc-inventory'],
                'wordpress': ['wp-content', 'wordpress'],
                'custom': []
            }
            
            for platform, indicators in platforms.items():
                if any(indicator in content for indicator in indicators):
                    return platform
            
            return 'custom'
            
        except Exception as e:
            return 'unknown'
    
    def find_inventory_pages(self, base_url):
        """Find inventory/vehicle listing pages on the website"""
        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common inventory page patterns
            inventory_patterns = [
                r'inventory',
                r'vehicles',
                r'cars',
                r'used',
                r'new',
                r'pre-owned',
                r'search'
            ]
            
            inventory_urls = set()
            
            # Find links that match inventory patterns
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                for pattern in inventory_patterns:
                    if re.search(pattern, href.lower()) or re.search(pattern, text):
                        full_url = urljoin(base_url, href)
                        inventory_urls.add(full_url)
            
            return list(inventory_urls)
            
        except Exception as e:
            return []
    
    def scrape_vehicle_listings(self, inventory_url):
        """Scrape vehicle listings from an inventory page"""
        try:
            response = self.session.get(inventory_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            vehicles = []
            
            # Common vehicle listing selectors
            vehicle_selectors = [
                '.vehicle-item',
                '.car-item',
                '.inventory-item',
                '.vehicle-card',
                '.listing-item',
                '[data-vehicle]',
                '.vehicle'
            ]
            
            vehicle_elements = []
            for selector in vehicle_selectors:
                elements = soup.select(selector)
                if elements:
                    vehicle_elements = elements
                    break
            
            for element in vehicle_elements:
                try:
                    vehicle_data = self._extract_vehicle_data(element, inventory_url)
                    if vehicle_data:
                        vehicles.append(vehicle_data)
                except Exception as e:
                    continue
            
            return vehicles
            
        except Exception as e:
            return []
    
    def _extract_vehicle_data(self, element, base_url):
        """Extract vehicle data from a listing element"""
        try:
            vehicle_data = {
                'images': [],
                'year': None,
                'make': None,
                'model': None,
                'price': None,
                'mileage': None,
                'stock_number': None,
                'detail_url': None
            }
            
            # Extract images
            img_tags = element.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src:
                    full_url = urljoin(base_url, src)
                    # Filter out non-vehicle images
                    if self._is_vehicle_image(src, img.get('alt', '')):
                        vehicle_data['images'].append(full_url)
            
            # Extract text content
            text_content = element.get_text()
            
            # Extract year (4 digits)
            year_match = re.search(r'\b(19|20)\d{2}\b', text_content)
            if year_match:
                vehicle_data['year'] = year_match.group()
            
            # Extract price
            price_match = re.search(r'\$[\d,]+', text_content)
            if price_match:
                vehicle_data['price'] = price_match.group().replace('$', '').replace(',', '')
            
            # Extract mileage
            mileage_match = re.search(r'([\d,]+)\s*(miles?|mi)', text_content, re.IGNORECASE)
            if mileage_match:
                vehicle_data['mileage'] = mileage_match.group(1).replace(',', '')
            
            # Extract make and model (this is more complex and may need customization)
            vehicle_data.update(self._extract_make_model(text_content))
            
            # Extract detail URL
            detail_link = element.find('a', href=True)
            if detail_link:
                vehicle_data['detail_url'] = urljoin(base_url, detail_link['href'])
            
            # Only return if we have at least year and images
            if vehicle_data['year'] and vehicle_data['images']:
                return vehicle_data
            
            return None
            
        except Exception as e:
            return None
    
    def _is_vehicle_image(self, src, alt_text):
        """Determine if an image is likely a vehicle image"""
        # Filter out common non-vehicle images
        exclude_patterns = [
            'logo', 'icon', 'banner', 'header', 'footer',
            'nav', 'menu', 'button', 'arrow', 'star',
            'social', 'facebook', 'twitter', 'instagram'
        ]
        
        src_lower = src.lower()
        alt_lower = alt_text.lower()
        
        for pattern in exclude_patterns:
            if pattern in src_lower or pattern in alt_lower:
                return False
        
        # Look for vehicle-related keywords
        vehicle_patterns = [
            'vehicle', 'car', 'auto', 'truck', 'suv',
            'sedan', 'coupe', 'hatchback', 'wagon'
        ]
        
        for pattern in vehicle_patterns:
            if pattern in src_lower or pattern in alt_lower:
                return True
        
        # If no specific indicators, assume it's a vehicle image
        # (better to include too many than miss vehicle images)
        return True
    
    def _extract_make_model(self, text_content):
        """Extract vehicle make and model from text"""
        # Common automotive makes
        makes = [
            'toyota', 'honda', 'ford', 'chevrolet', 'nissan',
            'hyundai', 'kia', 'volkswagen', 'bmw', 'mercedes',
            'audi', 'lexus', 'acura', 'infiniti', 'mazda',
            'subaru', 'mitsubishi', 'jeep', 'ram', 'dodge',
            'chrysler', 'buick', 'gmc', 'cadillac', 'lincoln',
            'volvo', 'jaguar', 'land rover', 'porsche', 'tesla'
        ]
        
        text_lower = text_content.lower()
        
        for make in makes:
            if make in text_lower:
                # Try to extract model (word after make)
                pattern = rf'\b{make}\s+(\w+)'
                match = re.search(pattern, text_lower)
                if match:
                    return {
                        'make': make.title(),
                        'model': match.group(1).title()
                    }
                else:
                    return {'make': make.title(), 'model': None}
        
        return {'make': None, 'model': None}
    
    def scrape_dealership_website(self, dealership_id, website_url, max_vehicles=50):
        """Scrape entire dealership website for vehicle images"""
        try:
            scraped_count = 0
            error_count = 0
            errors = []
            
            # Detect website platform
            platform = self.detect_website_platform(website_url)
            
            # Find inventory pages
            inventory_urls = self.find_inventory_pages(website_url)
            
            if not inventory_urls:
                inventory_urls = [website_url]  # Fallback to main URL
            
            for inventory_url in inventory_urls[:5]:  # Limit to 5 pages
                try:
                    # Scrape vehicle listings
                    vehicles = self.scrape_vehicle_listings(inventory_url)
                    
                    for vehicle in vehicles[:max_vehicles]:
                        try:
                            # Download and save images for each vehicle
                            vehicle_scraped, vehicle_errors = self._save_scraped_vehicle_images(
                                vehicle, dealership_id, website_url
                            )
                            scraped_count += vehicle_scraped
                            error_count += len(vehicle_errors)
                            errors.extend(vehicle_errors)
                            
                            # Rate limiting
                            time.sleep(1)
                            
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Vehicle processing error: {str(e)}")
                    
                    # Rate limiting between pages
                    time.sleep(2)
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Page scraping error for {inventory_url}: {str(e)}")
            
            return scraped_count, error_count, errors, platform
            
        except Exception as e:
            return 0, 1, [f"Website scraping error: {str(e)}"], 'unknown'
    
    def _save_scraped_vehicle_images(self, vehicle_data, dealership_id, source_url):
        """Save scraped vehicle images"""
        saved_count = 0
        errors = []
        
        try:
            for i, image_url in enumerate(vehicle_data['images'][:5]):  # Limit to 5 images per vehicle
                try:
                    # Download image
                    response = self.session.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    # Create file-like object
                    from io import BytesIO
                    image_file = BytesIO(response.content)
                    
                    # Generate filename
                    url_parts = urlparse(image_url)
                    original_filename = url_parts.path.split('/')[-1] or f'scraped_image_{i+1}.jpg'
                    image_file.name = original_filename
                    
                    # Prepare vehicle metadata
                    vehicle_metadata = {
                        'year': vehicle_data.get('year'),
                        'make': vehicle_data.get('make'),
                        'model': vehicle_data.get('model'),
                        'stock_number': vehicle_data.get('stock_number'),
                        'alt_text': f"Scraped {vehicle_data.get('year', '')} {vehicle_data.get('make', '')} {vehicle_data.get('model', '')}".strip(),
                        'tags': ['scraped', 'website'] + ([vehicle_data['make'].lower()] if vehicle_data.get('make') else [])
                    }
                    
                    # Save image
                    image_record, save_message = self.image_service.save_image(
                        image_file, dealership_id, vehicle_metadata, 'scraping'
                    )
                    
                    if image_record:
                        # Update with scraping-specific data
                        image_record.source_url = image_url
                        if i == 0:  # Set first image as primary
                            image_record.is_primary = True
                        db.session.commit()
                        
                        saved_count += 1
                    else:
                        errors.append(f"Image {i+1}: {save_message}")
                        
                except Exception as e:
                    errors.append(f"Image {i+1} from {image_url}: {str(e)}")
            
        except Exception as e:
            errors.append(f"Vehicle image processing error: {str(e)}")
        
        return saved_count, errors
    
    def schedule_website_scraping(self, dealership_id, website_url, scrape_frequency='weekly'):
        """Schedule automatic website scraping"""
        try:
            scrape_config = {
                'dealership_id': dealership_id,
                'website_url': website_url,
                'scrape_frequency': scrape_frequency,
                'last_scrape': None,
                'next_scrape': self._calculate_next_scrape(scrape_frequency),
                'is_active': True,
                'max_vehicles': 50
            }
            
            # In a real implementation, this would be stored in a database
            # and processed by a background task scheduler
            
            return True, f"Website scraping scheduled for {scrape_frequency} frequency"
            
        except Exception as e:
            return False, f"Failed to schedule website scraping: {str(e)}"
    
    def _calculate_next_scrape(self, frequency):
        """Calculate next scrape time based on frequency"""
        now = datetime.utcnow()
        
        if frequency == 'daily':
            return now + timedelta(days=1)
        elif frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif frequency == 'monthly':
            return now + timedelta(days=30)
        else:
            return now + timedelta(weeks=1)  # Default to weekly
    
    def get_scraping_status(self, dealership_id):
        """Get website scraping status"""
        try:
            # This would query the database for scraping status
            # For demo purposes, return sample status
            
            return {
                'is_configured': True,
                'website_url': 'https://example-dealership.com',
                'platform_detected': 'dealerfire',
                'last_scrape': '2025-07-12T18:00:00Z',
                'next_scrape': '2025-07-19T18:00:00Z',
                'scrape_frequency': 'weekly',
                'total_scraped': 89,
                'last_scrape_results': {
                    'vehicles_found': 23,
                    'images_scraped': 89,
                    'errors': 3
                },
                'is_active': True
            }
            
        except Exception as e:
            return {
                'is_configured': False,
                'error': str(e)
            }

