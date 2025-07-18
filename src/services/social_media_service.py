"""
Social Media Service for DealerFlow Pro
Handles content generation and posting automation with image integration
"""

import openai
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from services.image_service import ImageService

class SocialMediaService:
    """
    Social Media Service that provides both simulation and real API integration
    For MVP/Demo: Uses simulation mode
    For Production: Can be switched to real API mode
    """
    
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        self.image_service = ImageService()
        
        # Set up OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        
        self.platforms = {
            'facebook': {
                'name': 'Facebook',
                'icon': 'fab fa-facebook',
                'color': '#1877f2',
                'max_chars': 63206,
                'supports_images': True,
                'supports_video': True,
                'hashtag_limit': 30
            },
            'instagram': {
                'name': 'Instagram',
                'icon': 'fab fa-instagram',
                'color': '#E4405F',
                'max_chars': 2200,
                'supports_images': True,
                'supports_video': True,
                'hashtag_limit': 30
            },
            'tiktok': {
                'name': 'TikTok',
                'icon': 'fab fa-tiktok',
                'color': '#000000',
                'max_chars': 300,
                'supports_images': False,
                'supports_video': True,
                'hashtag_limit': 100
            },
            'reddit': {
                'name': 'Reddit',
                'icon': 'fab fa-reddit',
                'color': '#FF4500',
                'max_chars': 40000,
                'supports_images': True,
                'supports_video': True,
                'hashtag_limit': 0
            },
            'x': {
                'name': 'X (Twitter)',
                'icon': 'fab fa-x-twitter',
                'color': '#000000',
                'max_chars': 280,
                'supports_images': True,
                'supports_video': True,
                'hashtag_limit': 10
            },
            'youtube': {
                'name': 'YouTube',
                'icon': 'fab fa-youtube',
                'color': '#FF0000',
                'max_chars': 5000,
                'supports_images': True,
                'supports_video': True,
                'hashtag_limit': 15,
                'content_type': 'video_description'
            }
        }
    
    def _real_content_generation(self, vehicle_data, platform, content_type, keywords=None):
        """Generate content using OpenAI API"""
        try:
            # Get vehicle images if available
            vehicle_images = self.image_service.get_vehicle_images(
                vehicle_data.get('dealership_id', 1), 
                vehicle_data
            )
            primary_image = self.image_service.get_primary_vehicle_image(
                vehicle_data.get('dealership_id', 1), 
                vehicle_data
            )
            
            platform_info = self.platforms.get(platform, {})
            max_chars = platform_info.get('max_chars', 280)
            supports_images = platform_info.get('supports_images', True)
            hashtag_limit = platform_info.get('hashtag_limit', 10)
            
            # Build optional keyword context
            keyword_context = ""
            if keywords:
                if isinstance(keywords, str) and keywords.strip():
                    keyword_context = f"\nKeywords to incorporate (if relevant): {keywords.strip()}"
                elif isinstance(keywords, list) and keywords:
                    keyword_context = f"\nKeywords to incorporate (if relevant): {', '.join([k.strip() for k in keywords if k.strip()])}"
            
            # Create prompt based on content type and platform
            if platform == 'youtube':
                # YouTube-specific content generation
                if content_type == 'vehicle_showcase':
                    prompt = f"""Create a YouTube video description for a {vehicle_data.get('year', '')} {vehicle_data.get('make', '')} {vehicle_data.get('model', '')} showcase at an automotive dealership.

Vehicle Details:
- Year: {vehicle_data.get('year', 'N/A')}
- Make: {vehicle_data.get('make', 'N/A')}
- Model: {vehicle_data.get('model', 'N/A')}
- Price: {vehicle_data.get('price', 'Contact for pricing')}
- Features: {', '.join(vehicle_data.get('features', []))}
- Mileage: {vehicle_data.get('mileage', 'N/A')}{keyword_context}

Create a compelling YouTube video description that includes:
1. Engaging title suggestion (first line)
2. Detailed description highlighting key features
3. Call to action for viewers to visit the dealership
4. Relevant hashtags (max {hashtag_limit})
5. Contact information encouragement

Max characters: {max_chars}
Make it engaging for YouTube's algorithm and viewers."""

                elif content_type == 'promotional':
                    prompt = f"""Create a YouTube video description for a promotional automotive dealership video.

Focus on:
- Special offers or financing deals
- Limited time promotions
- Strong call to action
- Urgency and excitement{keyword_context}

Create content that includes:
1. Catchy title suggestion (first line)
2. Promotional details and benefits
3. Clear call to action
4. Relevant hashtags (max {hashtag_limit})
5. Contact information

Max characters: {max_chars}
Make it compelling for YouTube viewers and algorithm."""

                else:  # general dealership content
                    prompt = f"""Create a YouTube video description for general automotive dealership content.

Content should include:
1. Engaging title suggestion (first line)
2. Professional dealership introduction
3. Services and expertise highlights
4. Call to action for viewers
5. Relevant hashtags (max {hashtag_limit}){keyword_context}

Max characters: {max_chars}
Build brand awareness and trust with potential customers."""

            elif content_type == 'vehicle_showcase':
                prompt = f"""Create an engaging {platform} post for a {vehicle_data.get('year', '')} {vehicle_data.get('make', '')} {vehicle_data.get('model', '')} at an automotive dealership.

Vehicle Details:
- Year: {vehicle_data.get('year', 'N/A')}
- Make: {vehicle_data.get('make', 'N/A')}
- Model: {vehicle_data.get('model', 'N/A')}
- Price: {vehicle_data.get('price', 'Contact for pricing')}
- Features: {', '.join(vehicle_data.get('features', []))}
- Mileage: {vehicle_data.get('mileage', 'N/A')}{keyword_context}

Platform: {platform}
Max characters: {max_chars}
{"Include relevant hashtags (max " + str(hashtag_limit) + ")" if hashtag_limit > 0 else "No hashtags needed"}
{"Images available: " + str(len(vehicle_images)) + " images" if vehicle_images else "No images available"}

Create compelling copy that highlights the vehicle's best features and encourages engagement. Use emojis appropriately for the platform."""

            elif content_type == 'promotional':
                prompt = f"""Create a promotional {platform} post for an automotive dealership.

Focus on:
- Special offers or financing
- Limited time deals
- Call to action
- Urgency and excitement{keyword_context}

Platform: {platform}
Max characters: {max_chars}
{"Include relevant hashtags (max " + str(hashtag_limit) + ")" if hashtag_limit > 0 else "No hashtags needed"}

Make it engaging and action-oriented with appropriate emojis."""

            else:  # general dealership content
                prompt = f"""Create a general {platform} post for an automotive dealership.

Content should be:
- Engaging and professional
- Relevant to car buyers
- Include call to action
- Build brand awareness{keyword_context}

Platform: {platform}
Max characters: {max_chars}
{"Include relevant hashtags (max " + str(hashtag_limit) + ")" if hashtag_limit > 0 else "No hashtags needed"}

Use appropriate emojis and tone for the platform."""

            # Generate content using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert social media manager for automotive dealerships. Create engaging, professional content that drives sales and engagement."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            # Prepare response with image information
            content_data = {
                'content': generated_content,
                'platform': platform,
                'content_type': content_type,
                'character_count': len(generated_content),
                'max_characters': max_chars,
                'supports_images': supports_images,
                'images_available': len(vehicle_images) if vehicle_images else 0,
                'primary_image': primary_image.to_dict() if primary_image else None,
                'all_images': [img.to_dict() for img in vehicle_images] if vehicle_images else [],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return content_data
            
        except Exception as e:
            # Fallback to simulation if OpenAI fails
            return self._simulate_content_generation(vehicle_data, platform, content_type)
    
    def _simulate_content_generation(self, vehicle_data, platform, content_type):
        """Simulate content generation for demo purposes"""
        # Get vehicle images if available
        vehicle_images = []
        primary_image = None
        
        try:
            vehicle_images = self.image_service.get_vehicle_images(
                vehicle_data.get('dealership_id', 1), 
                vehicle_data
            )
            primary_image = self.image_service.get_primary_vehicle_image(
                vehicle_data.get('dealership_id', 1), 
                vehicle_data
            )
        except:
            pass  # Continue without images if service fails
        
        platform_info = self.platforms.get(platform, {})
        
        # Simulate different content based on type and platform
        if content_type == 'vehicle_showcase':
            if platform == 'instagram':
                content = f"🚗 {vehicle_data.get('year', '2023')} {vehicle_data.get('make', 'Honda')} {vehicle_data.get('model', 'Civic')} - Now Available! ✨\n\nFeatures: {' | '.join(vehicle_data.get('features', ['Low Mileage', 'Clean Title', 'Great Condition']))}\n💰 Price: {vehicle_data.get('price', '$22,995')}\n📍 Visit us today!\n\n#cars #auto #automotive #cardealer #{vehicle_data.get('make', 'honda').lower()}"
            elif platform == 'facebook':
                content = f"🎉 FEATURED VEHICLE ALERT! 🎉\n\n{vehicle_data.get('year', '2023')} {vehicle_data.get('make', 'Honda')} {vehicle_data.get('model', 'Civic')}\n{vehicle_data.get('mileage', '15,000')} miles | {vehicle_data.get('price', '$22,995')}\n\n✅ {' | '.join(vehicle_data.get('features', ['Low Mileage', 'Clean Title', 'Great Condition']))}\n\nDon't miss out! Contact us today for more details.\n\n#cars #auto #cardealer"
            elif platform == 'x':
                content = f"🚗 {vehicle_data.get('year', '2023')} {vehicle_data.get('make', 'Honda')} {vehicle_data.get('model', 'Civic')} - {vehicle_data.get('price', '$22,995')} 🔥\n\n✨ {vehicle_data.get('features', ['Great Condition'])[0] if vehicle_data.get('features') else 'Excellent Condition'}\n📞 Call now!\n\n#cars #auto #{vehicle_data.get('make', 'honda').lower()}"
            elif platform == 'tiktok':
                content = f"🔥 {vehicle_data.get('year', '2023')} {vehicle_data.get('make', 'Honda')} {vehicle_data.get('model', 'Civic')} Alert! 🚗 Only {vehicle_data.get('price', '$22,995')}! Perfect condition ✨ #cars #cardealer #automotive #{vehicle_data.get('make', 'honda').lower()}"
            else:  # reddit
                content = f"[For Sale] {vehicle_data.get('year', '2023')} {vehicle_data.get('make', 'Honda')} {vehicle_data.get('model', 'Civic')} - {vehicle_data.get('price', '$22,995')}\n\nFeatures: {', '.join(vehicle_data.get('features', ['Low Mileage', 'Clean Title', 'Great Condition']))}\nMileage: {vehicle_data.get('mileage', '15,000')} miles\n\nLocated at our dealership. Serious inquiries only. Feel free to ask questions!"
        
        elif content_type == 'promotional':
            if platform == 'instagram':
                content = "🎉 SPECIAL OFFER ALERT! 🎉\n\n💰 Special Financing Available\n⏰ Limited time offer for qualified buyers\n🚗 Wide selection of quality vehicles\n\nDon't wait - Limited time only!\n\n#SpecialOffer #CarFinancing #LimitedTime #QualityCars"
            elif platform == 'facebook':
                content = "🔥 WEEKEND SPECIAL! 🔥\n\nGet pre-approved for financing in minutes!\n✅ Low interest rates\n✅ Flexible terms\n✅ Bad credit? No problem!\n\nVisit us this weekend and drive home today!\n\n#WeekendSpecial #CarFinancing #DriveToday"
            else:
                content = "🚨 FLASH SALE! 🚨 Special financing rates this week only! Get pre-approved in minutes. #FlashSale #CarFinancing #SpecialRates"
        
        else:  # general content
            general_posts = [
                "🌟 Thank you to all our amazing customers! Your trust means everything to us. #CustomerAppreciation #ThankYou",
                "🔧 Regular maintenance keeps your car running smoothly! Schedule your service today. #CarMaintenance #ServiceReminder",
                "🚗 Looking for your next vehicle? We have an amazing selection waiting for you! #NewInventory #CarShopping"
            ]
            content = random.choice(general_posts)
        
        # Prepare response with image information
        content_data = {
            'content': content,
            'platform': platform,
            'content_type': content_type,
            'character_count': len(content),
            'max_characters': platform_info.get('max_chars', 280),
            'supports_images': platform_info.get('supports_images', True),
            'images_available': len(vehicle_images),
            'primary_image': primary_image.to_dict() if primary_image else None,
            'all_images': [img.to_dict() for img in vehicle_images],
            'generated_at': datetime.utcnow().isoformat(),
            'is_simulation': True
        }
        
        return content_data
    
    def generate_content(self, vehicle_data, platform, content_type='vehicle_showcase', keywords=None):
        """Generate social media content with image integration and optional keywords"""
        if self.simulation_mode:
            return self._simulate_content_generation(vehicle_data, platform, content_type)
        else:
            return self._real_content_generation(vehicle_data, platform, content_type, keywords)
    
    def generate_bulk_content(self, dealership_id, content_count=8):
        """Generate bulk content across all platforms with images"""
        try:
            # Sample vehicle data for bulk generation
            sample_vehicles = [
                {
                    'dealership_id': dealership_id,
                    'year': '2023', 'make': 'Honda', 'model': 'Civic',
                    'price': '$22,995', 'mileage': '15,000',
                    'features': ['Low Mileage', 'Clean Title', 'Great Condition']
                },
                {
                    'dealership_id': dealership_id,
                    'year': '2022', 'make': 'Toyota', 'model': 'Camry',
                    'price': '$24,995', 'mileage': '35,000',
                    'features': ['Excellent Condition', 'One Owner', 'Service Records']
                }
            ]
            
            platforms = list(self.platforms.keys())
            content_types = ['vehicle_showcase', 'promotional', 'general']
            
            generated_posts = []
            
            for i in range(content_count):
                vehicle = random.choice(sample_vehicles)
                platform = platforms[i % len(platforms)]
                content_type = content_types[i % len(content_types)]
                
                content_data = self.generate_content(vehicle, platform, content_type)
                
                # Add scheduling information
                content_data.update({
                    'post_id': f"bulk_{dealership_id}_{i+1}",
                    'scheduled_time': (datetime.utcnow() + timedelta(hours=i*2)).isoformat(),
                    'status': 'scheduled'
                })
                
                generated_posts.append(content_data)
            
            return {
                'success': True,
                'total_posts': len(generated_posts),
                'posts': generated_posts,
                'platforms_used': list(set(post['platform'] for post in generated_posts)),
                'content_types_used': list(set(post['content_type'] for post in generated_posts))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Bulk content generation failed: {str(e)}"
            }
    
    def schedule_automated_posting(self, dealership_id, posting_schedule):
        """Schedule automated posting with image integration"""
        try:
            # This would integrate with a task scheduler like Celery
            # For now, simulate the scheduling
            
            scheduled_posts = []
            
            for schedule_item in posting_schedule:
                platform = schedule_item.get('platform')
                frequency = schedule_item.get('frequency', 'daily')
                content_type = schedule_item.get('content_type', 'vehicle_showcase')
                
                # Generate content for scheduling
                vehicle_data = {'dealership_id': dealership_id}
                content_data = self.generate_content(vehicle_data, platform, content_type)
                
                scheduled_posts.append({
                    'platform': platform,
                    'content': content_data['content'],
                    'images': content_data.get('all_images', []),
                    'primary_image': content_data.get('primary_image'),
                    'frequency': frequency,
                    'next_post_time': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                    'status': 'scheduled'
                })
            
            return {
                'success': True,
                'message': f'Automated posting scheduled for {len(scheduled_posts)} platforms',
                'scheduled_posts': scheduled_posts
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Automated posting scheduling failed: {str(e)}"
            }
    
    def get_posting_queue(self, dealership_id):
        """Get current posting queue with image information"""
        try:
            # Simulate posting queue (in production, this would query a database)
            queue_posts = [
                {
                    'id': 1,
                    'platform': 'facebook',
                    'content': '🚗 2023 Honda Civic - Now Available! ✨ Features: Low Mileage | Clean Title | Great Condition 💰 Price: $22,995 📍 Visit us today! #cars #auto #automotive',
                    'images_count': 3,
                    'primary_image_id': 1,
                    'scheduled_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                    'status': 'scheduled'
                },
                {
                    'id': 2,
                    'platform': 'instagram',
                    'content': '🎉 SPECIAL OFFER ALERT! 🎉 Special Financing Available Limited time offer for qualified buyers Limited time only! Don\'t miss out! #Cars #AutoDealer #QualityCars',
                    'images_count': 1,
                    'primary_image_id': 2,
                    'scheduled_time': (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                    'status': 'scheduled'
                },
                {
                    'id': 3,
                    'platform': 'x',
                    'content': '🔥 FEATURED VEHICLE ALERT! 🔥 2022 Toyota Camry 35,000 miles | $24,995 Low Mileage | Clean Title | Great Condition Don\'t miss out! #cars #auto #cardealer',
                    'images_count': 2,
                    'primary_image_id': 3,
                    'scheduled_time': (datetime.utcnow() + timedelta(hours=6)).isoformat(),
                    'status': 'scheduled'
                }
            ]
            
            return {
                'success': True,
                'posts': queue_posts,
                'queue_length': len(queue_posts),
                'next_post_time': queue_posts[0]['scheduled_time'] if queue_posts else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to retrieve posting queue: {str(e)}"
            }

