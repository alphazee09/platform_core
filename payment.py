from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import logging

from app import db
from models import Payment, PaymentStatus, Project
from thawani_payment import ThawaniPayment
from utils import log_activity

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create-payment', methods=['POST'])
@login_required
def create_payment():
    """Create a new payment session"""
    
    try:
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency', 'OMR')
        description = request.form.get('description', '')
        project_id = request.form.get('project_id')
        
        if amount <= 0:
            flash('Invalid payment amount.', 'error')
            return redirect(url_for('user.payments'))
        
        # Create payment record
        payment = Payment(
            amount=amount,
            currency=currency,
            description=description,
            user_id=current_user.id,
            project_id=project_id if project_id and project_id != '0' else None,
            status=PaymentStatus.PENDING
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Create Thawani checkout session
        thawani = ThawaniPayment()
        result = thawani.create_checkout_session(
            amount=amount,
            currency=currency,
            metadata={'payment_id': str(payment.id), 'user_id': str(current_user.id)},
            success_url=url_for('payment.success', payment_id=payment.id, _external=True),
            cancel_url=url_for('payment.cancel', payment_id=payment.id, _external=True)
        )
        
        if result['success']:
            payment.thawani_session_id = result['session_id']
            db.session.commit()
            
            log_activity(current_user.id, 'payment_initiated', 
                        f'User initiated payment of {amount} {currency}')
            
            return redirect(result['session_url'])
        else:
            flash(f'Payment creation failed: {result["error"]}', 'error')
            db.session.delete(payment)
            db.session.commit()
            
    except Exception as e:
        logging.error(f"Payment creation error: {str(e)}")
        flash('An error occurred while processing your payment.', 'error')
    
    return redirect(url_for('user.payments'))

@payment_bp.route('/success/<int:payment_id>')
@login_required
def success(payment_id):
    """Payment success page"""
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify user owns this payment
    if payment.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.payments'))
    
    # Update payment status if not already updated by webhook
    if payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        
        log_activity(current_user.id, 'payment_completed', 
                    f'Payment of {payment.amount} {payment.currency} completed')
    
    return render_template('user/payment_success.html', payment=payment)

@payment_bp.route('/cancel/<int:payment_id>')
@login_required
def cancel(payment_id):
    """Payment cancel page"""
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify user owns this payment
    if payment.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.payments'))
    
    log_activity(current_user.id, 'payment_cancelled', 
                f'Payment of {payment.amount} {payment.currency} was cancelled')
    
    return render_template('user/payment_cancel.html', payment=payment)

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Thawani webhook notifications"""
    
    try:
        payload = request.get_json()
        signature = request.headers.get('thawani-signature')
        
        thawani = ThawaniPayment()
        result = thawani.process_webhook(payload, signature)
        
        if result['success']:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Webhook processing error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Webhook processing failed'}), 500

