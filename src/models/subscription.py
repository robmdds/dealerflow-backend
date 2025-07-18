"""
Subscription and Payment Models for DealerFlow Pro
Handles subscription plans, billing, and payment processing
"""

from datetime import datetime, timedelta
from enum import Enum
import uuid

class SubscriptionPlan(Enum):
    """Available subscription plans"""
    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    """Subscription status options"""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentStatus(Enum):
    """Payment status options"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Subscription:
    """Subscription model for managing customer subscriptions"""
    
    def __init__(self, subscription_id=None, user_id=None, plan=SubscriptionPlan.TRIAL,
                 status=SubscriptionStatus.TRIAL, amount=0.0, billing_cycle='monthly',
                 current_period_start=None, current_period_end=None, 
                 trial_end=None, created_at=None, updated_at=None,
                 helcim_customer_id=None, helcim_subscription_id=None):
        self.subscription_id = subscription_id or str(uuid.uuid4())
        self.user_id = user_id
        self.plan = plan if isinstance(plan, SubscriptionPlan) else SubscriptionPlan(plan)
        self.status = status if isinstance(status, SubscriptionStatus) else SubscriptionStatus(status)
        self.amount = amount
        self.billing_cycle = billing_cycle  # 'monthly' or 'yearly'
        self.current_period_start = current_period_start or datetime.utcnow()
        self.current_period_end = current_period_end or self._calculate_period_end()
        self.trial_end = trial_end or (datetime.utcnow() + timedelta(days=14))
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.helcim_customer_id = helcim_customer_id
        self.helcim_subscription_id = helcim_subscription_id
    
    def _calculate_period_end(self):
        """Calculate the end of the current billing period"""
        if self.billing_cycle == 'yearly':
            return self.current_period_start + timedelta(days=365)
        else:  # monthly
            return self.current_period_start + timedelta(days=30)
    
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status == SubscriptionStatus.TRIAL:
            return datetime.utcnow() <= self.trial_end
        return self.status == SubscriptionStatus.ACTIVE and datetime.utcnow() <= self.current_period_end
    
    def days_until_renewal(self):
        """Get days until next renewal"""
        if self.status == SubscriptionStatus.TRIAL:
            return max(0, (self.trial_end - datetime.utcnow()).days)
        return max(0, (self.current_period_end - datetime.utcnow()).days)
    
    def get_plan_features(self):
        """Get features available for the current plan"""
        features = {
            SubscriptionPlan.TRIAL: {
                'max_posts_per_month': 50,
                'max_images': 100,
                'platforms': ['facebook', 'instagram'],
                'automation': False,
                'analytics': False,
                'support': 'email',
                'price_monthly': 0,
                'price_yearly': 0
            },
            SubscriptionPlan.STARTER: {
                'max_posts_per_month': 200,
                'max_images': 500,
                'platforms': ['facebook', 'instagram', 'x'],
                'automation': True,
                'analytics': True,
                'support': 'email',
                'price_monthly': 197,
                'price_yearly': 1970  # 2 months free
            },
            SubscriptionPlan.PROFESSIONAL: {
                'max_posts_per_month': 1000,
                'max_images': 2000,
                'platforms': ['facebook', 'instagram', 'x', 'tiktok', 'reddit'],
                'automation': True,
                'analytics': True,
                'support': 'priority',
                'price_monthly': 397,
                'price_yearly': 3970  # 2 months free
            },
            SubscriptionPlan.ENTERPRISE: {
                'max_posts_per_month': -1,  # Unlimited
                'max_images': -1,  # Unlimited
                'platforms': ['facebook', 'instagram', 'x', 'tiktok', 'reddit', 'youtube'],
                'automation': True,
                'analytics': True,
                'support': 'phone',
                'price_monthly': 597,
                'price_yearly': 5970  # 2 months free
            }
        }
        return features.get(self.plan, features[SubscriptionPlan.TRIAL])
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'plan': self.plan.value,
            'status': self.status.value,
            'amount': self.amount,
            'billing_cycle': self.billing_cycle,
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active(),
            'days_until_renewal': self.days_until_renewal(),
            'features': self.get_plan_features(),
            'helcim_customer_id': self.helcim_customer_id,
            'helcim_subscription_id': self.helcim_subscription_id
        }

class Payment:
    """Payment model for tracking payment transactions"""
    
    def __init__(self, payment_id=None, user_id=None, subscription_id=None,
                 amount=0.0, currency='USD', status=PaymentStatus.PENDING,
                 payment_method=None, helcim_transaction_id=None,
                 description=None, created_at=None, processed_at=None,
                 failure_reason=None):
        self.payment_id = payment_id or str(uuid.uuid4())
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.amount = amount
        self.currency = currency
        self.status = status if isinstance(status, PaymentStatus) else PaymentStatus(status)
        self.payment_method = payment_method
        self.helcim_transaction_id = helcim_transaction_id
        self.description = description
        self.created_at = created_at or datetime.utcnow()
        self.processed_at = processed_at
        self.failure_reason = failure_reason
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'payment_id': self.payment_id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'payment_method': self.payment_method,
            'helcim_transaction_id': self.helcim_transaction_id,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'failure_reason': self.failure_reason
        }

class SubscriptionService:
    """Service for managing subscriptions and payments"""
    
    def __init__(self):
        # In-memory storage for demo (replace with database in production)
        self.subscriptions = {}
        self.payments = {}
        self.subscription_counter = 1
        self.payment_counter = 1
    
    def create_subscription(self, user_id, plan=SubscriptionPlan.TRIAL):
        """Create a new subscription for a user"""
        subscription = Subscription(
            subscription_id=self.subscription_counter,
            user_id=user_id,
            plan=plan,
            status=SubscriptionStatus.TRIAL if plan == SubscriptionPlan.TRIAL else SubscriptionStatus.ACTIVE
        )
        
        self.subscriptions[self.subscription_counter] = subscription
        self.subscription_counter += 1
        
        return subscription
    
    def get_subscription_by_user(self, user_id):
        """Get active subscription for a user"""
        for subscription in self.subscriptions.values():
            if subscription.user_id == user_id:
                return subscription
        return None
    
    def upgrade_subscription(self, user_id, new_plan, billing_cycle='monthly'):
        """Upgrade user's subscription plan"""
        subscription = self.get_subscription_by_user(user_id)
        if not subscription:
            return None, "No subscription found"
        
        # Calculate new amount based on plan and billing cycle
        features = subscription.get_plan_features()
        if billing_cycle == 'yearly':
            amount = features['price_yearly']
        else:
            amount = features['price_monthly']
        
        # Update subscription
        subscription.plan = new_plan if isinstance(new_plan, SubscriptionPlan) else SubscriptionPlan(new_plan)
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.amount = amount
        subscription.billing_cycle = billing_cycle
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = subscription._calculate_period_end()
        subscription.updated_at = datetime.utcnow()
        
        return subscription, None
    
    def cancel_subscription(self, user_id):
        """Cancel user's subscription"""
        subscription = self.get_subscription_by_user(user_id)
        if not subscription:
            return None, "No subscription found"
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.updated_at = datetime.utcnow()
        
        return subscription, None
    
    def create_payment(self, user_id, subscription_id, amount, description=None):
        """Create a new payment record"""
        payment = Payment(
            payment_id=self.payment_counter,
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            description=description
        )
        
        self.payments[self.payment_counter] = payment
        self.payment_counter += 1
        
        return payment
    
    def process_payment(self, payment_id, helcim_transaction_id=None, success=True, failure_reason=None):
        """Process a payment (simulate Helcim response)"""
        payment = self.payments.get(payment_id)
        if not payment:
            return None, "Payment not found"
        
        if success:
            payment.status = PaymentStatus.COMPLETED
            payment.helcim_transaction_id = helcim_transaction_id
            payment.processed_at = datetime.utcnow()
            
            # Update subscription if payment successful
            subscription = self.subscriptions.get(payment.subscription_id)
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.updated_at = datetime.utcnow()
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = failure_reason
            payment.processed_at = datetime.utcnow()
        
        return payment, None
    
    def get_payments_by_user(self, user_id):
        """Get all payments for a user"""
        return [payment for payment in self.payments.values() if payment.user_id == user_id]
    
    def get_subscription_plans(self):
        """Get all available subscription plans with pricing"""
        plans = {}
        for plan in SubscriptionPlan:
            if plan != SubscriptionPlan.TRIAL:
                temp_subscription = Subscription(plan=plan)
                features = temp_subscription.get_plan_features()
                plans[plan.value] = {
                    'name': plan.value.title(),
                    'features': features,
                    'recommended': plan == SubscriptionPlan.PROFESSIONAL
                }
        return plans
    
    def check_feature_access(self, user_id, feature):
        """Check if user has access to a specific feature"""
        subscription = self.get_subscription_by_user(user_id)
        if not subscription or not subscription.is_active():
            return False
        
        features = subscription.get_plan_features()
        return features.get(feature, False)
    
    def get_usage_stats(self, user_id):
        """Get usage statistics for a user (placeholder for real implementation)"""
        return {
            'posts_this_month': 23,
            'images_used': 45,
            'automation_runs': 12,
            'last_post_date': datetime.utcnow().isoformat()
        }

# Global subscription service instance
subscription_service = SubscriptionService()

