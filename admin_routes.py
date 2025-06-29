from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, asc, func, extract, or_
from datetime import datetime, timedelta
import calendar

from app import db
from models import (User, UserRole, Project, ProjectStatus, Payment, PaymentStatus, 
                   Contract, Message, BlogPost, Comment, ActivityLog, Notification,
                   GitHubRepo, Milestone)
from forms import BlogPostForm, ContractForm, ProjectForm, MilestoneForm
from utils import log_activity, save_uploaded_file, admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@admin_required
def require_admin():
    """Ensure only admin users can access these routes"""
    pass

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard with comprehensive analytics"""
    
    # User statistics
    total_users = User.query.count()
    new_users_this_month = User.query.filter(
        extract('month', User.created_at) == datetime.now().month,
        extract('year', User.created_at) == datetime.now().year
    ).count()
    verified_users = User.query.filter_by(is_verified=True).count()
    unverified_users = User.query.filter_by(is_verified=False).count()
    
    # Project statistics
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status=ProjectStatus.IN_PROGRESS).count()
    completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()
    pending_projects = Project.query.filter_by(status=ProjectStatus.PENDING).count()
    
    # Payment statistics
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status=PaymentStatus.COMPLETED).scalar() or 0
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED,
        extract('month', Payment.created_at) == datetime.now().month,
        extract('year', Payment.created_at) == datetime.now().year
    ).scalar() or 0
    pending_payments = Payment.query.filter_by(status=PaymentStatus.PENDING).count()
    
    # Recent activity
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_projects = Project.query.order_by(desc(Project.created_at)).limit(5).all()
    recent_payments = Payment.query.order_by(desc(Payment.created_at)).limit(5).all()
    recent_activities = ActivityLog.query.order_by(desc(ActivityLog.created_at)).limit(10).all()
    
    # Unread messages
    unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    # Monthly data for charts
    monthly_data = []
    for i in range(12):
        month = datetime.now().month - i
        year = datetime.now().year
        if month <= 0:
            month += 12
            year -= 1
        
        users_count = User.query.filter(
            extract('month', User.created_at) == month,
            extract('year', User.created_at) == year
        ).count()
        
        projects_count = Project.query.filter(
            extract('month', Project.created_at) == month,
            extract('year', Project.created_at) == year
        ).count()
        
        revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.COMPLETED,
            extract('month', Payment.created_at) == month,
            extract('year', Payment.created_at) == year
        ).scalar() or 0
        
        monthly_data.append({
            'month': calendar.month_abbr[month],
            'users': users_count,
            'projects': projects_count,
            'revenue': float(revenue)
        })
    
    monthly_data.reverse()
    
    stats = {
        'users': {
            'total': total_users,
            'new_this_month': new_users_this_month,
            'verified': verified_users,
            'unverified': unverified_users
        },
        'projects': {
            'total': total_projects,
            'active': active_projects,
            'completed': completed_projects,
            'pending': pending_projects
        },
        'payments': {
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'pending': pending_payments
        }
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_projects=recent_projects,
                         recent_payments=recent_payments,
                         recent_activities=recent_activities,
                         unread_messages=unread_messages,
                         monthly_data=monthly_data)

@admin_bp.route('/users')
@login_required
def users():
    """Manage users"""
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    # Apply role filter
    if role_filter != 'all':
        try:
            role = UserRole(role_filter)
            query = query.filter_by(role=role)
        except ValueError:
            pass
    
    # Apply status filter
    if status_filter == 'verified':
        query = query.filter_by(is_verified=True)
    elif status_filter == 'unverified':
        query = query.filter_by(is_verified=False)
    elif status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Apply sorting
    if hasattr(User, sort_by):
        sort_column = getattr(User, sort_by)
        if order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html',
                         users=users,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         order=order)

@admin_bp.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    """User detail page with full information and actions"""
    
    user = User.query.get_or_404(user_id)
    
    # Get user's projects
    projects = Project.query.filter_by(client_id=user_id).order_by(desc(Project.created_at)).all()
    
    # Get user's payments
    payments = Payment.query.filter_by(user_id=user_id).order_by(desc(Payment.created_at)).all()
    
    # Get user's messages
    messages = Message.query.filter(
        or_(Message.sender_id == user_id, Message.recipient_id == user_id)
    ).order_by(desc(Message.sent_at)).limit(10).all()
    
    # Get user's activity
    activities = ActivityLog.query.filter_by(user_id=user_id).order_by(desc(ActivityLog.created_at)).limit(20).all()
    
    # Calculate user statistics
    user_stats = {
        'total_projects': len(projects),
        'completed_projects': len([p for p in projects if p.status == ProjectStatus.COMPLETED]),
        'total_spent': sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED),
        'messages_sent': Message.query.filter_by(sender_id=user_id).count(),
        'last_activity': activities[0].created_at if activities else user.created_at
    }
    
    return render_template('admin/user_detail.html',
                         user=user,
                         projects=projects,
                         payments=payments,
                         messages=messages,
                         activities=activities,
                         user_stats=user_stats)

@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@login_required
def verify_user(user_id):
    """Verify a user account"""
    
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    user.is_active = True
    
    # Create notification for user
    notification = Notification(
        user_id=user.id,
        title='Account Verified',
        message='Your account has been verified by an administrator.',
        type='success'
    )
    
    db.session.add(notification)
    db.session.commit()
    
    log_activity(current_user.id, 'user_verified', f'Admin verified user: {user.username}')
    flash(f'User {user.username} has been verified.', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    
    # Create notification for user
    notification = Notification(
        user_id=user.id,
        title='Account Deactivated',
        message='Your account has been deactivated. Please contact support for assistance.',
        type='warning'
    )
    
    db.session.add(notification)
    db.session.commit()
    
    log_activity(current_user.id, 'user_deactivated', f'Admin deactivated user: {user.username}')
    flash(f'User {user.username} has been deactivated.', 'warning')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/projects')
@login_required
def projects():
    """Manage all projects"""
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = Project.query
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%'),
                Project.project_type.ilike(f'%{search}%')
            )
        )
    
    # Apply status filter
    if status_filter != 'all':
        try:
            status = ProjectStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    # Apply sorting
    if hasattr(Project, sort_by):
        sort_column = getattr(Project, sort_by)
        if order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    projects = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/projects.html',
                         projects=projects,
                         search=search,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         order=order)

@admin_bp.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    """Project detail page for admin"""
    
    project = Project.query.get_or_404(project_id)
    
    # Get all project data
    files = project.files
    milestones = project.milestones
    payments = Payment.query.filter_by(project_id=project_id).all()
    messages = Message.query.filter_by(project_id=project_id).all()
    
    return render_template('admin/project_detail.html',
                         project=project,
                         files=files,
                         milestones=milestones,
                         payments=payments,
                         messages=messages)

@admin_bp.route('/projects/<int:project_id>/update-status', methods=['POST'])
@login_required
def update_project_status(project_id):
    """Update project status"""
    
    project = Project.query.get_or_404(project_id)
    new_status = request.form.get('status')
    
    try:
        project.status = ProjectStatus(new_status)
        
        # Update progress based on status
        if project.status == ProjectStatus.COMPLETED:
            project.progress = 100
        elif project.status == ProjectStatus.IN_PROGRESS and project.progress == 0:
            project.progress = 10
        
        db.session.commit()
        
        # Create notification for client
        notification = Notification(
            user_id=project.client_id,
            title='Project Status Updated',
            message=f'Your project "{project.title}" status has been updated to {new_status.replace("_", " ").title()}.',
            type='info',
            action_url=url_for('user.project_detail', project_id=project.id)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        log_activity(current_user.id, 'project_status_updated', 
                    f'Admin updated project {project.title} status to {new_status}')
        
        flash(f'Project status updated to {new_status.replace("_", " ").title()}.', 'success')
        
    except ValueError:
        flash('Invalid status value.', 'error')
    
    return redirect(url_for('admin.project_detail', project_id=project_id))

@admin_bp.route('/projects/<int:project_id>/assign', methods=['POST'])
@login_required
def assign_project(project_id):
    """Assign project to a team member"""
    
    project = Project.query.get_or_404(project_id)
    assigned_to = request.form.get('assigned_to')
    
    if assigned_to:
        project.assigned_to = int(assigned_to)
    else:
        project.assigned_to = None
    
    db.session.commit()
    
    log_activity(current_user.id, 'project_assigned', 
                f'Admin assigned project {project.title} to user {assigned_to}')
    
    flash('Project assignment updated.', 'success')
    return redirect(url_for('admin.project_detail', project_id=project_id))

@admin_bp.route('/payments')
@login_required
def payments():
    """Manage payments and generate reports"""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Payment.query
    
    # Apply status filter
    if status_filter != 'all':
        try:
            status = PaymentStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payment.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Payment.created_at <= to_date)
        except ValueError:
            pass
    
    payments = query.order_by(desc(Payment.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate payment statistics
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status=PaymentStatus.COMPLETED).scalar() or 0
    pending_amount = db.session.query(func.sum(Payment.amount)).filter_by(status=PaymentStatus.PENDING).scalar() or 0
    failed_amount = db.session.query(func.sum(Payment.amount)).filter_by(status=PaymentStatus.FAILED).scalar() or 0
    
    payment_stats = {
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'failed_amount': failed_amount,
        'total_transactions': Payment.query.count(),
        'successful_transactions': Payment.query.filter_by(status=PaymentStatus.COMPLETED).count(),
        'pending_transactions': Payment.query.filter_by(status=PaymentStatus.PENDING).count()
    }
    
    return render_template('admin/payments.html',
                         payments=payments,
                         payment_stats=payment_stats,
                         status_filter=status_filter,
                         date_from=date_from,
                         date_to=date_to)

@admin_bp.route('/blog')
@login_required
def blog():
    """Manage blog posts"""
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', 'all')
    status_filter = request.args.get('status', 'all')
    
    query = BlogPost.query
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                BlogPost.title.ilike(f'%{search}%'),
                BlogPost.content.ilike(f'%{search}%'),
                BlogPost.excerpt.ilike(f'%{search}%')
            )
        )
    
    # Apply category filter
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    # Apply status filter
    if status_filter == 'published':
        query = query.filter_by(is_published=True)
    elif status_filter == 'draft':
        query = query.filter_by(is_published=False)
    elif status_filter == 'featured':
        query = query.filter_by(is_featured=True)
    
    blog_posts = query.order_by(desc(BlogPost.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(BlogPost.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin/blog.html',
                         blog_posts=blog_posts,
                         categories=categories,
                         search=search,
                         category_filter=category_filter,
                         status_filter=status_filter)

@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    """Create a new blog post"""
    
    form = BlogPostForm()
    
    if form.validate_on_submit():
        # Handle featured image upload
        featured_image = None
        if form.featured_image.data:
            featured_image = save_uploaded_file(form.featured_image.data, 'blog_images')
        
        blog_post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            category=form.category.data,
            tags=form.tags.data,
            featured_image=featured_image,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            author_id=current_user.id
        )
        
        if form.is_published.data:
            blog_post.published_at = datetime.utcnow()
        
        db.session.add(blog_post)
        db.session.commit()
        
        log_activity(current_user.id, 'blog_post_created', f'Admin created blog post: {blog_post.title}')
        flash('Blog post created successfully!', 'success')
        
        return redirect(url_for('admin.blog'))
    
    return render_template('admin/create_blog_post.html', form=form)

@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    """Edit a blog post"""
    
    blog_post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=blog_post)
    
    if form.validate_on_submit():
        # Handle featured image upload
        if form.featured_image.data:
            featured_image = save_uploaded_file(form.featured_image.data, 'blog_images')
            blog_post.featured_image = featured_image
        
        blog_post.title = form.title.data
        blog_post.content = form.content.data
        blog_post.excerpt = form.excerpt.data
        blog_post.category = form.category.data
        blog_post.tags = form.tags.data
        blog_post.is_published = form.is_published.data
        blog_post.is_featured = form.is_featured.data
        
        if form.is_published.data and not blog_post.published_at:
            blog_post.published_at = datetime.utcnow()
        
        db.session.commit()
        
        log_activity(current_user.id, 'blog_post_updated', f'Admin updated blog post: {blog_post.title}')
        flash('Blog post updated successfully!', 'success')
        
        return redirect(url_for('admin.blog'))
    
    return render_template('admin/edit_blog_post.html', form=form, blog_post=blog_post)

@admin_bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_blog_post(post_id):
    """Delete a blog post"""
    
    blog_post = BlogPost.query.get_or_404(post_id)
    title = blog_post.title
    
    db.session.delete(blog_post)
    db.session.commit()
    
    log_activity(current_user.id, 'blog_post_deleted', f'Admin deleted blog post: {title}')
    flash('Blog post deleted successfully!', 'success')
    
    return redirect(url_for('admin.blog'))

@admin_bp.route('/messages')
@login_required
def messages():
    """Admin message center"""
    
    page = request.args.get('page', 1, type=int)
    message_type = request.args.get('type', 'all')
    
    if message_type == 'sent':
        query = Message.query.filter_by(sender_id=current_user.id)
    elif message_type == 'received':
        query = Message.query.filter_by(recipient_id=current_user.id)
    else:
        query = Message.query.filter(
            or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
        )
    
    messages = query.order_by(desc(Message.sent_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unread count
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    return render_template('admin/messages.html',
                         messages=messages,
                         message_type=message_type,
                         unread_count=unread_count)

@admin_bp.route('/analytics')
@login_required
def analytics():
    """Advanced analytics dashboard"""
    
    # Time period filter
    period = request.args.get('period', '30')  # days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(period))
    
    # User analytics
    user_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= start_date).group_by(func.date(User.created_at)).all()
    
    # Project analytics
    project_creation = db.session.query(
        func.date(Project.created_at).label('date'),
        func.count(Project.id).label('count')
    ).filter(Project.created_at >= start_date).group_by(func.date(Project.created_at)).all()
    
    # Revenue analytics
    revenue_data = db.session.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount).label('amount')
    ).filter(
        Payment.created_at >= start_date,
        Payment.status == PaymentStatus.COMPLETED
    ).group_by(func.date(Payment.created_at)).all()
    
    # Top clients by revenue
    top_clients = db.session.query(
        User.username,
        User.email,
        func.sum(Payment.amount).label('total_spent')
    ).join(Payment).filter(
        Payment.status == PaymentStatus.COMPLETED
    ).group_by(User.id).order_by(desc(func.sum(Payment.amount))).limit(10).all()
    
    # Project status distribution
    project_status_data = db.session.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Popular project types
    project_types = db.session.query(
        Project.project_type,
        func.count(Project.id).label('count')
    ).group_by(Project.project_type).order_by(desc(func.count(Project.id))).all()
    
    analytics_data = {
        'user_registrations': [{'date': str(item.date), 'count': item.count} for item in user_registrations],
        'project_creation': [{'date': str(item.date), 'count': item.count} for item in project_creation],
        'revenue_data': [{'date': str(item.date), 'amount': float(item.amount or 0)} for item in revenue_data],
        'top_clients': [{'username': item.username, 'email': item.email, 'total_spent': float(item.total_spent)} for item in top_clients],
        'project_status': [{'status': item.status.value, 'count': item.count} for item in project_status_data],
        'project_types': [{'type': item.project_type, 'count': item.count} for item in project_types]
    }
    
    return render_template('admin/analytics.html',
                         analytics_data=analytics_data,
                         period=period)

@admin_bp.route('/settings')
@login_required
def settings():
    """Admin system settings"""
    
    return render_template('admin/settings.html')
