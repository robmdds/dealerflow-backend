"""
User Model for DealerFlow Pro Authentication System
"""

from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
import os

class User:
    """User model for authentication and account management"""
    
    def __init__(self, user_id=None, email=None, password_hash=None, 
                 dealership_name=None, contact_name=None, phone=None,
                 subscription_plan=None, subscription_status='trial',
                 created_at=None, last_login=None, is_active=True):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        self.dealership_name = dealership_name
        self.contact_name = contact_name
        self.phone = phone
        self.subscription_plan = subscription_plan or 'trial'
        self.subscription_status = subscription_status
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.is_active = is_active
        self.trial_end_date = self.created_at + timedelta(days=14)  # 14-day trial
    
    @staticmethod
    def hash_password(password):
        """Hash a password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password):
        """Verify a password against the stored hash"""
        if not self.password_hash:
            return False
        
        try:
            salt, stored_hash = self.password_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except ValueError:
            return False
    
    def generate_jwt_token(self):
        """Generate JWT token for authentication"""
        payload = {
            'user_id': self.user_id,
            'email': self.email,
            'dealership_name': self.dealership_name,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
            'iat': datetime.utcnow()
        }
        
        secret_key = os.getenv('JWT_SECRET_KEY', 'dealerflow-pro-secret-key-2024')
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_jwt_token(token):
        """Verify and decode JWT token"""
        try:
            secret_key = os.getenv('JWT_SECRET_KEY', 'dealerflow-pro-secret-key-2024')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        user_dict = {
            'user_id': self.user_id,
            'email': self.email,
            'dealership_name': self.dealership_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'is_trial_expired': self.is_trial_expired()
        }
        
        if include_sensitive:
            user_dict['password_hash'] = self.password_hash
        
        return user_dict
    
    def is_trial_expired(self):
        """Check if trial period has expired"""
        if self.subscription_status != 'trial':
            return False
        return datetime.utcnow() > self.trial_end_date
    
    def can_access_features(self):
        """Check if user can access platform features"""
        if not self.is_active:
            return False
        
        if self.subscription_status == 'active':
            return True
        
        if self.subscription_status == 'trial' and not self.is_trial_expired():
            return True
        
        return False
    
    def get_feature_limits(self):
        """Get feature limits based on subscription plan"""
        limits = {
            'trial': {
                'max_posts_per_month': 50,
                'max_images': 100,
                'platforms': ['facebook', 'instagram'],
                'automation': False,
                'analytics': False
            },
            'starter': {
                'max_posts_per_month': 200,
                'max_images': 500,
                'platforms': ['facebook', 'instagram', 'x'],
                'automation': True,
                'analytics': True
            },
            'professional': {
                'max_posts_per_month': 1000,
                'max_images': 2000,
                'platforms': ['facebook', 'instagram', 'x', 'tiktok', 'reddit'],
                'automation': True,
                'analytics': True
            },
            'enterprise': {
                'max_posts_per_month': -1,  # Unlimited
                'max_images': -1,  # Unlimited
                'platforms': ['facebook', 'instagram', 'x', 'tiktok', 'reddit', 'youtube'],
                'automation': True,
                'analytics': True
            }
        }
        
        return limits.get(self.subscription_plan, limits['trial'])

class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        # In-memory storage for demo (replace with database in production)
        self.users = {}
        self.user_counter = 1
    
    def create_user(self, email, password, dealership_name, contact_name, phone=None):
        """Create a new user account"""
        # Check if email already exists
        if self.get_user_by_email(email):
            return None, "Email already registered"
        
        # Create new user
        user = User(
            user_id=self.user_counter,
            email=email.lower().strip(),
            password_hash=User.hash_password(password),
            dealership_name=dealership_name.strip(),
            contact_name=contact_name.strip(),
            phone=phone.strip() if phone else None,
            subscription_plan='trial',
            subscription_status='trial'
        )
        
        self.users[self.user_counter] = user
        self.user_counter += 1
        
        return user, None
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None, "Invalid email or password"
        
        if not user.verify_password(password):
            return None, "Invalid email or password"
        
        if not user.is_active:
            return None, "Account is deactivated"
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        return user, None
    
    def get_user_by_email(self, email):
        """Get user by email address"""
        email = email.lower().strip()
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return self.users.get(user_id)
    
    def update_user(self, user_id, **kwargs):
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None, "User not found"
        
        # Update allowed fields
        allowed_fields = ['dealership_name', 'contact_name', 'phone', 'subscription_plan', 'subscription_status']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)
        
        return user, None
    
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not user.verify_password(old_password):
            return False, "Current password is incorrect"
        
        user.password_hash = User.hash_password(new_password)
        return True, "Password updated successfully"
    
    def deactivate_user(self, user_id):
        """Deactivate user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        user.is_active = False
        return True, "Account deactivated"
    
    def get_all_users(self):
        """Get all users (admin function)"""
        return list(self.users.values())
    
    def get_user_stats(self):
        """Get user statistics"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)
        trial_users = sum(1 for user in self.users.values() if user.subscription_status == 'trial')
        paid_users = sum(1 for user in self.users.values() if user.subscription_status == 'active')
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'trial_users': trial_users,
            'paid_users': paid_users
        }

# Global user service instance
user_service = UserService()

