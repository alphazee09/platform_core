from flask import Blueprint, request, jsonify, redirect, url_for, current_app
import requests
import os
from app import db
from models import Payment, User, Project, Contract, Milestone, PaymentStatus
from datetime import datetime

payment_bp = Blueprint('payment', __name__)

THAWANI_API_KEY = os.environ.get('THAWANI_API_KEY')
THAWANI_MERCHANT_CODE = os.environ.get('THAWANI_MERCHANT_CODE')
THAWANI_SUCCESS_URL = os.environ.get('THAWANI_SUCCESS_URL')
THAWANI_CANCEL_URL = os.environ.get('THAWANI_CANCEL_URL')
THAWANI_WEBHOOK_URL = os.environ.get('THAWANI_WEBHOOK_URL')

THAWANI_API_BASE_URL = "https://uatcheckout.thawani.om/api/v1"

@payment_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    amount = data.get('amount')
    description = data.get('description')
    user_id = data.get('user_id')
    project_id = data.get('project_id')
    contract_id = data.get('contract_id')
    milestone_id = data.get('milestone_id')

    if not all([amount, description, user_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create a new payment record in your database
    new_payment = Payment(
        amount=amount,
        currency='OMR',
        description=description,
        user_id=user_id,
        project_id=project_id,
        contract_id=contract_id,
        milestone_id=milestone_id,
        status=PaymentStatus.PENDING
    )
    db.session.add(new_payment)
    db.session.commit()

    headers = {
        'Content-Type': 'application/json',
        'thawani-api-key': THAWANI_API_KEY
    }

    payload = {
        "client_reference_id": str(new_payment.id),
        "products": [
            {
                "name": description,
                "quantity": 1,
                "unit_amount": int(amount * 100)  # Amount in cents
            }
        ],
        "success_url": THAWANI_SUCCESS_URL,
        "cancel_url": THAWANI_CANCEL_URL,
        "metadata": {
            "payment_id": new_payment.id,
            "user_id": user_id
        }
    }

    try:
        response = requests.post(f"{THAWANI_API_BASE_URL}/checkout/session", headers=headers, json=payload)
        response.raise_for_status()
        checkout_data = response.json()

        if checkout_data.get('success') and checkout_data.get('data', {}).get('session_id'):
            new_payment.stripe_session_id = checkout_data['data']['session_id'] # Reusing stripe_session_id for Thawani session_id
            db.session.commit()
            return jsonify({'session_id': checkout_data['data']['session_id'], 'checkout_url': checkout_data['data']['checkout_url']})
        else:
            current_app.logger.error(f"Thawani checkout session creation failed: {checkout_data.get('description')}")
            return jsonify({'error': checkout_data.get('description', 'Failed to create Thawani checkout session')}), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request to Thawani API failed: {e}")
        return jsonify({'error': 'Failed to connect to payment gateway'}), 500

@payment_bp.route('/payment/success', methods=['GET'])
def payment_success():
    session_id = request.args.get('session_id')
    payment = Payment.query.filter_by(stripe_session_id=session_id).first()
    if payment:
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Payment successful', 'payment_id': payment.id})
    return jsonify({'error': 'Payment not found'}), 404

@payment_bp.route('/payment/cancel', methods=['GET'])
def payment_cancel():
    session_id = request.args.get('session_id')
    payment = Payment.query.filter_by(stripe_session_id=session_id).first()
    if payment:
        payment.status = PaymentStatus.FAILED
        db.session.commit()
        return jsonify({'message': 'Payment cancelled', 'payment_id': payment.id})
    return jsonify({'error': 'Payment not found'}), 404

@payment_bp.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    data = request.get_json()
    event_type = data.get('event_type')
    session_id = data.get('data', {}).get('session_id')

    if event_type == 'checkout.success' and session_id:
        payment = Payment.query.filter_by(stripe_session_id=session_id).first()
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.paid_at = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(f"Webhook: Payment {payment.id} updated to COMPLETED.")
            return jsonify({'status': 'success'}), 200
    
    current_app.logger.warning(f"Webhook: Unhandled event type {event_type} or missing session_id.")
    return jsonify({'status': 'ignored'}), 200




@payment_bp.route('/payment/checkout')
def payment_checkout():
    from flask import render_template
    amount = request.args.get('amount', '0.00')
    description = request.args.get('description', 'Payment for services')
    project_id = request.args.get('project_id')
    contract_id = request.args.get('contract_id')
    milestone_id = request.args.get('milestone_id')
    
    return render_template('payment_checkout.html', 
                         amount=amount, 
                         description=description,
                         project_id=project_id,
                         contract_id=contract_id,
                         milestone_id=milestone_id)

@payment_bp.route('/payment/success')
def payment_success_page():
    from flask import render_template
    session_id = request.args.get('session_id')
    payment = None
    if session_id:
        payment = Payment.query.filter_by(stripe_session_id=session_id).first()
    return render_template('payment_success.html', payment=payment)

@payment_bp.route('/payment/cancel')
def payment_cancel_page():
    from flask import render_template
    return render_template('payment_cancel.html')

