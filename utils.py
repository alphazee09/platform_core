from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from app import db
from models import ActivityLog, UserRole

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Admin access required', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def log_activity(user_id, action, description):
    """Log user activity"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
        'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'svg'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_currency(amount, currency='USD'):
    """Format currency for display"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        import os
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except:
        return 0

def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length] + "..."

def get_time_ago(datetime_obj):
    """Get human-readable time ago string"""
    from datetime import datetime
    
    if not datetime_obj:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - datetime_obj
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return datetime_obj.strftime("%B %d, %Y")

def generate_project_id():
    """Generate unique project ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    import unicodedata
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    # Remove non-ASCII characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove any remaining unsafe characters
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    
    return filename

def calculate_project_progress(project):
    """Calculate project progress based on milestones"""
    if not project.milestones:
        return project.progress
    
    total_milestones = len(project.milestones)
    completed_milestones = sum(1 for m in project.milestones if m.is_completed)
    
    return int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0

def get_contract_status_color(status):
    """Get CSS class for contract status"""
    status_colors = {
        'draft': 'secondary',
        'sent': 'warning',
        'signed': 'info',
        'active': 'success',
        'completed': 'primary',
        'expired': 'danger'
    }
    return status_colors.get(status.value if hasattr(status, 'value') else status, 'secondary')

def get_payment_status_color(status):
    """Get CSS class for payment status"""
    status_colors = {
        'pending': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'refunded': 'info'
    }
    return status_colors.get(status.value if hasattr(status, 'value') else status, 'secondary')

def get_project_status_color(status):
    """Get CSS class for project status"""
    status_colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_colors.get(status.value if hasattr(status, 'value') else status, 'secondary')
