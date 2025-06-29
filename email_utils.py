import os
import logging
from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail

def send_email(to, subject, template, **kwargs):
    """
    Send email using Flask-Mail with error handling
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=template,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        logging.info(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to}: {str(e)}")
        return False

def send_verification_email(user, token):
    """
    Send email verification email to user
    """
    try:
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        
        html_content = render_template('email/verification.html', 
                                     user=user, 
                                     verification_url=verification_url)
        
        subject = "Verify Your Email Address - Platform Core"
        
        return send_email(
            to=user.email,
            subject=subject,
            template=html_content
        )
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        return False

def send_welcome_email(user):
    """
    Send welcome email after successful verification
    """
    try:
        dashboard_url = url_for('user.dashboard', _external=True)
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #ffffff;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">Welcome to Platform Core!</h1>
            </div>
            <div style="padding: 40px 20px;">
                <h2 style="color: #667eea;">Hello {user.get_full_name()},</h2>
                <p style="font-size: 16px; line-height: 1.6;">
                    Welcome to Platform Core! Your email has been successfully verified and your account is now active.
                </p>
                <p style="font-size: 16px; line-height: 1.6;">
                    You can now access all features of our platform including:
                </p>
                <ul style="font-size: 14px; line-height: 1.8;">
                    <li>Project management and tracking</li>
                    <li>Secure payment processing</li>
                    <li>Contract management</li>
                    <li>Direct communication with our team</li>
                    <li>Real-time project updates</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Your Dashboard</a>
                </div>
                <p style="font-size: 14px; color: #888; margin-top: 30px;">
                    If you have any questions, feel free to contact our support team.
                </p>
            </div>
            <div style="background: #111; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>&copy; 2025 Platform Core. All rights reserved.</p>
                <p>Mazin Yahia - Software Engineering Platform</p>
            </div>
        </div>
        """
        
        return send_email(
            to=user.email,
            subject="Welcome to Platform Core - Account Activated!",
            template=html_content
        )
    except Exception as e:
        logging.error(f"Failed to send welcome email: {str(e)}")
        return False

def send_password_reset_email(user, token):
    """
    Send password reset email
    """
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #ffffff;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">Password Reset Request</h1>
            </div>
            <div style="padding: 40px 20px;">
                <h2 style="color: #667eea;">Hello {user.get_full_name()},</h2>
                <p style="font-size: 16px; line-height: 1.6;">
                    You have requested to reset your password. Click the button below to create a new password.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
                </div>
                <p style="font-size: 14px; color: #888;">
                    This link will expire in 24 hours. If you didn't request this reset, please ignore this email.
                </p>
            </div>
            <div style="background: #111; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>&copy; 2025 Platform Core. All rights reserved.</p>
            </div>
        </div>
        """
        
        return send_email(
            to=user.email,
            subject="Reset Your Password - Platform Core",
            template=html_content
        )
    except Exception as e:
        logging.error(f"Failed to send password reset email: {str(e)}")
        return False

def send_project_notification_email(user, project, message_type, **kwargs):
    """
    Send project-related notification emails
    """
    try:
        templates = {
            'status_update': f"""
                <h2>Project Status Update</h2>
                <p>Your project "{project.title}" status has been updated to: <strong>{project.status.value}</strong></p>
                <p>Progress: {project.get_completion_percentage()}%</p>
            """,
            'milestone_completed': f"""
                <h2>Milestone Completed</h2>
                <p>A milestone has been completed for your project "{project.title}"</p>
                <p>Milestone: {kwargs.get('milestone_title', 'N/A')}</p>
            """,
            'payment_received': f"""
                <h2>Payment Received</h2>
                <p>We have received your payment for project "{project.title}"</p>
                <p>Amount: ${kwargs.get('amount', 0):.2f}</p>
            """
        }
        
        project_url = url_for('user.project_detail', id=project.id, _external=True)
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #ffffff;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">Project Update</h1>
            </div>
            <div style="padding: 40px 20px;">
                <h2 style="color: #667eea;">Hello {user.get_full_name()},</h2>
                {templates.get(message_type, '<p>You have a new project update.</p>')}
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{project_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">View Project</a>
                </div>
            </div>
            <div style="background: #111; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>&copy; 2025 Platform Core. All rights reserved.</p>
            </div>
        </div>
        """
        
        return send_email(
            to=user.email,
            subject=f"Project Update: {project.title}",
            template=html_content
        )
    except Exception as e:
        logging.error(f"Failed to send project notification email: {str(e)}")
        return False
