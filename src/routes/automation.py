"""
Automation API Routes for DealerFlow Pro
Handles automated social media posting, content generation, and workflow management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.services.social_media_service import SocialMediaService
import json

automation_bp = Blueprint('automation', __name__)

# Initialize social media service (use real mode for production)
social_service = SocialMediaService(simulation_mode=False)

@automation_bp.route('/generate-content', methods=['POST'])
def generate_content():
    """Generate AI-powered content for specific vehicle and platform"""
    try:
        data = request.get_json()
        
        vehicle_data = data.get('vehicle_data', {})
        platform = data.get('platform', 'instagram')
        content_type = data.get('content_type', 'vehicle_showcase')
        keywords = data.get('keywords', '')  # Optional keywords
        
        result = social_service.generate_content(
            vehicle_data=vehicle_data,
            platform=platform,
            content_type=content_type,
            keywords=keywords
        )
        
        return jsonify({
            'success': True,
            'content_data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/bulk-generate', methods=['POST'])
def bulk_generate_content():
    """Generate bulk content for multiple platforms and vehicles"""
    try:
        data = request.get_json()
        
        dealership_info = data.get('dealership_info', {})
        vehicle_inventory = data.get('vehicle_inventory', None)
        platforms = data.get('platforms', ['facebook', 'instagram', 'tiktok', 'twitter', 'reddit'])
        
        result = social_service.generate_bulk_content(
            dealership_info=dealership_info,
            vehicle_inventory=vehicle_inventory,
            platforms=platforms
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/schedule-posts', methods=['POST'])
def schedule_posts():
    """Schedule multiple posts with optimal timing"""
    try:
        data = request.get_json()
        
        posts = data.get('posts', [])
        start_time_str = data.get('start_time', None)
        interval_hours = data.get('interval_hours', 2)
        
        start_time = None
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        
        result = social_service.schedule_bulk_posts(
            posts=posts,
            start_time=start_time,
            interval_hours=interval_hours
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/auto-workflow', methods=['POST'])
def auto_workflow():
    """Execute complete automated posting workflow"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id', 1)
        vehicle_inventory = data.get('vehicle_inventory', None)
        
        result = social_service.auto_post_workflow(
            dealership_id=dealership_id,
            vehicle_inventory=vehicle_inventory
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/posting-queue', methods=['GET'])
def get_posting_queue():
    """Get current posting queue and scheduled posts"""
    try:
        dealership_id = request.args.get('dealership_id', 1, type=int)
        
        result = social_service.get_posting_queue(dealership_id=dealership_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get social media analytics and performance data"""
    try:
        platform = request.args.get('platform', None)
        days = request.args.get('days', 30, type=int)
        
        result = social_service.get_analytics(platform=platform, days=days)
        
        return jsonify({
            'success': True,
            'analytics': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/insights', methods=['GET'])
def get_performance_insights():
    """Get AI-powered performance insights and recommendations"""
    try:
        dealership_id = request.args.get('dealership_id', 1, type=int)
        days = request.args.get('days', 30, type=int)
        
        result = social_service.get_performance_insights(
            dealership_id=dealership_id,
            days=days
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/connect-account', methods=['POST'])
def connect_social_account():
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

@automation_bp.route('/account-status/<platform>', methods=['GET'])
def get_account_status(platform):
    """Get social media account connection status"""
    try:
        result = social_service.get_account_status(platform)
        
        return jsonify({
            'success': True,
            'platform': platform,
            'account_status': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/content-suggestions', methods=['GET'])
def get_content_suggestions():
    """Get AI-powered content suggestions"""
    try:
        dealership_id = request.args.get('dealership_id', 1, type=int)
        
        dealership_info = {'id': dealership_id}
        suggestions = social_service.get_content_suggestions(dealership_info)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported social media platforms"""
    try:
        return jsonify({
            'success': True,
            'platforms': social_service.platforms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/health', methods=['GET'])
def automation_health():
    """Health check for automation service"""
    return jsonify({
        'status': 'healthy',
        'service': 'DealerFlow Pro Automation',
        'timestamp': datetime.now().isoformat(),
        'features': [
            'AI Content Generation',
            'Bulk Content Creation',
            'Automated Scheduling',
            'Multi-Platform Posting',
            'Performance Analytics',
            'Account Management'
        ]
    })

