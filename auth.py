from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from app import db, login_manager
from models import User, UserRole, ActivityLog
from utils import log_activity, allowed_file

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me', False)
        
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            log_activity(user.id, 'LOGIN', f'User {user.username} logged in')
            
            next_page = request.args.get('next')
            if not next_page:
                if user.role == UserRole.ADMIN:
                    next_page = url_for('main.admin')
                else:
                    next_page = url_for('main.dashboard')
            
            flash('Welcome back!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
            log_activity(None, 'LOGIN_FAILED', f'Failed login attempt for {username}')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        phone = request.form.get('phone', '')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=UserRole.CLIENT
        )
        user.set_password(password)
        
        # Handle file uploads
        if 'id_card' in request.files:
            id_card = request.files['id_card']
            if id_card and allowed_file(id_card.filename):
                filename = secure_filename(f"{username}_id_card_{id_card.filename}")
                id_card_path = os.path.join('uploads', 'documents', filename)
                os.makedirs(os.path.dirname(id_card_path), exist_ok=True)
                id_card.save(id_card_path)
                user.id_card_path = id_card_path
        
        if 'signature' in request.files:
            signature = request.files['signature']
            if signature and allowed_file(signature.filename):
                filename = secure_filename(f"{username}_signature_{signature.filename}")
                signature_path = os.path.join('uploads', 'documents', filename)
                os.makedirs(os.path.dirname(signature_path), exist_ok=True)
                signature.save(signature_path)
                user.signature_path = signature_path
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(user.id, 'REGISTER', f'User {user.username} registered')
        flash('Registration successful! Please wait for account verification.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'LOGOUT', f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        # Handle profile image upload
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            if profile_image and allowed_file(profile_image.filename):
                filename = secure_filename(f"{current_user.username}_profile_{profile_image.filename}")
                profile_path = os.path.join('uploads', 'profiles', filename)
                os.makedirs(os.path.dirname(profile_path), exist_ok=True)
                profile_image.save(profile_path)
                current_user.profile_image = profile_path
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return render_template('profile.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('profile.html')
            
            current_user.set_password(new_password)
            log_activity(current_user.id, 'PASSWORD_CHANGE', 'User changed password')
        
        db.session.commit()
        log_activity(current_user.id, 'PROFILE_UPDATE', 'User updated profile')
        flash('Profile updated successfully', 'success')
    
    return render_template('profile.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Basic password reset functionality
    # In a production environment, you would implement email verification
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token (simplified for demo)
            token = create_access_token(identity=user.id)
            session['reset_token'] = token
            session['reset_user_id'] = user.id
            flash('Password reset instructions sent to your email', 'info')
            return redirect(url_for('auth.reset_password_confirm'))
        else:
            flash('Email not found', 'error')
    
    return render_template('reset_password.html')

@auth_bp.route('/reset-password-confirm', methods=['GET', 'POST'])
def reset_password_confirm():
    if 'reset_token' not in session:
        flash('Invalid reset session', 'error')
        return redirect(url_for('auth.reset_password'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password_confirm.html')
        
        user_id = session.get('reset_user_id')
        user = User.query.get(user_id)
        
        if user:
            user.set_password(new_password)
            db.session.commit()
            
            # Clear reset session
            session.pop('reset_token', None)
            session.pop('reset_user_id', None)
            
            log_activity(user.id, 'PASSWORD_RESET', 'User reset password')
            flash('Password reset successfully', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('reset_password_confirm.html')
