from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.user import User
from src.models.dealership import Dealership, SocialMediaAccount, ContentTemplate, Post
from src.extensions import db

dealership_bp = Blueprint('dealership', __name__)

@dealership_bp.route('/dealerships', methods=['GET'])
def get_dealerships():
    """Get all dealerships"""
    dealerships = Dealership.query.all()
    return jsonify([dealership.to_dict() for dealership in dealerships])

@dealership_bp.route('/dealerships', methods=['POST'])
def create_dealership():
    """Create a new dealership"""
    data = request.json
    
    # Set trial end date to 30 days from now
    trial_end = datetime.utcnow() + timedelta(days=30)
    
    dealership = Dealership(
        name=data['name'],
        address=data.get('address'),
        phone=data.get('phone'),
        website=data.get('website'),
        subscription_plan=data.get('subscription_plan', 'starter'),
        trial_end_date=trial_end,
        brand_color=data.get('brand_color', '#1a73e8'),
        inventory_feed_url=data.get('inventory_feed_url'),
        dms_type=data.get('dms_type')
    )
    
    db.session.add(dealership)
    db.session.commit()
    return jsonify(dealership.to_dict()), 201

@dealership_bp.route('/dealerships/<int:dealership_id>', methods=['GET'])
def get_dealership(dealership_id):
    """Get a specific dealership"""
    dealership = Dealership.query.get_or_404(dealership_id)
    return jsonify(dealership.to_dict())

@dealership_bp.route('/dealerships/<int:dealership_id>', methods=['PUT'])
def update_dealership(dealership_id):
    """Update a dealership"""
    dealership = Dealership.query.get_or_404(dealership_id)
    data = request.json
    
    dealership.name = data.get('name', dealership.name)
    dealership.address = data.get('address', dealership.address)
    dealership.phone = data.get('phone', dealership.phone)
    dealership.website = data.get('website', dealership.website)
    dealership.subscription_plan = data.get('subscription_plan', dealership.subscription_plan)
    dealership.brand_color = data.get('brand_color', dealership.brand_color)
    dealership.logo_url = data.get('logo_url', dealership.logo_url)
    dealership.inventory_feed_url = data.get('inventory_feed_url', dealership.inventory_feed_url)
    dealership.dms_type = data.get('dms_type', dealership.dms_type)
    
    db.session.commit()
    return jsonify(dealership.to_dict())

@dealership_bp.route('/dealerships/<int:dealership_id>/social-accounts', methods=['GET'])
def get_social_accounts(dealership_id):
    """Get all social media accounts for a dealership"""
    accounts = SocialMediaAccount.query.filter_by(dealership_id=dealership_id).all()
    return jsonify([account.to_dict() for account in accounts])

@dealership_bp.route('/dealerships/<int:dealership_id>/social-accounts', methods=['POST'])
def create_social_account(dealership_id):
    """Connect a new social media account"""
    data = request.json
    
    account = SocialMediaAccount(
        dealership_id=dealership_id,
        platform=data['platform'],
        account_id=data['account_id'],
        account_name=data.get('account_name'),
        access_token=data.get('access_token'),  # Should be encrypted in production
        page_id=data.get('page_id'),
        business_account_id=data.get('business_account_id'),
        posting_frequency=data.get('posting_frequency', 1),
        optimal_posting_times=data.get('optimal_posting_times', '["09:00", "12:00", "17:00"]')
    )
    
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201

@dealership_bp.route('/social-accounts/<int:account_id>', methods=['PUT'])
def update_social_account(account_id):
    """Update social media account settings"""
    account = SocialMediaAccount.query.get_or_404(account_id)
    data = request.json
    
    account.is_active = data.get('is_active', account.is_active)
    account.posting_frequency = data.get('posting_frequency', account.posting_frequency)
    account.optimal_posting_times = data.get('optimal_posting_times', account.optimal_posting_times)
    
    db.session.commit()
    return jsonify(account.to_dict())

@dealership_bp.route('/social-accounts/<int:account_id>', methods=['DELETE'])
def delete_social_account(account_id):
    """Disconnect a social media account"""
    account = SocialMediaAccount.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    return '', 204

@dealership_bp.route('/dealerships/<int:dealership_id>/posts', methods=['GET'])
def get_posts(dealership_id):
    """Get all posts for a dealership"""
    posts = Post.query.filter_by(dealership_id=dealership_id).order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

@dealership_bp.route('/dealerships/<int:dealership_id>/analytics', methods=['GET'])
def get_analytics(dealership_id):
    """Get analytics for a dealership"""
    # Get posts from the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    posts = Post.query.filter(
        Post.dealership_id == dealership_id,
        Post.posted_at >= thirty_days_ago,
        Post.status == 'posted'
    ).all()
    
    # Calculate analytics
    total_posts = len(posts)
    total_likes = sum(post.likes_count for post in posts)
    total_comments = sum(post.comments_count for post in posts)
    total_shares = sum(post.shares_count for post in posts)
    total_reach = sum(post.reach for post in posts)
    total_impressions = sum(post.impressions for post in posts)
    
    # Platform breakdown
    platform_stats = {}
    for post in posts:
        platform = post.social_account.platform
        if platform not in platform_stats:
            platform_stats[platform] = {
                'posts': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'reach': 0,
                'impressions': 0
            }
        platform_stats[platform]['posts'] += 1
        platform_stats[platform]['likes'] += post.likes_count
        platform_stats[platform]['comments'] += post.comments_count
        platform_stats[platform]['shares'] += post.shares_count
        platform_stats[platform]['reach'] += post.reach
        platform_stats[platform]['impressions'] += post.impressions
    
    return jsonify({
        'period': '30_days',
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_reach': total_reach,
        'total_impressions': total_impressions,
        'engagement_rate': round((total_likes + total_comments + total_shares) / max(total_impressions, 1) * 100, 2),
        'platform_breakdown': platform_stats
    })

