from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail
import logging

def send_verification_email(user, token):
    """Send email verification email to user"""
    try:
        verification_url = url_for('auth.verify_email', token=token.token, _external=True)
        
        msg = Message(
            subject='Verify Your Email - Mazen Yahia Platform',
            recipients=[user.email],
            html=render_template('emails/verification.html', 
                               user=user, 
                               verification_url=verification_url),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logging.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_welcome_email(user):
    """Send welcome email after successful verification"""
    try:
        msg = Message(
            subject='Welcome to Mazen Yahia Platform!',
            recipients=[user.email],
            html=render_template('emails/welcome.html', user=user),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logging.info(f"Welcome email sent to {user.email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_token):
    """Send password reset email"""
    try:
        reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
        
        msg = Message(
            subject='Password Reset - Mazen Yahia Platform',
            recipients=[user.email],
            html=render_template('emails/password_reset.html', 
                               user=user, 
                               reset_url=reset_url),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logging.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def send_project_notification_email(user, project, notification_type):
    """Send project-related notification emails"""
    try:
        subject_map = {
            'project_created': 'New Project Created',
            'project_updated': 'Project Updated',
            'milestone_completed': 'Milestone Completed',
            'payment_received': 'Payment Received'
        }
        
        msg = Message(
            subject=f"{subject_map.get(notification_type, 'Project Notification')} - {project.title}",
            recipients=[user.email],
            html=render_template('emails/project_notification.html', 
                               user=user, 
                               project=project,
                               notification_type=notification_type),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logging.info(f"Project notification email sent to {user.email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send project notification email to {user.email}: {str(e)}")
        return False
