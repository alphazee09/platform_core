from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_required, current_user
from sqlalchemy import or_, desc, asc
from datetime import datetime, timedelta
import os

from app import db
from models import (User, Project, ProjectStatus, Payment, PaymentStatus, Contract, 
                   Message, Milestone, ProjectFile, ProjectFollower, Notification)
from forms import ProjectForm, MessageForm, PaymentForm
from utils import log_activity, save_uploaded_file, allowed_file
from thawani_payment import ThawaniPayment

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with overview of projects, payments, and recent activity"""
    
    # Get user's projects
    projects = Project.query.filter_by(client_id=current_user.id).order_by(desc(Project.created_at)).limit(5).all()
    
    # Get followed projects
    followed_projects = db.session.query(Project).join(ProjectFollower).filter(
        ProjectFollower.user_id == current_user.id
    ).order_by(desc(ProjectFollower.created_at)).limit(3).all()
    
    # Get recent payments
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(desc(Payment.created_at)).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    # Get recent notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(desc(Notification.created_at)).limit(5).all()
    
    # Calculate statistics
    stats = {
        'total_projects': Project.query.filter_by(client_id=current_user.id).count(),
        'active_projects': Project.query.filter_by(client_id=current_user.id, status=ProjectStatus.IN_PROGRESS).count(),
        'completed_projects': Project.query.filter_by(client_id=current_user.id, status=ProjectStatus.COMPLETED).count(),
        'total_payments': sum(p.amount for p in Payment.query.filter_by(user_id=current_user.id, status=PaymentStatus.COMPLETED).all()),
        'pending_payments': Payment.query.filter_by(user_id=current_user.id, status=PaymentStatus.PENDING).count()
    }
    
    return render_template('user/dashboard.html', 
                         projects=projects,
                         followed_projects=followed_projects,
                         payments=payments,
                         unread_messages=unread_messages,
                         notifications=notifications,
                         stats=stats)

@user_bp.route('/projects')
@login_required
def projects():
    """List all user's projects with filtering and search"""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = Project.query.filter_by(client_id=current_user.id)
    
    # Apply status filter
    if status_filter != 'all':
        try:
            status = ProjectStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%'),
                Project.project_type.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if hasattr(Project, sort_by):
        sort_column = getattr(Project, sort_by)
        if order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    projects = query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('user/projects.html', 
                         projects=projects,
                         status_filter=status_filter,
                         search=search,
                         sort_by=sort_by,
                         order=order)

@user_bp.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    """Project detail page with files, milestones, and progress"""
    
    project = Project.query.get_or_404(project_id)
    
    # Check if user can access this project
    if not current_user.can_access_project(project):
        abort(403)
    
    # Get project files
    files = ProjectFile.query.filter_by(project_id=project_id).order_by(desc(ProjectFile.uploaded_at)).all()
    
    # Get milestones
    milestones = Milestone.query.filter_by(project_id=project_id).order_by(asc(Milestone.due_date)).all()
    
    # Get project payments
    payments = Payment.query.filter_by(project_id=project_id).order_by(desc(Payment.created_at)).all()
    
    # Check if user is following this project
    is_following = ProjectFollower.query.filter_by(
        user_id=current_user.id, 
        project_id=project_id
    ).first() is not None
    
    # Get project messages
    messages = Message.query.filter_by(project_id=project_id).order_by(desc(Message.sent_at)).limit(10).all()
    
    return render_template('user/project_detail.html',
                         project=project,
                         files=files,
                         milestones=milestones,
                         payments=payments,
                         is_following=is_following,
                         messages=messages)

@user_bp.route('/projects/<int:project_id>/follow', methods=['POST'])
@login_required
def follow_project(project_id):
    """Follow/unfollow a project"""
    
    project = Project.query.get_or_404(project_id)
    
    existing_follow = ProjectFollower.query.filter_by(
        user_id=current_user.id,
        project_id=project_id
    ).first()
    
    if existing_follow:
        db.session.delete(existing_follow)
        action = 'unfollowed'
    else:
        follow = ProjectFollower(user_id=current_user.id, project_id=project_id)
        db.session.add(follow)
        action = 'followed'
    
    db.session.commit()
    log_activity(current_user.id, f'project_{action}', f'User {action} project: {project.title}')
    
    return jsonify({'success': True, 'action': action})

@user_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create a new project"""
    
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            project_type=form.project_type.data,
            technologies=form.technologies.data,
            budget=form.budget.data,
            deadline=form.deadline.data,
            priority=form.priority.data,
            client_id=current_user.id,
            status=ProjectStatus.PENDING
        )
        
        db.session.add(project)
        db.session.commit()
        
        log_activity(current_user.id, 'project_created', f'User created project: {project.title}')
        flash('Project created successfully!', 'success')
        
        return redirect(url_for('user.project_detail', project_id=project.id))
    
    return render_template('user/create_project.html', form=form)

@user_bp.route('/payments')
@login_required
def payments():
    """List all user's payments with filtering"""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Payment.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        try:
            status = PaymentStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    payments = query.order_by(desc(Payment.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate payment statistics
    total_paid = sum(p.amount for p in Payment.query.filter_by(
        user_id=current_user.id, status=PaymentStatus.COMPLETED
    ).all())
    
    pending_amount = sum(p.amount for p in Payment.query.filter_by(
        user_id=current_user.id, status=PaymentStatus.PENDING
    ).all())
    
    stats = {
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'total_transactions': Payment.query.filter_by(user_id=current_user.id).count()
    }
    
    return render_template('user/payments.html', 
                         payments=payments,
                         status_filter=status_filter,
                         stats=stats)

@user_bp.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id):
    """Payment detail page"""
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Check if user owns this payment
    if payment.user_id != current_user.id:
        abort(403)
    
    return render_template('user/payment_detail.html', payment=payment)

@user_bp.route('/payments/create', methods=['GET', 'POST'])
@login_required
def create_payment():
    """Create a new payment"""
    
    form = PaymentForm()
    
    # Populate project choices
    user_projects = Project.query.filter_by(client_id=current_user.id).all()
    form.project_id.choices = [(0, 'No Project')] + [(p.id, p.title) for p in user_projects]
    
    if form.validate_on_submit():
        # Create payment record
        payment = Payment(
            amount=form.amount.data,
            currency=form.currency.data,
            description=form.description.data,
            user_id=current_user.id,
            project_id=form.project_id.data if form.project_id.data != 0 else None,
            status=PaymentStatus.PENDING
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Create Thawani checkout session
        thawani = ThawaniPayment()
        result = thawani.create_checkout_session(
            amount=payment.amount,
            currency=payment.currency,
            metadata={'payment_id': str(payment.id)},
            success_url=url_for('user.payment_success', payment_id=payment.id, _external=True),
            cancel_url=url_for('user.payment_cancel', payment_id=payment.id, _external=True)
        )
        
        if result['success']:
            payment.thawani_session_id = result['session_id']
            db.session.commit()
            
            log_activity(current_user.id, 'payment_initiated', f'User initiated payment of {payment.amount} {payment.currency}')
            
            return redirect(result['session_url'])
        else:
            flash(f'Payment creation failed: {result["error"]}', 'error')
            db.session.delete(payment)
            db.session.commit()
    
    return render_template('user/create_payment.html', form=form)

@user_bp.route('/payments/<int:payment_id>/success')
@login_required
def payment_success(payment_id):
    """Payment success page"""
    
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.user_id != current_user.id:
        abort(403)
    
    # Update payment status if not already done by webhook
    if payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('user/payment_success.html', payment=payment)

@user_bp.route('/payments/<int:payment_id>/cancel')
@login_required
def payment_cancel(payment_id):
    """Payment cancel page"""
    
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.user_id != current_user.id:
        abort(403)
    
    return render_template('user/payment_cancel.html', payment=payment)

@user_bp.route('/contracts')
@login_required
def contracts():
    """List user's contracts"""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Contract.query.filter_by(client_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    contracts = query.order_by(desc(Contract.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('user/contracts.html', 
                         contracts=contracts,
                         status_filter=status_filter)

@user_bp.route('/contracts/<int:contract_id>')
@login_required
def contract_detail(contract_id):
    """Contract detail page"""
    
    contract = Contract.query.get_or_404(contract_id)
    
    if contract.client_id != current_user.id:
        abort(403)
    
    return render_template('user/contract_detail.html', contract=contract)

@user_bp.route('/contracts/<int:contract_id>/sign', methods=['POST'])
@login_required
def sign_contract(contract_id):
    """Sign a contract"""
    
    contract = Contract.query.get_or_404(contract_id)
    
    if contract.client_id != current_user.id:
        abort(403)
    
    # In a real implementation, you would handle digital signature
    # For now, we'll just mark it as signed
    contract.status = 'signed'
    contract.signed_at = datetime.utcnow()
    contract.client_signature = f"Digitally signed by {current_user.get_full_name()}"
    
    db.session.commit()
    
    log_activity(current_user.id, 'contract_signed', f'User signed contract: {contract.title}')
    flash('Contract signed successfully!', 'success')
    
    return redirect(url_for('user.contract_detail', contract_id=contract_id))

@user_bp.route('/messages')
@login_required
def messages():
    """List user's messages"""
    
    page = request.args.get('page', 1, type=int)
    message_type = request.args.get('type', 'received')
    
    if message_type == 'sent':
        query = Message.query.filter_by(sender_id=current_user.id)
    else:
        query = Message.query.filter_by(recipient_id=current_user.id)
    
    messages = query.order_by(desc(Message.sent_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Mark received messages as read
    if message_type == 'received':
        unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).all()
        for msg in unread_messages:
            msg.is_read = True
        db.session.commit()
    
    return render_template('user/messages.html', 
                         messages=messages,
                         message_type=message_type)

@user_bp.route('/messages/<int:message_id>')
@login_required
def message_detail(message_id):
    """Message detail page"""
    
    message = Message.query.get_or_404(message_id)
    
    # Check if user can access this message
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        abort(403)
    
    # Mark as read if user is recipient
    if message.recipient_id == current_user.id and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    # Get message thread
    if message.parent_id:
        parent_message = Message.query.get(message.parent_id)
        thread_messages = Message.query.filter_by(parent_id=message.parent_id).order_by(Message.sent_at).all()
    else:
        parent_message = message
        thread_messages = Message.query.filter_by(parent_id=message.id).order_by(Message.sent_at).all()
    
    return render_template('user/message_detail.html', 
                         message=message,
                         parent_message=parent_message,
                         thread_messages=thread_messages)

@user_bp.route('/messages/compose', methods=['GET', 'POST'])
@login_required
def compose_message():
    """Compose a new message"""
    
    form = MessageForm()
    
    # Get admin users for recipient selection
    admin_users = User.query.filter_by(role='admin').all()
    
    # Get user's projects for project selection
    user_projects = Project.query.filter_by(client_id=current_user.id).all()
    
    recipient_id = request.args.get('recipient_id')
    project_id = request.args.get('project_id')
    reply_to = request.args.get('reply_to')
    
    if form.validate_on_submit():
        # Handle file attachment
        attachment_path = None
        if form.attachment.data:
            attachment_path = save_uploaded_file(form.attachment.data, 'message_attachments')
        
        message = Message(
            subject=form.subject.data,
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=form.recipient_id.data or recipient_id,
            project_id=form.project_id.data if form.project_id.data else project_id,
            parent_id=reply_to,
            attachment_path=attachment_path
        )
        
        db.session.add(message)
        db.session.commit()
        
        log_activity(current_user.id, 'message_sent', f'User sent message: {message.subject}')
        flash('Message sent successfully!', 'success')
        
        return redirect(url_for('user.messages'))
    
    return render_template('user/compose_message.html', 
                         form=form,
                         admin_users=admin_users,
                         user_projects=user_projects,
                         recipient_id=recipient_id,
                         project_id=project_id,
                         reply_to=reply_to)

@user_bp.route('/notifications')
@login_required
def notifications():
    """List user's notifications"""
    
    page = request.args.get('page', 1, type=int)
    
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        desc(Notification.created_at)
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Mark notifications as read
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True
    db.session.commit()
    
    return render_template('user/notifications.html', notifications=notifications)

@user_bp.route('/files/<int:file_id>/download')
@login_required
def download_file(file_id):
    """Download a project file"""
    
    file = ProjectFile.query.get_or_404(file_id)
    project = file.project
    
    # Check if user can access this file
    if not current_user.can_access_project(project):
        abort(403)
    
    file_path = os.path.join('uploads', file.file_path)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=file.original_filename)
    else:
        flash('File not found.', 'error')
        return redirect(url_for('user.project_detail', project_id=project.id))
