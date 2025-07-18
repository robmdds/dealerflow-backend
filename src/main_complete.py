"""
DealerFlow Pro Complete SaaS Backend API
Integrates authentication, payments, subscriptions, and all platform features
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timedelta

# Import our models and routes
from models.user import user_service, User
from models.subscription import subscription_service, SubscriptionPlan, SubscriptionStatus
from routes.auth import auth_bp, require_auth
from routes.payments import payments_bp
from routes.user import user_bp
from routes.dealership import dealership_bp
from services.social_media_service import SocialMediaService

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dealerflow-pro-secret-key-2024')

# Enable CORS for all origins
CORS(app, origins="*", supports_credentials=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(payments_bp, url_prefix='/api/payments')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(dealership_bp, url_prefix='/api/dealership')

# Initialize services
social_media_service = SocialMediaService()

# In-memory storage for demo features (replace with database in production)
dealership_data = {}
scraping_configs = {}
automation_status = {}
image_library = {}

def check_feature_access(user, feature):
    """Check if user has access to a specific feature based on subscription"""
    if not user:
        return False
    
    subscription = subscription_service.get_subscription_by_user(user.user_id)
    if not subscription or not subscription.is_active():
        return False
    
    features = subscription.get_plan_features()
    
    # Map feature names to subscription features
    feature_mapping = {
        'website_scraping': features.get('platforms', []),  # Available if has platforms
        'bulk_generation': True,  # Available for all paid plans
        'automation': features.get('automation', False),
        'analytics': features.get('analytics', False),
        'youtube': 'youtube' in features.get('platforms', []),
        'dms_integration': True,  # Available for all paid plans
        'unlimited_posts': features.get('max_posts_per_month', 0) == -1,
        'unlimited_images': features.get('max_images', 0) == -1
    }
    
    return feature_mapping.get(feature, False)

def get_user_platform_access(user):
    """Get list of platforms user has access to"""
    if not user:
        return ['facebook', 'instagram']  # Default for unauthenticated
    
    subscription = subscription_service.get_subscription_by_user(user.user_id)
    if not subscription or not subscription.is_active():
        return ['facebook', 'instagram']  # Trial access
    
    features = subscription.get_plan_features()
    return features.get('platforms', ['facebook', 'instagram'])

# Content Generation Endpoints
@app.route('/api/content/generate-bulk', methods=['POST'])
@require_auth
def generate_bulk_content():
    """Generate bulk content for multiple platforms"""
    try:
        user = request.current_user
        data = request.get_json()
        
        content_type = data.get('content_type', 'vehicle_showcase')
        keywords = data.get('keywords', '')
        platforms = data.get('platforms', ['facebook', 'instagram'])
        
        # Check platform access
        allowed_platforms = get_user_platform_access(user)
        platforms = [p for p in platforms if p in allowed_platforms]
        
        if not platforms:
            return jsonify({
                'success': False,
                'error': 'No accessible platforms selected. Upgrade your plan for more platforms.',
                'upgrade_required': True
            }), 403
        
        # Generate content using social media service
        generated_content = []
        
        for platform in platforms:
            content = social_media_service.generate_content(
                platform=platform,
                content_type=content_type,
                keywords=keywords,
                dealership_name=user.dealership_name
            )
            
            generated_content.append({
                'platform': platform,
                'content': content['text'],
                'hashtags': content['hashtags'],
                'content_type': content_type,
                'generated_at': datetime.utcnow().isoformat(),
                'character_count': len(content['text'])
            })
        
        return jsonify({
            'success': True,
            'content': generated_content,
            'count': len(generated_content),
            'message': f'Generated content for {len(platforms)} platforms',
            'platforms_used': platforms,
            'platforms_available': allowed_platforms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Content generation failed: {str(e)}'
        }), 500

# Website Scraping Endpoints
@app.route('/api/scraping/setup', methods=['POST'])
@require_auth
def setup_scraping():
    """Setup website scraping for dealership inventory"""
    try:
        user = request.current_user
        data = request.get_json()
        
        website_url = data.get('website_url', '').strip()
        
        if not website_url:
            return jsonify({
                'success': False,
                'error': 'Website URL is required'
            }), 400
        
        # Add protocol if missing
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Test website accessibility
        try:
            response = requests.get(website_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            if response.status_code == 200:
                # Detect platform type
                content = response.text.lower()
                platform_detected = "Generic Website"
                
                if 'wordpress' in content or 'wp-content' in content:
                    platform_detected = "WordPress"
                elif 'shopify' in content or 'shopify.com' in content:
                    platform_detected = "Shopify"
                elif 'wix' in content or 'wix.com' in content:
                    platform_detected = "Wix"
                elif 'squarespace' in content:
                    platform_detected = "Squarespace"
                
                # Store scraping configuration
                scraping_configs[user.user_id] = {
                    'website_url': website_url,
                    'platform_detected': platform_detected,
                    'status': 'configured',
                    'last_sync': None,
                    'setup_date': datetime.utcnow().isoformat(),
                    'images_found': 0,
                    'last_error': None
                }
                
                return jsonify({
                    'success': True,
                    'message': f'Scraping configured for {website_url}',
                    'website_url': website_url,
                    'platform_detected': platform_detected,
                    'status': 'configured'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Website not accessible (HTTP {response.status_code})'
                }), 400
                
        except requests.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Failed to access website: {str(e)}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Scraping setup failed: {str(e)}'
        }), 500

@app.route('/api/scraping/status/<int:user_id>', methods=['GET'])
@require_auth
def get_scraping_status(user_id):
    """Get scraping status for user"""
    try:
        user = request.current_user
        
        # Users can only access their own scraping status
        if user.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        config = scraping_configs.get(user_id, {
            'status': 'not_configured',
            'website_url': None,
            'platform_detected': None,
            'last_sync': None,
            'images_found': 0
        })
        
        return jsonify({
            'success': True,
            'scraping_config': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get scraping status: {str(e)}'
        }), 500

# Image Management Endpoints
@app.route('/api/images/dealership/<int:user_id>', methods=['GET'])
@require_auth
def get_dealership_images(user_id):
    """Get images for dealership"""
    try:
        user = request.current_user
        
        # Users can only access their own images
        if user.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Get images from library (demo data)
        images = image_library.get(user_id, [
            {
                'id': 1,
                'url': '/api/placeholder/400/300',
                'filename': 'vehicle_1.jpg',
                'source': 'manual_upload',
                'uploaded_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'url': '/api/placeholder/400/300',
                'filename': 'vehicle_2.jpg',
                'source': 'website_scraping',
                'uploaded_at': datetime.utcnow().isoformat()
            }
        ])
        
        return jsonify({
            'success': True,
            'images': images,
            'count': len(images)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get images: {str(e)}'
        }), 500

# Automation Endpoints
@app.route('/api/automation/status/<int:user_id>', methods=['GET'])
@require_auth
def get_automation_status(user_id):
    """Get automation status for user"""
    try:
        user = request.current_user
        
        # Users can only access their own automation status
        if user.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Check if user has automation access
        has_automation = check_feature_access(user, 'automation')
        
        status = automation_status.get(user_id, {
            'enabled': False,
            'last_run': None,
            'next_run': None,
            'posts_in_queue': 0,
            'total_posts_generated': 0
        })
        
        return jsonify({
            'success': True,
            'automation_status': status,
            'has_access': has_automation,
            'upgrade_required': not has_automation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get automation status: {str(e)}'
        }), 500

# Analytics Endpoints
@app.route('/api/analytics/dashboard/<int:user_id>', methods=['GET'])
@require_auth
def get_analytics_dashboard(user_id):
    """Get analytics dashboard data"""
    try:
        user = request.current_user
        
        # Users can only access their own analytics
        if user.user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Check if user has analytics access
        has_analytics = check_feature_access(user, 'analytics')
        
        if not has_analytics:
            return jsonify({
                'success': False,
                'error': 'Analytics requires a paid subscription plan',
                'upgrade_required': True
            }), 403
        
        # Get user's accessible platforms
        platforms = get_user_platform_access(user)
        
        # Generate sample analytics data
        analytics_data = {
            'total_posts': 156,
            'total_engagement': 2847,
            'platforms': {}
        }
        
        for platform in platforms:
            analytics_data['platforms'][platform] = {
                'posts': 26,
                'engagement': 485,
                'reach': 1250,
                'clicks': 89
            }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data,
            'platforms': platforms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get analytics: {str(e)}'
        }), 500

# Health Check and Info
@app.route('/', methods=['GET'])
def health_check():
    """API health check and information"""
    return jsonify({
        'success': True,
        'message': 'DealerFlow Pro SaaS API is running',
        'version': '3.0.0',
        'features': [
            'authentication',
            'subscriptions', 
            'payments',
            'feature_gating',
            'content_generation',
            'website_scraping',
            'automation',
            'analytics',
            'youtube_support'
        ],
        'endpoints': {
            'auth': ['/api/auth/signup', '/api/auth/login', '/api/auth/profile'],
            'payments': ['/api/payments/plans', '/api/payments/subscription', '/api/payments/upgrade'],
            'content': ['/api/content/generate-bulk'],
            'scraping': ['/api/scraping/setup', '/api/scraping/status/<id>'],
            'images': ['/api/images/dealership/<id>'],
            'automation': ['/api/automation/status/<id>'],
            'analytics': ['/api/analytics/dashboard/<id>']
        },
        'subscription_plans': {
            'trial': 'Free 14-day trial with basic features',
            'starter': '$197/month - 3 platforms, 200 posts/month',
            'professional': '$397/month - 5 platforms, 1000 posts/month',
            'enterprise': '$597/month - 6 platforms including YouTube, unlimited'
        }
    })

@app.route('/api/feature-check/<feature>', methods=['GET'])
@require_auth
def check_feature_endpoint(feature):
    """Check if user has access to a specific feature"""
    try:
        user = request.current_user
        has_access = check_feature_access(user, feature)
        
        subscription = subscription_service.get_subscription_by_user(user.user_id)
        
        return jsonify({
            'success': True,
            'feature': feature,
            'has_access': has_access,
            'current_plan': subscription.plan.value if subscription else 'none',
            'upgrade_required': not has_access
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Feature check failed: {str(e)}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting DealerFlow Pro SaaS Backend...")
    print("📊 Features: Authentication, Payments, Subscriptions, Feature Gating")
    print("🌐 CORS enabled for all origins")
    print("🔐 JWT authentication with 7-day expiry")
    print("💳 Helcim payment processing integration")
    print("📱 6 social media platforms supported (including YouTube)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

