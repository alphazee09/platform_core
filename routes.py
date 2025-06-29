from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import desc, or_
import os

from app import db
from models import Project, BlogPost, GitHubRepo, User, Payment, Message, Notification
from utils import log_activity

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with featured content"""
    
    # Get featured projects
    featured_projects = Project.query.filter_by(is_featured=True).order_by(desc(Project.created_at)).limit(6).all()
    
    # Get recent projects if no featured projects
    if not featured_projects:
        featured_projects = Project.query.filter_by(status='completed').order_by(desc(Project.created_at)).limit(6).all()
    
    # Get featured blog posts
    featured_posts = BlogPost.query.filter_by(is_published=True, is_featured=True).order_by(desc(BlogPost.published_at)).limit(3).all()
    
    # Get recent blog posts if no featured posts
    if not featured_posts:
        featured_posts = BlogPost.query.filter_by(is_published=True).order_by(desc(BlogPost.published_at)).limit(3).all()
    
    # Get GitHub repositories
    github_repos = GitHubRepo.query.filter_by(is_featured=True).order_by(desc(GitHubRepo.stars)).limit(6).all()
    
    # Get basic statistics for homepage
    stats = {
        'total_projects': Project.query.count(),
        'completed_projects': Project.query.filter_by(status='completed').count(),
        'happy_clients': User.query.filter_by(role='client', is_verified=True).count(),
        'years_experience': 5  # Static value or calculate based on your start date
    }
    
    return render_template('landing.html',
                         featured_projects=featured_projects,
                         featured_posts=featured_posts,
                         github_repos=github_repos,
                         stats=stats)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirect to appropriate dashboard based on user role"""
    
    if current_user.role.value == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))

@main_bp.route('/projects')
def public_projects():
    """Public projects showcase page"""
    
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = Project.query.filter_by(status='completed')
    
    # Apply category filter
    if category != 'all':
        query = query.filter_by(project_type=category)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%'),
                Project.technologies.ilike(f'%{search}%')
            )
        )
    
    projects = query.order_by(desc(Project.created_at)).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get unique project types for category filter
    project_types = db.session.query(Project.project_type).distinct().all()
    project_types = [pt[0] for pt in project_types if pt[0]]
    
    return render_template('public_projects.html',
                         projects=projects,
                         project_types=project_types,
                         category=category,
                         search=search)

@main_bp.route('/blog')
def blog():
    """Public blog listing page"""
    
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = BlogPost.query.filter_by(is_published=True)
    
    # Apply category filter
    if category != 'all':
        query = query.filter_by(category=category)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                BlogPost.title.ilike(f'%{search}%'),
                BlogPost.content.ilike(f'%{search}%'),
                BlogPost.excerpt.ilike(f'%{search}%')
            )
        )
    
    posts = query.order_by(desc(BlogPost.published_at)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(BlogPost.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Get recent posts for sidebar
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(desc(BlogPost.published_at)).limit(5).all()
    
    return render_template('blog.html',
                         posts=posts,
                         categories=categories,
                         recent_posts=recent_posts,
                         category=category,
                         search=search)

@main_bp.route('/blog/<int:post_id>')
def blog_post(post_id):
    """Individual blog post page"""
    
    post = BlogPost.query.get_or_404(post_id)
    
    if not post.is_published:
        flash('This blog post is not available.', 'error')
        return redirect(url_for('main.blog'))
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get related posts
    related_posts = BlogPost.query.filter(
        BlogPost.is_published == True,
        BlogPost.category == post.category,
        BlogPost.id != post.id
    ).order_by(desc(BlogPost.published_at)).limit(3).all()
    
    return render_template('blog_post.html',
                         post=post,
                         related_posts=related_posts)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/services')
def services():
    """Services page"""
    return render_template('services.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form"""
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_content = request.form.get('message')
        
        if name and email and subject and message_content:
            # Create a message to admin
            admin_user = User.query.filter_by(role='admin').first()
            if admin_user:
                message = Message(
                    subject=f"Contact Form: {subject}",
                    content=f"From: {name} ({email})\n\n{message_content}",
                    sender_id=1,  # System user or create a system user
                    recipient_id=admin_user.id
                )
                db.session.add(message)
                db.session.commit()
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('main.contact'))
        else:
            flash('Please fill in all required fields.', 'error')
    
    return render_template('contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

# API Routes
@main_bp.route('/api/notifications')
@login_required
def api_notifications():
    """Get user notifications"""
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(desc(Notification.created_at)).limit(10).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'created_at': n.created_at.isoformat(),
        'action_url': n.action_url
    } for n in notifications])

@main_bp.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/api/messages/unread-count')
@login_required
def unread_messages_count():
    """Get unread messages count"""
    
    count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})

@main_bp.route('/api/search')
def api_search():
    """Global search API"""
    
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    limit = request.args.get('limit', 10, type=int)
    
    results = []
    
    if len(query) >= 2:
        if category in ['all', 'projects']:
            projects = Project.query.filter(
                Project.title.ilike(f'%{query}%')
            ).limit(limit).all()
            
            for project in projects:
                results.append({
                    'type': 'project',
                    'id': project.id,
                    'title': project.title,
                    'description': project.description[:100] + '...' if len(project.description) > 100 else project.description,
                    'url': url_for('user.project_detail', project_id=project.id) if current_user.is_authenticated else '#'
                })
        
        if category in ['all', 'blog']:
            posts = BlogPost.query.filter(
                BlogPost.is_published == True,
                BlogPost.title.ilike(f'%{query}%')
            ).limit(limit).all()
            
            for post in posts:
                results.append({
                    'type': 'blog_post',
                    'id': post.id,
                    'title': post.title,
                    'description': post.excerpt or (post.content[:100] + '...' if len(post.content) > 100 else post.content),
                    'url': url_for('main.blog_post', post_id=post.id)
                })
    
    return jsonify({'results': results})

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Timeline route (from existing codebase)
@main_bp.route('/timeline')
def timeline():
    """Developer timeline page"""
    return render_template('timeline.html')

# Payment success/cancel routes
@main_bp.route('/payment/success')
def payment_success():
    """Payment success callback"""
    session_id = request.args.get('session_id')
    
    if session_id:
        # Handle payment success
        payment = Payment.query.filter_by(thawani_session_id=session_id).first()
        if payment:
            payment.status = 'completed'
            payment.paid_at = datetime.utcnow()
            db.session.commit()
            
            # Create notification
            notification = Notification(
                user_id=payment.user_id,
                title='Payment Successful',
                message=f'Your payment of {payment.amount} {payment.currency} has been processed successfully.',
                type='success'
            )
            db.session.add(notification)
            db.session.commit()
    
    return render_template('payment_success.html')

@main_bp.route('/payment/cancel')
def payment_cancel():
    """Payment cancel callback"""
    return render_template('payment_cancel.html')
