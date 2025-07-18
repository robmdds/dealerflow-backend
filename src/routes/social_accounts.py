from flask import Blueprint, jsonify, request
import sys
import os

# Add the parent directory to the path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.social_media_service import SocialMediaService

social_accounts_bp = Blueprint('social_accounts', __name__)
social_service = SocialMediaService(simulation_mode=True)

@social_accounts_bp.route('/status', methods=['GET'])
def get_accounts_status():
    """Get status of all social media accounts"""
    try:
        platforms = ['facebook', 'instagram', 'tiktok', 'twitter', 'reddit']
        accounts_status = {}
        
        for platform in platforms:
            accounts_status[platform] = social_service.get_account_status(platform)
        
        return jsonify({
            'success': True,
            'accounts': accounts_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_accounts_bp.route('/connect', methods=['POST'])
def connect_account():
    """Connect a social media account"""
    try:
        data = request.get_json()
        platform = data.get('platform')
        credentials = data.get('credentials', {})
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform is required'
            }), 400
        
        result = social_service.connect_account(platform, credentials)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_accounts_bp.route('/disconnect', methods=['POST'])
def disconnect_account():
    """Disconnect a social media account"""
    try:
        data = request.get_json()
        platform = data.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform is required'
            }), 400
        
        # Simulate disconnection
        return jsonify({
            'success': True,
            'platform': platform,
            'message': f'{platform.title()} account disconnected successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_accounts_bp.route('/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported social media platforms"""
    try:
        platforms = [
            {
                'id': 'facebook',
                'name': 'Facebook',
                'icon': 'fab fa-facebook',
                'color': '#1877f2',
                'description': 'Connect your Facebook business page'
            },
            {
                'id': 'instagram',
                'name': 'Instagram',
                'icon': 'fab fa-instagram',
                'color': '#E4405F',
                'description': 'Connect your Instagram business account'
            },
            {
                'id': 'tiktok',
                'name': 'TikTok',
                'icon': 'fab fa-tiktok',
                'color': '#000000',
                'description': 'Connect your TikTok business account'
            },
            {
                'id': 'twitter',
                'name': 'Twitter/X',
                'icon': 'fab fa-twitter',
                'color': '#1DA1F2',
                'description': 'Connect your Twitter/X business account'
            },
            {
                'id': 'reddit',
                'name': 'Reddit',
                'icon': 'fab fa-reddit',
                'color': '#FF4500',
                'description': 'Connect your Reddit business account'
            }
        ]
        
        return jsonify({
            'success': True,
            'platforms': platforms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

