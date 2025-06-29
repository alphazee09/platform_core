from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import os
from datetime import datetime

from app import db
from models import User, UserRole, EmailVerificationToken, ActivityLog
from email_service import send_verification_email, send_welcome_email
from forms import LoginForm, RegisterForm, ProfileForm
from utils import log_activity, allowed_file, save_uploaded_file

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Check if user exists by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_email_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.resend_verification', email=user.email))
            
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_activity(user.id, 'login', f'User {user.username} logged in')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user role
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            company=form.company.data,
            role=UserRole.CLIENT,
            is_verified=False,
            is_email_verified=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create email verification token
        token = EmailVerificationToken.create_for_user(user.id)
        
        # Send verification email
        if send_verification_email(user, token):
            flash('Registration successful! Please check your email to verify your account.', 'success')
            log_activity(user.id, 'register', f'User {user.username} registered')
        else:
            flash('Registration successful, but verification email could not be sent. Please contact support.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    verification_token = EmailVerificationToken.query.filter_by(token=token, is_used=False).first()
    
    if not verification_token:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    if verification_token.is_expired():
        flash('Verification link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.resend_verification', email=verification_token.user.email))
    
    # Verify the user
    user = verification_token.user
    user.is_email_verified = True
    user.is_active = True
    verification_token.is_used = True
    
    db.session.commit()
    
    # Send welcome email
    send_welcome_email(user)
    
    log_activity(user.id, 'email_verified', f'User {user.username} verified email')
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification')
def resend_verification():
    email = request.args.get('email')
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.is_email_verified:
        flash('Email is already verified.', 'info')
        return redirect(url_for('auth.login'))
    
    # Create new verification token
    token = EmailVerificationToken.create_for_user(user.id)
    
    if send_verification_email(user, token):
        flash('Verification email sent successfully! Please check your inbox.', 'success')
    else:
        flash('Failed to send verification email. Please try again later.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email is being changed and if it's already in use
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already in use by another account.', 'error')
                return render_template('auth/profile.html', form=form)
            
            # If email is changed, require re-verification
            current_user.is_email_verified = False
            current_user.email = form.email.data
            
            # Create new verification token
            token = EmailVerificationToken.create_for_user(current_user.id)
            send_verification_email(current_user, token)
            
            flash('Email updated. Please check your new email address for verification.', 'warning')
        
        # Update user information
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.company = form.company.data
        current_user.bio = form.bio.data
        current_user.address = form.address.data
        
        # Handle profile image upload
        if form.profile_image.data:
            filename = save_uploaded_file(form.profile_image.data, 'profiles')
            if filename:
                current_user.profile_image = filename
        
        db.session.commit()
        log_activity(current_user.id, 'profile_updated', 'User updated profile information')
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout', f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real implementation, you would create a password reset token
            # and send it via email. For now, we'll just show a success message
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        else:
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        
        log_activity(current_user.id, 'password_changed', 'User changed password')
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')
