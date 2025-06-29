import os
import secrets
import string
from werkzeug.utils import secure_filename
from flask import current_app, abort
from flask_login import current_user
from functools import wraps
import logging
from datetime import datetime

from app import db
from models import ActivityLog, UserRole

def log_activity(user_id, action, description, ip_address=None, user_agent=None):
    """Log user activity"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
        logging.info(f"Activity logged: {action} - {description}")
    except Exception as e:
        logging.error(f"Failed to log activity: {str(e)}")

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
            'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z'
        }
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_filename(original_filename):
    """Generate a secure filename"""
    if not original_filename:
        return None
    
    # Get file extension
    ext = ''
    if '.' in original_filename:
        ext = '.' + original_filename.rsplit('.', 1)[1].lower()
    
    # Generate random filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    return f"{timestamp}_{random_str}{ext}"

def save_uploaded_file(file, subfolder='general'):
    """Save uploaded file and return filename"""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = generate_filename(file.filename)
        if not filename:
            return None
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return os.path.join(subfolder, filename)
        
    except Exception as e:
        logging.error(f"File upload error: {str(e)}")
        return None

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except:
        return 0

def format_currency(amount, currency='OMR'):
    """Format currency for display"""
    if currency == 'OMR':
        return f"{amount:.3f} OMR"
    elif currency == 'USD':
        return f"${amount:.2f}"
    elif currency == 'EUR':
        return f"€{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def get_project_status_color(status):
    """Get color class for project status"""
    status_colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_colors.get(status.value if hasattr(status, 'value') else status, 'secondary')

def get_payment_status_color(status):
    """Get color class for payment status"""
    status_colors = {
        'pending': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'refunded': 'info'
    }
    return status_colors.get(status.value if hasattr(status, 'value') else status, 'secondary')

def calculate_project_progress(project):
    """Calculate project progress based on milestones"""
    if not project.milestones:
        return project.progress or 0
    
    completed_milestones = sum(1 for m in project.milestones if m.is_completed)
    total_milestones = len(project.milestones)
    
    if total_milestones == 0:
        return 0
    
    return int((completed_milestones / total_milestones) * 100)

def send_notification(user_id, title, message, type='info', action_url=None):
    """Send notification to user"""
    try:
        from models import Notification
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            action_url=action_url
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"Notification sent to user {user_id}: {title}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send notification: {str(e)}")
        return False

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    if not filename:
        return None
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename

def get_user_avatar_url(user):
    """Get user avatar URL or default"""
    if user.profile_image:
        return url_for('main.uploaded_file', filename=user.profile_image)
    else:
        # Return default avatar based on user initials
        initials = ''
        if user.first_name:
            initials += user.first_name[0].upper()
        if user.last_name:
            initials += user.last_name[0].upper()
        if not initials:
            initials = user.username[0].upper()
        
        # You can use a service like UI Avatars or implement your own default avatar
        return f"https://ui-avatars.com/api/?name={initials}&background=4f46e5&color=ffffff&size=150"

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "Never"
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 7:
        return dt.strftime('%Y-%m-%d %H:%M')
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def get_file_icon(filename):
    """Get icon class for file type"""
    if not filename:
        return 'fa-file'
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    icon_map = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        'txt': 'fa-file-alt',
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
        '7z': 'fa-file-archive',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image'
    }
    
    return icon_map.get(ext, 'fa-file')

