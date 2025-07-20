"""
DealerFlow Pro SaaS Backend API
Complete authentication, subscription, and feature gating system
"""

from flask import Flask, jsonify, request, session
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
import secrets
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'dealerflow-pro-secret-key-2024'
CORS(
    app,
    origins=["https://www.dynamicdealerservices.com"],
    supports_credentials=True
)

# In-memory storage for demo (in production, use a real database)
users = {}
subscriptions = {}
dealership_data = {}
scraping_configs = {}
sessions = {}

# Subscription plans
SUBSCRIPTION_PLANS = {
    'trial': {
        'name': 'Free Trial',
        'price': 0,
        'duration_days': 14,
        'features': {
            'platforms': ['facebook', 'instagram'],
            'posts_per_month': 50,
            'image_uploads': 10,
            'website_scraping': False,
            'dms_integration': False,
            'bulk_generation': False,
            'analytics': 'basic'
        }
    },
    'starter': {
        'name': 'Starter Plan',
        'price': 197,
        'duration_days': 30,
        'features': {
            'platforms': ['facebook', 'instagram', 'tiktok'],
            'posts_per_month': 200,
            'image_uploads': 50,
            'website_scraping': True,
            'dms_integration': False,
            'bulk_generation': True,
            'analytics': 'standard'
        }
    },
    'professional': {
        'name': 'Professional Plan',
        'price': 397,
        'duration_days': 30,
        'features': {
            'platforms': ['facebook', 'instagram', 'tiktok', 'reddit', 'x'],
            'posts_per_month': 1000,
            'image_uploads': 200,
            'website_scraping': True,
            'dms_integration': True,
            'bulk_generation': True,
            'analytics': 'advanced'
        }
    },
    'enterprise': {
        'name': 'Enterprise Plan',
        'price': 597,
        'duration_days': 30,
        'features': {
            'platforms': ['facebook', 'instagram', 'tiktok', 'reddit', 'x', 'youtube'],
            'posts_per_month': -1,  # unlimited
            'image_uploads': -1,    # unlimited
            'website_scraping': True,
            'dms_integration': True,
            'bulk_generation': True,
            'analytics': 'premium'
        }
    }
}

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        salt, password_hash = hashed.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except:
        return False

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_user_from_session():
    """Get user from session token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    session_data = sessions.get(token)
    
    if not session_data:
        return None
    
    # Check if session is expired
    if datetime.now() > session_data['expires']:
        del sessions[token]
        return None
    
    return users.get(session_data['user_id'])

def check_feature_access(user, feature):
    """Check if user has access to a specific feature"""
    if not user:
        return False
    
    subscription = subscriptions.get(user['id'])
    if not subscription:
        return False
    
    # Check if subscription is active
    if datetime.now() > subscription['expires']:
        return False
    
    plan = SUBSCRIPTION_PLANS.get(subscription['plan'])
    if not plan:
        return False
    
    return plan['features'].get(feature, False)

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        dealership_name = data.get('dealership_name', '').strip()
        contact_name = data.get('contact_name', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validation
        if not all([email, password, dealership_name, contact_name]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Check if user already exists
        for user in users.values():
            if user['email'] == email:
                return jsonify({
                    'success': False,
                    'error': 'Email already registered'
                }), 400
        
        # Create user
        user_id = str(len(users) + 1)
        user = {
            'id': user_id,
            'email': email,
            'password': hash_password(password),
            'dealership_name': dealership_name,
            'contact_name': contact_name,
            'phone': phone,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        users[user_id] = user
        
        # Create trial subscription
        subscription = {
            'user_id': user_id,
            'plan': 'trial',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=14)).isoformat(),
            'payment_method': None
        }
        
        subscriptions[user_id] = subscription
        
        # Create session
        token = generate_session_token()
        sessions[token] = {
            'user_id': user_id,
            'created': datetime.now(),
            'expires': datetime.now() + timedelta(days=30)
        }
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'dealership_name': user['dealership_name'],
                'contact_name': user['contact_name']
            },
            'subscription': {
                'plan': subscription['plan'],
                'status': subscription['status'],
                'expires': subscription['expires']
            },
            'token': token
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not all([email, password]):
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Find user
        user = None
        for u in users.values():
            if u['email'] == email:
                user = u
                break
        
        if not user or not verify_password(password, user['password']):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Create session
        token = generate_session_token()
        sessions[token] = {
            'user_id': user['id'],
            'created': datetime.now(),
            'expires': datetime.now() + timedelta(days=30)
        }
        
        # Get subscription
        subscription = subscriptions.get(user['id'])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'dealership_name': user['dealership_name'],
                'contact_name': user['contact_name']
            },
            'subscription': {
                'plan': subscription['plan'] if subscription else 'none',
                'status': subscription['status'] if subscription else 'inactive',
                'expires': subscription['expires'] if subscription else None
            },
            'token': token
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Remove session
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if token in sessions:
                del sessions[token]
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Logout failed: {str(e)}'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        subscription = subscriptions.get(user['id'])
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'dealership_name': user['dealership_name'],
                'contact_name': user['contact_name'],
                'phone': user.get('phone', '')
            },
            'subscription': {
                'plan': subscription['plan'] if subscription else 'none',
                'status': subscription['status'] if subscription else 'inactive',
                'expires': subscription['expires'] if subscription else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get user info: {str(e)}'
        }), 500

# Subscription endpoints
@app.route('/api/subscriptions/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        return jsonify({
            'success': True,
            'plans': SUBSCRIPTION_PLANS
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get plans: {str(e)}'
        }), 500

@app.route('/api/subscriptions/upgrade', methods=['POST'])
def upgrade_subscription():
    """Upgrade user subscription"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        data = request.get_json()
        plan_id = data.get('plan')
        payment_method = data.get('payment_method', {})
        
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({
                'success': False,
                'error': 'Invalid subscription plan'
            }), 400
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # In production, process payment with Helcim here
        # For demo, we'll simulate successful payment
        
        # Update subscription
        subscription = {
            'user_id': user['id'],
            'plan': plan_id,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=plan['duration_days'])).isoformat(),
            'payment_method': payment_method
        }
        
        subscriptions[user['id']] = subscription
        
        return jsonify({
            'success': True,
            'message': f'Successfully upgraded to {plan["name"]}',
            'subscription': {
                'plan': subscription['plan'],
                'status': subscription['status'],
                'expires': subscription['expires']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upgrade failed: {str(e)}'
        }), 500

# Feature-gated endpoints
@app.route('/api/scraping/setup', methods=['POST'])
def setup_scraping():
    """Setup website scraping for a dealership (requires subscription)"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        if not check_feature_access(user, 'website_scraping'):
            return jsonify({
                'success': False,
                'error': 'Website scraping requires Starter plan or higher',
                'upgrade_required': True
            }), 403
        
        data = request.get_json()
        website_url = data.get('website_url')
        
        if not website_url:
            return jsonify({
                'success': False,
                'error': 'website_url is required'
            }), 400
        
        # Simple URL validation
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Test if website is accessible
        try:
            response = requests.get(website_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                platform_detected = "Generic Website"
                # Simple platform detection
                content = response.text.lower()
                if 'wordpress' in content:
                    platform_detected = "WordPress"
                elif 'shopify' in content:
                    platform_detected = "Shopify"
                elif 'wix' in content:
                    platform_detected = "Wix"
                
                # Store configuration
                scraping_configs[user['id']] = {
                    'website_url': website_url,
                    'platform_detected': platform_detected,
                    'status': 'configured',
                    'last_sync': None,
                    'setup_date': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Website scraping setup completed successfully',
                    'website_url': website_url,
                    'platform_detected': platform_detected,
                    'status': 'configured',
                    'last_sync': None,
                    'url': website_url
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

@app.route('/api/content/generate-bulk', methods=['POST'])
def generate_bulk_content():
    """Generate bulk content for all platforms (requires subscription)"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        if not check_feature_access(user, 'bulk_generation'):
            return jsonify({
                'success': False,
                'error': 'Bulk generation requires Starter plan or higher',
                'upgrade_required': True
            }), 403
        
        data = request.get_json()
        
        content_type = data.get('content_type', 'vehicle_showcase')
        keywords = data.get('keywords', '')
        platforms = data.get('platforms', ['facebook', 'instagram'])
        
        # Check platform access
        subscription = subscriptions.get(user['id'])
        if subscription:
            plan = SUBSCRIPTION_PLANS.get(subscription['plan'])
            if plan:
                allowed_platforms = plan['features']['platforms']
                platforms = [p for p in platforms if p in allowed_platforms]
        
        # Generate sample content for each platform
        sample_content = []
        
        for platform in platforms:
            if platform == 'facebook':
                content = f"🚗 Amazing vehicle showcase! {keywords} Check out our latest inventory with great deals and financing options available."
            elif platform == 'instagram':
                content = f"✨ New arrival! {keywords} #Cars #Automotive #Dealership #NewCar #Quality"
            elif platform == 'tiktok':
                content = f"🎵 Quick tour of our {keywords} inventory! Swipe to see more amazing vehicles. #CarTok #Automotive"
            elif platform == 'reddit':
                content = f"Just wanted to share our latest {keywords} inventory. Great deals available for serious buyers!"
            elif platform == 'x':
                content = f"🚗 New {keywords} vehicles just arrived! DM for pricing and availability. #Cars #Automotive"
            elif platform == 'youtube':
                content = f"🎥 Complete walkthrough of our {keywords} inventory. Subscribe for more vehicle reviews and tours!"
            else:
                content = f"Check out our amazing {keywords} vehicle selection!"
            
            sample_content.append({
                'platform': platform,
                'content': content,
                'content_type': content_type,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'content': sample_content,
            'count': len(sample_content),
            'message': f'Generated content for {len(platforms)} platforms'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Content generation failed: {str(e)}'
        }), 500

# Health check and info endpoints
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'DealerFlow Pro SaaS API is running',
        'version': '2.0.0',
        'features': ['authentication', 'subscriptions', 'feature_gating', 'scraping'],
        'endpoints': [
            '/api/auth/signup',
            '/api/auth/login',
            '/api/auth/logout',
            '/api/auth/me',
            '/api/subscriptions/plans',
            '/api/subscriptions/upgrade',
            '/api/scraping/setup',
            '/api/content/generate-bulk'
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

