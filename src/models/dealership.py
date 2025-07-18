from datetime import datetime
from src.extensions import db

class Dealership(db.Model):
    __tablename__ = 'dealerships'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(20))
    zip_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    business_hours = db.Column(db.Text)
    subscription_plan = db.Column(db.String(20), default='basic')  # basic, pro, enterprise
    subscription_status = db.Column(db.String(20), default='active')  # active, suspended, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'business_hours': self.business_hours,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SocialMediaAccount(db.Model):
    __tablename__ = 'social_media_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    dealership_id = db.Column(db.Integer, db.ForeignKey('dealerships.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # facebook, instagram, tiktok, twitter, reddit
    account_id = db.Column(db.String(100))
    account_name = db.Column(db.String(100))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    is_connected = db.Column(db.Boolean, default=False)
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dealership = db.relationship('Dealership', backref='social_accounts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'dealership_id': self.dealership_id,
            'platform': self.platform,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'is_connected': self.is_connected,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ContentTemplate(db.Model):
    __tablename__ = 'content_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    dealership_id = db.Column(db.Integer, db.ForeignKey('dealerships.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # vehicle_showcase, promotion, testimonial, etc.
    platforms = db.Column(db.Text)  # JSON array of supported platforms
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dealership = db.relationship('Dealership', backref='content_templates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'dealership_id': self.dealership_id,
            'name': self.name,
            'description': self.description,
            'template_content': self.template_content,
            'category': self.category,
            'platforms': self.platforms,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SocialMediaPost(db.Model):
    __tablename__ = 'social_media_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    dealership_id = db.Column(db.Integer, db.ForeignKey('dealerships.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_urls = db.Column(db.Text)  # JSON array of media URLs
    hashtags = db.Column(db.Text)  # JSON array of hashtags
    scheduled_time = db.Column(db.DateTime)
    posted_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, posted, failed
    post_id = db.Column(db.String(100))  # Platform-specific post ID
    engagement_data = db.Column(db.Text)  # JSON object with likes, comments, shares
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dealership = db.relationship('Dealership', backref='social_posts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'dealership_id': self.dealership_id,
            'platform': self.platform,
            'content': self.content,
            'media_urls': self.media_urls,
            'hashtags': self.hashtags,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'posted_time': self.posted_time.isoformat() if self.posted_time else None,
            'status': self.status,
            'post_id': self.post_id,
            'engagement_data': self.engagement_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Alias for backward compatibility
Post = SocialMediaPost

