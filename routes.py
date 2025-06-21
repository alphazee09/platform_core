from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import stripe
from datetime import datetime
from app import app, db
from models import *
from utils import admin_required, log_activity, allowed_file

# Configure Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect(url_for('main.admin'))
        else:
            return redirect(url_for('main.dashboard'))
    
    # Get featured blog posts and GitHub repos for landing page
    featured_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    featured_repos = GitHubRepo.query.filter_by(is_featured=True).order_by(GitHubRepo.updated_at.desc()).limit(6).all()
    
    return render_template('index.html', featured_posts=featured_posts, featured_repos=featured_repos)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == UserRole.ADMIN:
        return redirect(url_for('main.admin'))
    
    # Get user's projects, contracts, and recent messages
    projects = Project.query.filter_by(client_id=current_user.id).order_by(Project.updated_at.desc()).limit(5).all()
    contracts = Contract.query.filter_by(client_id=current_user.id).order_by(Contract.updated_at.desc()).limit(5).all()
    recent_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).order_by(Message.sent_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', projects=projects, contracts=contracts, messages=recent_messages)

@main_bp.route('/admin')
@login_required
@admin_required
def admin():
    # Get admin dashboard statistics
    total_users = User.query.count()
    total_projects = Project.query.count()
    active_contracts = Contract.query.filter_by(status=ContractStatus.ACTIVE).count()
    pending_payments = Payment.query.filter_by(status=PaymentStatus.PENDING).count()
    
    # Recent activity
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    unverified_users = User.query.filter_by(is_verified=False).all()
    
    stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'active_contracts': active_contracts,
        'pending_payments': pending_payments
    }
    
    return render_template('admin.html', stats=stats, activities=recent_activities, unverified_users=unverified_users)

@main_bp.route('/projects')
@login_required
def projects():
    if current_user.role == UserRole.ADMIN:
        all_projects = Project.query.order_by(Project.updated_at.desc()).all()
    else:
        all_projects = Project.query.filter_by(client_id=current_user.id).order_by(Project.updated_at.desc()).all()
    
    return render_template('projects.html', projects=all_projects)

@main_bp.route('/project-wizard')
def project_wizard():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('project_wizard.html', today=today)

@main_bp.route('/project-wizard/submit', methods=['POST'])
def submit_project_wizard():
    try:
        # Extract form data
        title = request.form.get('project_title')
        project_type = request.form.get('project_type')
        description = request.form.get('project_description')
        budget_range = request.form.get('budget_range')
        deadline = request.form.get('deadline')
        client_email = request.form.get('client_email')
        client_name = request.form.get('client_name')
        
        # Check if user exists or create new one
        user = User.query.filter_by(email=client_email).first()
        if not user:
            # Generate random password
            import secrets
            import string
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            # Create new user
            user = User()
            user.username = client_email.split('@')[0]
            user.email = client_email
            user.first_name = client_name.split(' ')[0] if client_name else ''
            user.last_name = ' '.join(client_name.split(' ')[1:]) if client_name and len(client_name.split(' ')) > 1 else ''
            user.set_password(password)
            user.role = UserRole.CLIENT
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Send welcome email with password (placeholder for now)
            log_activity(user.id, 'ACCOUNT_CREATED', f'Account auto-created via project wizard for {client_email}')
        
        # Convert budget range to estimated amount
        budget_mapping = {
            'under_5k': 2500,
            '5k_15k': 10000,
            '15k_50k': 32500,
            '50k_100k': 75000,
            'over_100k': 150000,
            'discuss': None
        }
        
        budget = budget_mapping.get(budget_range)
        deadline_date = None
        if deadline:
            from datetime import datetime
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        
        # Create new project
        new_project = Project()
        new_project.title = title
        new_project.description = description
        new_project.project_type = project_type
        new_project.budget = budget
        new_project.deadline = deadline_date
        new_project.client_id = user.id
        new_project.status = ProjectStatus.PENDING
        
        db.session.add(new_project)
        db.session.commit()
        
        # Handle file uploads
        files = request.files.getlist('project_files')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create file record
                project_file = ProjectFile()
                project_file.filename = filename
                project_file.original_filename = file.filename
                project_file.file_path = file_path
                project_file.file_size = os.path.getsize(file_path)
                project_file.mime_type = file.content_type or 'application/octet-stream'
                project_file.project_id = new_project.id
                
                db.session.add(project_file)
        
        # Extract and save additional data as JSON in description
        additional_data = {
            'target_audience': request.form.get('target_audience'),
            'industry': request.form.get('industry'),
            'technologies': request.form.getlist('technologies'),
            'platforms': request.form.getlist('platforms'),
            'integrations': request.form.get('integrations'),
            'urgency': request.form.get('urgency'),
            'payment_preference': request.form.get('payment_preference'),
            'special_requirements': request.form.get('special_requirements'),
            'design_preferences': request.form.get('design_preferences'),
            'color_scheme': request.form.get('color_scheme'),
            'inspiration_links': request.form.get('inspiration_links')
        }
        
        # Append additional data to description
        import json
        new_project.description += f"\n\n--- Additional Details ---\n{json.dumps(additional_data, indent=2)}"
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'PROJECT_SUBMITTED', f'New project submitted via wizard: {title}')
        
        return jsonify({
            'success': True, 
            'message': 'Project submitted successfully!',
            'project_id': new_project.id,
            'user_created': user.username if not User.query.filter_by(email=client_email).first() else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error submitting project. Please try again.'})

@main_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        project_type = request.form['project_type']
        budget = float(request.form['budget']) if request.form['budget'] else None
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d') if request.form['deadline'] else None
        
        project = Project(
            title=title,
            description=description,
            project_type=project_type,
            budget=budget,
            deadline=deadline,
            client_id=current_user.id,
            status=ProjectStatus.PENDING
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Handle file uploads
        if 'project_files' in request.files:
            files = request.files.getlist('project_files')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"project_{project.id}_{file.filename}")
                    file_path = os.path.join('uploads', 'projects', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    
                    project_file = ProjectFile(
                        filename=filename,
                        original_filename=file.filename,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        mime_type=file.content_type,
                        project_id=project.id
                    )
                    db.session.add(project_file)
        
        db.session.commit()
        log_activity(current_user.id, 'PROJECT_CREATE', f'Created project: {title}')
        flash('Project created successfully!', 'success')
        return redirect(url_for('main.projects'))
    
    return render_template('create_project.html')

@main_bp.route('/contracts')
@login_required
def contracts():
    if current_user.role == UserRole.ADMIN:
        all_contracts = Contract.query.order_by(Contract.updated_at.desc()).all()
    else:
        all_contracts = Contract.query.filter_by(client_id=current_user.id).order_by(Contract.updated_at.desc()).all()
    
    return render_template('contracts.html', contracts=all_contracts)

@main_bp.route('/payments')
@login_required
def payments():
    if current_user.role == UserRole.ADMIN:
        all_payments = Payment.query.order_by(Payment.created_at.desc()).all()
    else:
        all_payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    return render_template('payments.html', payments=all_payments)

@main_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        payment_id = request.form.get('payment_id')
        payment = Payment.query.get_or_404(payment_id)
        
        # Verify user authorization
        if current_user.role != UserRole.ADMIN and payment.user_id != current_user.id:
            flash('Unauthorized access', 'error')
            return redirect(url_for('main.payments'))
        
        YOUR_DOMAIN = request.host_url.rstrip('/')
        
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price_data': {
                        'currency': payment.currency.lower(),
                        'product_data': {
                            'name': payment.description or f'Payment #{payment.id}',
                        },
                        'unit_amount': int(payment.amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + url_for('main.payment_success', payment_id=payment.id),
            cancel_url=YOUR_DOMAIN + url_for('main.payment_cancel', payment_id=payment.id),
            metadata={
                'payment_id': payment.id,
                'user_id': current_user.id
            }
        )
        
        # Update payment with Stripe session ID
        payment.stripe_session_id = checkout_session.id
        db.session.commit()
        
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f'Error creating payment session: {str(e)}', 'error')
        return redirect(url_for('main.payments'))

@main_bp.route('/payment/success/<int:payment_id>')
@login_required
def payment_success(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Update payment status
    payment.status = PaymentStatus.COMPLETED
    payment.paid_at = datetime.utcnow()
    db.session.commit()
    
    log_activity(current_user.id, 'PAYMENT_SUCCESS', f'Payment #{payment.id} completed')
    flash('Payment completed successfully!', 'success')
    return redirect(url_for('main.payments'))

@main_bp.route('/payment/cancel/<int:payment_id>')
@login_required
def payment_cancel(payment_id):
    flash('Payment was cancelled', 'info')
    return redirect(url_for('main.payments'))

@main_bp.route('/messages')
@login_required
def messages():
    if current_user.role == UserRole.ADMIN:
        sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.sent_at.desc()).all()
        received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.sent_at.desc()).all()
    else:
        # Clients can only see messages with admin
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin_user:
            sent_messages = Message.query.filter_by(sender_id=current_user.id, recipient_id=admin_user.id).order_by(Message.sent_at.desc()).all()
            received_messages = Message.query.filter_by(sender_id=admin_user.id, recipient_id=current_user.id).order_by(Message.sent_at.desc()).all()
        else:
            sent_messages = []
            received_messages = []
    
    return render_template('messages.html', sent_messages=sent_messages, received_messages=received_messages)

@main_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    subject = request.form['subject']
    content = request.form['content']
    recipient_id = request.form.get('recipient_id')
    
    # If no recipient specified and user is client, send to admin
    if not recipient_id and current_user.role == UserRole.CLIENT:
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        recipient_id = admin_user.id if admin_user else None
    
    if not recipient_id:
        flash('No recipient specified', 'error')
        return redirect(url_for('main.messages'))
    
    message = Message(
        subject=subject,
        content=content,
        sender_id=current_user.id,
        recipient_id=recipient_id
    )
    
    # Handle file attachment
    if 'attachment' in request.files:
        attachment = request.files['attachment']
        if attachment and allowed_file(attachment.filename):
            filename = secure_filename(f"msg_{attachment.filename}")
            attachment_path = os.path.join('uploads', 'messages', filename)
            os.makedirs(os.path.dirname(attachment_path), exist_ok=True)
            attachment.save(attachment_path)
            message.attachment_path = attachment_path
    
    db.session.add(message)
    db.session.commit()
    
    log_activity(current_user.id, 'MESSAGE_SEND', f'Sent message: {subject}')
    flash('Message sent successfully!', 'success')
    return redirect(url_for('main.messages'))

@main_bp.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    query = BlogPost.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    
    posts = query.order_by(BlogPost.published_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    categories = db.session.query(BlogPost.category).filter_by(is_published=True).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('blog.html', posts=posts, categories=categories, current_category=category)

@main_bp.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    # Increment views
    post.views += 1
    db.session.commit()
    
    # Get comments
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    return render_template('blog_post.html', post=post, comments=comments)

@main_bp.route('/github')
def github_repos():
    repos = GitHubRepo.query.order_by(GitHubRepo.updated_at.desc()).all()
    return render_template('github.html', repos=repos)

# File serving routes
@main_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API endpoints for AJAX calls
@main_bp.route('/api/mark-message-read/<int:message_id>', methods=['POST'])
@login_required
def mark_message_read(message_id):
    message = Message.query.get_or_404(message_id)
    if message.recipient_id == current_user.id:
        message.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Unauthorized'}), 403

@main_bp.route('/api/like-post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return jsonify({'likes': post.likes})

@main_bp.route('/api/verify-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    
    log_activity(current_user.id, 'USER_VERIFY', f'Verified user: {user.username}')
    return jsonify({'success': True})

@main_bp.route('/api/update-project-status/<int:project_id>', methods=['POST'])
@login_required
@admin_required
def update_project_status(project_id):
    project = Project.query.get_or_404(project_id)
    new_status = request.json.get('status')
    progress = request.json.get('progress', project.progress)
    
    try:
        project.status = ProjectStatus(new_status)
        project.progress = progress
        db.session.commit()
        
        log_activity(current_user.id, 'PROJECT_UPDATE', f'Updated project {project.id} status to {new_status}')
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

# Error handlers
@main_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# API endpoints for real-time updates
@main_bp.route('/api/unread-messages')
def api_unread_messages():
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@main_bp.route('/api/notifications')
def api_notifications():
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    # Count unread messages as notifications for now
    count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@main_bp.route('/privacy')
def privacy_policy():
    from datetime import datetime
    current_date = datetime.now().strftime('%B %d, %Y')
    return render_template('privacy.html', current_date=current_date)

@main_bp.route('/terms')
def terms_of_service():
    from datetime import datetime
    current_date = datetime.now().strftime('%B %d, %Y')
    return render_template('terms.html', current_date=current_date)

@main_bp.route('/latest-projects')
def latest_projects():
    # Show latest 6 completed projects (public view)
    featured_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).order_by(Project.updated_at.desc()).limit(6).all()
    return render_template('latest_projects.html', projects=featured_projects)

# Blueprint registration moved to main.py to avoid circular imports
