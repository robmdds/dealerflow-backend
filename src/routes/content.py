from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.dealership import SocialMediaPost, ContentTemplate
from services.social_media_service import SocialMediaService
from src.extensions import db

content_bp = Blueprint('content', __name__)
social_service = SocialMediaService(simulation_mode=True)

@content_bp.route('/generate', methods=['POST'])
def generate_content():
    """Generate AI-powered social media content"""
    try:
        data = request.get_json()
        
        # Extract vehicle data
        vehicle_data = {
            'year': data.get('year', '2023'),
            'make': data.get('make', 'Honda'),
            'model': data.get('model', 'Civic'),
            'price': data.get('price', '$22,995'),
            'mileage': data.get('mileage', '15,000')
        }
        
        platform = data.get('platform', 'instagram')
        content_type = data.get('content_type', 'vehicle_showcase')
        keywords = data.get('keywords', '')  # Optional keywords
        
        # Generate content using the social media service
        result = social_service.generate_content(vehicle_data, platform, content_type, keywords)
        
        return jsonify({
            'success': True,
            'content': result['content'],
            'platform': result['platform'],
            'character_count': result['character_count'],
            'hashtags': result['hashtags'],
            'estimated_reach': result['estimated_reach'],
            'predicted_engagement': result['predicted_engagement'],
            'best_posting_time': result['best_posting_time']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_bp.route('/schedule', methods=['POST'])
def schedule_post():
    """Schedule a social media post"""
    try:
        data = request.get_json()
        
        content = data.get('content', '')
        platform = data.get('platform', 'instagram')
        schedule_time_str = data.get('schedule_time')
        
        # Parse schedule time
        if schedule_time_str:
            schedule_time = datetime.fromisoformat(schedule_time_str.replace('Z', '+00:00'))
        else:
            schedule_time = datetime.now() + timedelta(hours=1)
        
        # Schedule the post
        result = social_service.schedule_post(content, platform, schedule_time)
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'post_id': result['post_id'],
            'scheduled_time': result['scheduled_time']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get social media analytics"""
    try:
        platform = request.args.get('platform')
        days = int(request.args.get('days', 30))
        
        analytics = social_service.get_analytics(platform, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_bp.route('/posts', methods=['GET'])
def get_recent_posts():
    """Get recent social media posts"""
    try:
        # Simulate recent posts data
        recent_posts = [
            {
                'id': 1,
                'platform': 'instagram',
                'content': '🚗 2023 Honda Civic - Now Available! ✨ Features: Low Mileage | Clean Title | Great Condition 💰 Price: $22,995 📍 Visit us today! #cars #auto #automotive',
                'posted_time': '2 hours ago',
                'engagement': {
                    'likes': 45,
                    'comments': 8,
                    'shares': 3
                },
                'status': 'published'
            },
            {
                'id': 2,
                'platform': 'facebook',
                'content': '🎉 SPECIAL OFFER ALERT! 🎉 Special Financing Available Limited time offer for qualified buyers Limited time only! Don\'t miss out! #Cars #AutoDealer #QualityCars',
                'posted_time': 'Today 3:00 PM',
                'engagement': {
                    'likes': 23,
                    'comments': 5,
                    'shares': 7
                },
                'status': 'scheduled'
            },
            {
                'id': 3,
                'platform': 'tiktok',
                'content': '🔥 FEATURED VEHICLE ALERT! 🔥 2022 Toyota Camry 35,000 miles | $24,995 Low Mileage | Clean Title | Great Condition Don\'t miss out! #cars #auto #cardealer',
                'posted_time': '5 hours ago',
                'engagement': {
                    'likes': 127,
                    'comments': 23,
                    'shares': 15
                },
                'status': 'published'
            }
        ]
        
        return jsonify({
            'success': True,
            'posts': recent_posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

