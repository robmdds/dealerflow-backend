"""
Authentication Routes for DealerFlow Pro
Handles user registration, login, and account management
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import re
from models.user import user_service, User

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': 'No authorization token provided'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = User.verify_jwt_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Get current user
        user = user_service.get_user_by_id(payload.get('user_id'))
        if not user or not user.is_active:
            return jsonify({'success': False, 'error': 'User account not found or inactive'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'dealership_name', 'contact_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        email = data['email'].strip()
        password = data['password']
        dealership_name = data['dealership_name'].strip()
        contact_name = data['contact_name'].strip()
        phone = data.get('phone', '').strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Create user account
        user, error = user_service.create_user(
            email=email,
            password=password,
            dealership_name=dealership_name,
            contact_name=contact_name,
            phone=phone
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Generate JWT token
        token = user.generate_jwt_token()
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user.to_dict(),
            'token': token,
            'trial_days_remaining': (user.trial_end_date - user.created_at).days
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Registration failed: ' + str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Authenticate user
        user, error = user_service.authenticate_user(email, password)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401
        
        # Check if trial has expired and user doesn't have active subscription
        if user.is_trial_expired() and user.subscription_status == 'trial':
            return jsonify({
                'success': False,
                'error': 'Trial period has expired. Please upgrade to continue using DealerFlow Pro.',
                'trial_expired': True,
                'user': user.to_dict()
            }), 402  # Payment Required
        
        # Generate JWT token
        token = user.generate_jwt_token()
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token,
            'trial_days_remaining': max(0, (user.trial_end_date - user.created_at).days) if user.subscription_status == 'trial' else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Login failed: ' + str(e)
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
    try:
        user = request.current_user
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'feature_limits': user.get_feature_limits(),
            'trial_days_remaining': max(0, (user.trial_end_date - user.created_at).days) if user.subscription_status == 'trial' else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get profile: ' + str(e)
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Update allowed fields
        updated_user, error = user_service.update_user(
            user.user_id,
            dealership_name=data.get('dealership_name'),
            contact_name=data.get('contact_name'),
            phone=data.get('phone')
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to update profile: ' + str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Both old and new passwords are required'
            }), 400
        
        # Validate new password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Change password
        success, message = user_service.change_password(
            user.user_id,
            old_password,
            new_password
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to change password: ' + str(e)
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token validity"""
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token is required'
            }), 400
        
        payload = User.verify_jwt_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Get user to verify account is still active
        user = user_service.get_user_by_id(payload.get('user_id'))
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'User account not found or inactive'
            }), 401
        
        return jsonify({
            'success': True,
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Token verification failed: ' + str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user (client-side token removal)"""
    try:
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Logout failed: ' + str(e)
        }), 500

@auth_bp.route('/subscription-status', methods=['GET'])
@require_auth
def get_subscription_status():
    """Get user subscription status and limits"""
    try:
        user = request.current_user
        
        return jsonify({
            'success': True,
            'subscription': {
                'plan': user.subscription_plan,
                'status': user.subscription_status,
                'trial_end_date': user.trial_end_date.isoformat() if user.trial_end_date else None,
                'is_trial_expired': user.is_trial_expired(),
                'can_access_features': user.can_access_features(),
                'feature_limits': user.get_feature_limits(),
                'trial_days_remaining': max(0, (user.trial_end_date - user.created_at).days) if user.subscription_status == 'trial' else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get subscription status: ' + str(e)
        }), 500

# Admin routes (for platform management)
@auth_bp.route('/admin/users', methods=['GET'])
@require_auth
def get_all_users():
    """Get all users (admin only)"""
    try:
        # In production, add admin role check here
        users = user_service.get_all_users()
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'stats': user_service.get_user_stats()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get users: ' + str(e)
        }), 500

