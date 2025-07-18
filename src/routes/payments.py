"""
Payment and Subscription Routes for DealerFlow Pro
Handles subscription management and Helcim payment processing
"""

from flask import Blueprint, request, jsonify
import requests
import os
from models.user import user_service
from models.subscription import subscription_service, SubscriptionPlan, SubscriptionStatus
from routes.auth import require_auth

payments_bp = Blueprint('payments', __name__)

# Helcim API configuration
HELCIM_API_URL = "https://api.helcim.com/v2"
HELCIM_API_TOKEN = os.getenv('HELCIM_API_TOKEN', 'demo-token-for-testing')

class HelcimService:
    """Service for Helcim payment processing"""
    
    @staticmethod
    def create_customer(user_data):
        """Create a customer in Helcim"""
        try:
            # In demo mode, simulate Helcim customer creation
            if HELCIM_API_TOKEN == 'demo-token-for-testing':
                return {
                    'success': True,
                    'customer_id': f"helcim_customer_{user_data['user_id']}",
                    'customer_code': f"DEALER{user_data['user_id']:04d}"
                }
            
            # Real Helcim API call (when API token is configured)
            headers = {
                'Authorization': f'Bearer {HELCIM_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'customerCode': f"DEALER{user_data['user_id']:04d}",
                'contactName': user_data['contact_name'],
                'businessName': user_data['dealership_name'],
                'email': user_data['email'],
                'phone': user_data.get('phone', ''),
                'currency': 'USD'
            }
            
            response = requests.post(
                f"{HELCIM_API_URL}/customers",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'customer_id': data['customerId'],
                    'customer_code': data['customerCode']
                }
            else:
                return {
                    'success': False,
                    'error': f"Helcim API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create Helcim customer: {str(e)}"
            }
    
    @staticmethod
    def create_payment_intent(amount, currency='USD', customer_id=None, description=None):
        """Create a payment intent in Helcim"""
        try:
            # In demo mode, simulate payment intent creation
            if HELCIM_API_TOKEN == 'demo-token-for-testing':
                return {
                    'success': True,
                    'payment_intent_id': f"pi_demo_{amount}_{currency}",
                    'client_secret': f"pi_demo_{amount}_{currency}_secret",
                    'amount': amount,
                    'currency': currency
                }
            
            # Real Helcim API call (when API token is configured)
            headers = {
                'Authorization': f'Bearer {HELCIM_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'amount': amount,
                'currency': currency,
                'customerId': customer_id,
                'description': description or 'DealerFlow Pro Subscription'
            }
            
            response = requests.post(
                f"{HELCIM_API_URL}/payment-intents",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'payment_intent_id': data['id'],
                    'client_secret': data['clientSecret'],
                    'amount': data['amount'],
                    'currency': data['currency']
                }
            else:
                return {
                    'success': False,
                    'error': f"Helcim API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create payment intent: {str(e)}"
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id, payment_method_id):
        """Confirm a payment in Helcim"""
        try:
            # In demo mode, simulate payment confirmation
            if HELCIM_API_TOKEN == 'demo-token-for-testing':
                return {
                    'success': True,
                    'transaction_id': f"txn_demo_{payment_intent_id}",
                    'status': 'completed',
                    'amount': 197.00,
                    'currency': 'USD'
                }
            
            # Real Helcim API call (when API token is configured)
            headers = {
                'Authorization': f'Bearer {HELCIM_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'paymentMethodId': payment_method_id
            }
            
            response = requests.post(
                f"{HELCIM_API_URL}/payment-intents/{payment_intent_id}/confirm",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'transaction_id': data['transactionId'],
                    'status': data['status'],
                    'amount': data['amount'],
                    'currency': data['currency']
                }
            else:
                return {
                    'success': False,
                    'error': f"Helcim API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to confirm payment: {str(e)}"
            }

@payments_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = subscription_service.get_subscription_plans()
        
        return jsonify({
            'success': True,
            'plans': plans
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get plans: {str(e)}'
        }), 500

@payments_bp.route('/subscription', methods=['GET'])
@require_auth
def get_current_subscription():
    """Get current user's subscription"""
    try:
        user = request.current_user
        subscription = subscription_service.get_subscription_by_user(user.user_id)
        
        if not subscription:
            # Create trial subscription if none exists
            subscription = subscription_service.create_subscription(user.user_id)
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'usage': subscription_service.get_usage_stats(user.user_id)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get subscription: {str(e)}'
        }), 500

@payments_bp.route('/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """Upgrade user's subscription plan"""
    try:
        user = request.current_user
        data = request.get_json()
        
        plan = data.get('plan')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not plan:
            return jsonify({
                'success': False,
                'error': 'Plan is required'
            }), 400
        
        # Validate plan
        try:
            plan_enum = SubscriptionPlan(plan)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid plan'
            }), 400
        
        # Get or create subscription
        subscription = subscription_service.get_subscription_by_user(user.user_id)
        if not subscription:
            subscription = subscription_service.create_subscription(user.user_id)
        
        # Calculate amount
        temp_subscription = subscription_service.subscriptions[subscription.subscription_id]
        temp_subscription.plan = plan_enum
        features = temp_subscription.get_plan_features()
        amount = features['price_yearly'] if billing_cycle == 'yearly' else features['price_monthly']
        
        if amount == 0:
            return jsonify({
                'success': False,
                'error': 'Cannot upgrade to free plan'
            }), 400
        
        # Create Helcim customer if needed
        if not user.to_dict().get('helcim_customer_id'):
            helcim_result = HelcimService.create_customer(user.to_dict())
            if not helcim_result['success']:
                return jsonify({
                    'success': False,
                    'error': f"Payment setup failed: {helcim_result['error']}"
                }), 500
        
        # Create payment intent
        payment_intent = HelcimService.create_payment_intent(
            amount=amount,
            customer_id=user.to_dict().get('helcim_customer_id'),
            description=f"DealerFlow Pro {plan.title()} Plan ({billing_cycle})"
        )
        
        if not payment_intent['success']:
            return jsonify({
                'success': False,
                'error': f"Payment setup failed: {payment_intent['error']}"
            }), 500
        
        # Create payment record
        payment = subscription_service.create_payment(
            user_id=user.user_id,
            subscription_id=subscription.subscription_id,
            amount=amount,
            description=f"Upgrade to {plan.title()} plan"
        )
        
        return jsonify({
            'success': True,
            'payment_intent': {
                'id': payment_intent['payment_intent_id'],
                'client_secret': payment_intent['client_secret'],
                'amount': payment_intent['amount'],
                'currency': payment_intent['currency']
            },
            'payment_id': payment.payment_id,
            'plan': plan,
            'billing_cycle': billing_cycle
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to upgrade subscription: {str(e)}'
        }), 500

@payments_bp.route('/payment/confirm', methods=['POST'])
@require_auth
def confirm_payment():
    """Confirm payment and activate subscription"""
    try:
        user = request.current_user
        data = request.get_json()
        
        payment_intent_id = data.get('payment_intent_id')
        payment_method_id = data.get('payment_method_id')
        payment_id = data.get('payment_id')
        plan = data.get('plan')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not all([payment_intent_id, payment_method_id, payment_id, plan]):
            return jsonify({
                'success': False,
                'error': 'Missing required payment information'
            }), 400
        
        # Confirm payment with Helcim
        payment_result = HelcimService.confirm_payment(payment_intent_id, payment_method_id)
        
        if not payment_result['success']:
            # Mark payment as failed
            subscription_service.process_payment(
                payment_id,
                success=False,
                failure_reason=payment_result['error']
            )
            
            return jsonify({
                'success': False,
                'error': f"Payment failed: {payment_result['error']}"
            }), 400
        
        # Mark payment as successful
        payment, _ = subscription_service.process_payment(
            payment_id,
            helcim_transaction_id=payment_result['transaction_id'],
            success=True
        )
        
        # Upgrade subscription
        subscription, error = subscription_service.upgrade_subscription(
            user.user_id,
            plan,
            billing_cycle
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Payment successful and subscription upgraded',
            'subscription': subscription.to_dict(),
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to confirm payment: {str(e)}'
        }), 500

@payments_bp.route('/subscription/cancel', methods=['POST'])
@require_auth
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user = request.current_user
        
        subscription, error = subscription_service.cancel_subscription(user.user_id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Subscription cancelled successfully',
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to cancel subscription: {str(e)}'
        }), 500

@payments_bp.route('/payments/history', methods=['GET'])
@require_auth
def get_payment_history():
    """Get user's payment history"""
    try:
        user = request.current_user
        payments = subscription_service.get_payments_by_user(user.user_id)
        
        return jsonify({
            'success': True,
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get payment history: {str(e)}'
        }), 500

@payments_bp.route('/feature-access/<feature>', methods=['GET'])
@require_auth
def check_feature_access(feature):
    """Check if user has access to a specific feature"""
    try:
        user = request.current_user
        has_access = subscription_service.check_feature_access(user.user_id, feature)
        
        return jsonify({
            'success': True,
            'has_access': has_access,
            'feature': feature
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to check feature access: {str(e)}'
        }), 500

@payments_bp.route('/webhook/helcim', methods=['POST'])
def helcim_webhook():
    """Handle Helcim webhook events"""
    try:
        data = request.get_json()
        event_type = data.get('type')
        
        # Handle different webhook events
        if event_type == 'payment.succeeded':
            # Handle successful payment
            transaction_id = data.get('transactionId')
            # Update payment status in database
            pass
        elif event_type == 'payment.failed':
            # Handle failed payment
            transaction_id = data.get('transactionId')
            # Update payment status in database
            pass
        elif event_type == 'subscription.cancelled':
            # Handle subscription cancellation
            subscription_id = data.get('subscriptionId')
            # Update subscription status in database
            pass
        
        return jsonify({
            'success': True,
            'message': 'Webhook processed'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Webhook processing failed: {str(e)}'
        }), 500

