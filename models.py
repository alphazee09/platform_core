from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum
import secrets
import string

class UserRole(enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"

class ProjectStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ContractStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class EmailVerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_token():
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    @classmethod
    def create_for_user(cls, user_id):
        token = cls.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        verification_token = cls(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(verification_token)
        db.session.commit()
        return verification_token
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    id_card_path = db.Column(db.String(255), nullable=True)
    signature_path = db.Column(db.String(255), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    company = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', backref='client', lazy=True)
    contracts = db.relationship('Contract', backref='client', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy=True)
    blog_posts = db.relationship('BlogPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    verification_tokens = db.relationship('EmailVerificationToken', backref='user', lazy=True)
    followed_projects = db.relationship('ProjectFollower', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_unread_messages_count(self):
        return Message.query.filter_by(recipient_id=self.id, is_read=False).count()
    
    def can_access_project(self, project):
        return self.role == UserRole.ADMIN or project.client_id == self.id

class ProjectFollower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id'),)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PENDING, nullable=False)
    progress = db.Column(db.Integer, default=0)  # Percentage
    priority = db.Column(db.String(20), default='medium')
    technologies = db.Column(db.String(500), nullable=True)  # Comma-separated
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    repository_url = db.Column(db.String(500), nullable=True)
    demo_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = db.relationship('ProjectFile', backref='project', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    followers = db.relationship('ProjectFollower', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def get_completion_percentage(self):
        if not self.milestones:
            return 0
        completed = sum(1 for m in self.milestones if m.is_completed)
        return int((completed / len(self.milestones)) * 100)
    
    def get_total_payments(self):
        return sum(p.amount for p in Payment.query.filter_by(project_id=self.id, status=PaymentStatus.COMPLETED))

class ProjectFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    payment_percentage = db.Column(db.Float, default=0)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    terms = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    client_signature = db.Column(db.String(500), nullable=True)
    admin_signature = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='OMR')  # Changed to OMR for Thawani
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method = db.Column(db.String(50), default='thawani')  # thawani, stripe, bank
    thawani_session_id = db.Column(db.String(255), nullable=True)
    thawani_payment_id = db.Column(db.String(255), nullable=True)
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)
    stripe_session_id = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)  # Project-wise messaging
    is_read = db.Column(db.Boolean, default=False)
    attachment_path = db.Column(db.String(500), nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referential relationship for threading
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated
    featured_image = db.Column(db.String(255), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    likes = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referential relationship for nested comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

class GitHubRepo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(50), nullable=True)
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
