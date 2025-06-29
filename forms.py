from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SelectField, FloatField, BooleanField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=300)])
    profile_image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20)])
    project_type = SelectField('Project Type', choices=[
        ('web_app', 'Web Application'),
        ('mobile_app', 'Mobile Application'),
        ('desktop_app', 'Desktop Application'),
        ('api', 'API Development'),
        ('ecommerce', 'E-commerce'),
        ('cms', 'Content Management System'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    technologies = StringField('Technologies', validators=[Optional(), Length(max=500)])
    budget = FloatField('Budget', validators=[Optional(), NumberRange(min=1)])
    deadline = DateTimeField('Deadline', validators=[Optional()], format='%Y-%m-%d')
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')

class MessageForm(FlaskForm):
    recipient_id = HiddenField('Recipient ID')
    project_id = HiddenField('Project ID', validators=[Optional()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])
    attachment = FileField('Attachment', validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'png'])])

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=50)])
    excerpt = TextAreaField('Excerpt', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('technology', 'Technology'),
        ('web_development', 'Web Development'),
        ('mobile_development', 'Mobile Development'),
        ('design', 'Design'),
        ('business', 'Business'),
        ('tutorials', 'Tutorials'),
        ('news', 'News')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=500)])
    featured_image = FileField('Featured Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    is_published = BooleanField('Publish immediately')
    is_featured = BooleanField('Feature this post')

class ContractForm(FlaskForm):
    title = StringField('Contract Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Contract Content', validators=[DataRequired(), Length(min=100)])
    terms = TextAreaField('Terms & Conditions', validators=[Optional()])
    total_amount = FloatField('Total Amount', validators=[DataRequired(), NumberRange(min=1)])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    project_id = SelectField('Project', coerce=int, validators=[Optional()])

class MilestoneForm(FlaskForm):
    title = StringField('Milestone Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    due_date = DateTimeField('Due Date', validators=[Optional()], format='%Y-%m-%d')
    payment_percentage = FloatField('Payment Percentage', validators=[Optional(), NumberRange(min=0, max=100)])

class PaymentForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    currency = SelectField('Currency', choices=[
        ('OMR', 'Omani Rial'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro')
    ], default='OMR')
    description = StringField('Description', validators=[Optional(), Length(max=500)])
    project_id = SelectField('Project', coerce=int, validators=[Optional()])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField('Category', choices=[
        ('all', 'All'),
        ('projects', 'Projects'),
        ('users', 'Users'),
        ('blog', 'Blog Posts')
    ], default='all')
