import requests
import json
import logging
from flask import current_app, url_for
from datetime import datetime

class ThawaniPayment:
    def __init__(self):
        self.secret_key = current_app.config['THAWANI_SECRET_KEY']
        self.publishable_key = current_app.config['THAWANI_PUBLISHABLE_KEY']
        self.base_url = current_app.config['THAWANI_BASE_URL']
        self.headers = {
            'Content-Type': 'application/json',
            'thawani-api-key': self.secret_key
        }
    
    def create_checkout_session(self, amount, currency='OMR', metadata={}, success_url=None, cancel_url=None):
        """Create a Thawani checkout session"""
        try:
            # Convert amount to baisa (1 OMR = 1000 baisa)
            amount_baisa = int(float(amount) * 1000)
            
            payload = {
                'client_reference_id': metadata.get('payment_id', ''),
                'mode': 'payment',
                'products': [{
                    'name': 'Project Payment',
                    'unit_amount': amount_baisa,
                    'quantity': 1
                }],
                'success_url': success_url or url_for('main.payment_success', _external=True),
                'cancel_url': cancel_url or url_for('main.payment_cancel', _external=True),
                'metadata': metadata
            }
            
            response = requests.post(
                f"{self.base_url}/checkout/session",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                session_data = response.json()
                logging.info(f"Thawani checkout session created: {session_data['data']['session_id']}")
                return {
                    'success': True,
                    'session_id': session_data['data']['session_id'],
                    'session_url': session_data['data']['session_url']
                }
            else:
                logging.error(f"Thawani session creation failed: {response.text}")
                return {
                    'success': False,
                    'error': response.json().get('description', 'Payment session creation failed')
                }
                
        except Exception as e:
            logging.error(f"Thawani payment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def retrieve_session(self, session_id):
        """Retrieve a Thawani checkout session"""
        try:
            response = requests.get(
                f"{self.base_url}/checkout/session/{session_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()['data']
                }
            else:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
                
        except Exception as e:
            logging.error(f"Thawani session retrieval error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_intent(self, payment_intent_id):
        """Get payment intent details"""
        try:
            response = requests.get(
                f"{self.base_url}/payment_intents/{payment_intent_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()['data']
                }
            else:
                return {
                    'success': False,
                    'error': 'Payment intent not found'
                }
                
        except Exception as e:
            logging.error(f"Thawani payment intent error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook(self, payload, signature):
        """Process Thawani webhook"""
        try:
            # Verify webhook signature if needed
            # Implementation depends on Thawani's webhook signature verification
            
            event_type = payload.get('type')
            data = payload.get('data', {})
            
            if event_type == 'payment_intent.payment_succeeded':
                return self._handle_payment_success(data)
            elif event_type == 'payment_intent.payment_failed':
                return self._handle_payment_failure(data)
            
            return {'success': True, 'processed': False}
            
        except Exception as e:
            logging.error(f"Thawani webhook processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_success(self, data):
        """Handle successful payment webhook"""
        try:
            from models import Payment, PaymentStatus
            from app import db
            
            payment_intent_id = data.get('id')
            metadata = data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            
            if payment_id:
                payment = Payment.query.get(payment_id)
                if payment:
                    payment.status = PaymentStatus.COMPLETED
                    payment.thawani_payment_id = payment_intent_id
                    payment.paid_at = datetime.utcnow()
                    db.session.commit()
                    
                    logging.info(f"Payment {payment_id} marked as completed")
                    return {'success': True, 'processed': True}
            
            return {'success': True, 'processed': False}
            
        except Exception as e:
            logging.error(f"Payment success handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failure(self, data):
        """Handle failed payment webhook"""
        try:
            from models import Payment, PaymentStatus
            from app import db
            
            payment_intent_id = data.get('id')
            metadata = data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            
            if payment_id:
                payment = Payment.query.get(payment_id)
                if payment:
                    payment.status = PaymentStatus.FAILED
                    payment.thawani_payment_id = payment_intent_id
                    db.session.commit()
                    
                    logging.info(f"Payment {payment_id} marked as failed")
                    return {'success': True, 'processed': True}
            
            return {'success': True, 'processed': False}
            
        except Exception as e:
            logging.error(f"Payment failure handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
