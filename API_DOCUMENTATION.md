# Software Engineering Platform - API Documentation

## Overview
A comprehensive platform for managing software engineering projects, client relationships, contracts, payments, and communications. Built with Flask and PostgreSQL.

## Base URL
- Development: `http://localhost:5000`
- Production: `https://your-domain.replit.app`

## Authentication
The platform uses Flask-Login for session-based authentication. Users must be logged in to access most endpoints.

### User Roles
- **CLIENT**: Regular users who can submit projects and manage their own data
- **ADMIN**: Administrators with full access to all platform features

---

## Core Endpoints

### 1. Home & Landing
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/` | Landing page with featured content | No | Any |

**Response**: Renders landing page with featured blog posts and GitHub repositories

---

### 2. Authentication Routes (auth.py)
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/auth/login` | Login page | No | Any |
| POST | `/auth/login` | Process login | No | Any |
| GET | `/auth/register` | Registration page | No | Any |
| POST | `/auth/register` | Process registration | No | Any |
| GET | `/auth/logout` | Logout user | Yes | Any |
| GET | `/auth/profile` | User profile page | Yes | Any |
| POST | `/auth/profile` | Update profile | Yes | Any |

---

### 3. Dashboard
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/dashboard` | User dashboard | Yes | CLIENT |
| GET | `/admin` | Admin dashboard | Yes | ADMIN |

**Dashboard Response Data**:
- Recent projects (5 latest)
- Recent contracts (5 latest)
- Unread messages (5 latest)

**Admin Dashboard Response Data**:
- Total users count
- Total projects count
- Active contracts count
- Pending payments count
- Recent activities (10 latest)
- Unverified users list

---

### 4. Project Management

#### Project Listing & Creation
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/projects` | List user's projects | Yes | Any |
| GET | `/projects/create` | Create project form | Yes | CLIENT |
| POST | `/projects/create` | Submit new project | Yes | CLIENT |

#### Project Wizard (Public)
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/project-wizard` | Public project submission wizard | No | Any |
| POST | `/project-wizard/submit` | Submit project via wizard | No | Any |

**Project Wizard Form Fields**:
```json
{
  "project_title": "string",
  "project_type": "string",
  "project_description": "string",
  "budget_range": "string",
  "deadline": "YYYY-MM-DD",
  "client_email": "string",
  "client_name": "string",
  "target_audience": "string",
  "industry": "string",
  "technologies": ["array"],
  "platforms": ["array"],
  "integrations": "string",
  "urgency": "string",
  "payment_preference": "string",
  "special_requirements": "string",
  "design_preferences": "string",
  "color_scheme": "string",
  "inspiration_links": "string",
  "project_files": "file[]"
}
```

**Project Wizard Response**:
```json
{
  "success": true,
  "message": "Project submitted successfully!",
  "project_id": 123,
  "user_created": "username_or_null"
}
```

---

### 5. Contract Management
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/contracts` | List contracts | Yes | Any |

---

### 6. Payment Processing
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/payments` | List payments | Yes | Any |
| POST | `/create-checkout-session` | Create Stripe checkout | Yes | Any |
| GET | `/payment/success/<payment_id>` | Payment success callback | Yes | Any |
| GET | `/payment/cancel/<payment_id>` | Payment cancel callback | Yes | Any |

**Stripe Integration**:
- Uses Stripe Checkout for payment processing
- Supports multiple currencies
- Automatic payment status updates
- Success/cancel redirect handling

---

### 7. Messaging System
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/messages` | List messages | Yes | Any |
| POST | `/messages/send` | Send new message | Yes | Any |

**Message Form Fields**:
```json
{
  "subject": "string",
  "content": "string",
  "recipient_id": "int (optional)",
  "attachment": "file (optional)"
}
```

---

### 8. Blog System
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/blog` | List blog posts | No | Any |
| GET | `/blog/<post_id>` | View blog post | No | Any |

**Blog Query Parameters**:
- `page`: Page number for pagination
- `category`: Filter by category

---

### 9. GitHub Integration
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/github` | List GitHub repositories | No | Any |

---

### 10. File Management
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/uploads/<path:filename>` | Serve uploaded files | Yes | Any |

---

## API Endpoints (AJAX/JSON)

### Real-time Updates
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/api/unread-messages` | Get unread message count | Yes | Any |
| GET | `/api/notifications` | Get notification count | Yes | Any |

**Response Format**:
```json
{
  "count": 5
}
```

### Interactive Actions
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/mark-message-read/<message_id>` | Mark message as read | Yes | Any |
| POST | `/api/like-post/<post_id>` | Like a blog post | No | Any |
| POST | `/api/verify-user/<user_id>` | Verify user account | Yes | ADMIN |
| POST | `/api/update-project-status/<project_id>` | Update project status | Yes | ADMIN |

**Project Status Update Request**:
```json
{
  "status": "in_progress|completed|cancelled",
  "progress": 50
}
```

---

## Static Pages
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/privacy` | Privacy policy | No | Any |
| GET | `/terms` | Terms of service | No | Any |
| GET | `/latest-projects` | Public project showcase | No | Any |

---

## Data Models

### User
```json
{
  "id": "int",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "role": "CLIENT|ADMIN",
  "is_verified": "boolean",
  "profile_image": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Project
```json
{
  "id": "int",
  "title": "string",
  "description": "text",
  "project_type": "string",
  "budget": "float",
  "deadline": "datetime",
  "status": "PENDING|IN_PROGRESS|COMPLETED|CANCELLED",
  "progress": "int (0-100)",
  "client_id": "int",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Contract
```json
{
  "id": "int",
  "title": "string",
  "content": "text",
  "terms": "text",
  "total_amount": "float",
  "status": "DRAFT|SENT|SIGNED|ACTIVE|COMPLETED|EXPIRED",
  "client_id": "int",
  "project_id": "int",
  "signed_at": "datetime",
  "expires_at": "datetime",
  "created_at": "datetime"
}
```

### Payment
```json
{
  "id": "int",
  "amount": "float",
  "currency": "string",
  "description": "string",
  "status": "PENDING|COMPLETED|FAILED|REFUNDED",
  "stripe_payment_intent_id": "string",
  "stripe_session_id": "string",
  "user_id": "int",
  "project_id": "int",
  "paid_at": "datetime",
  "created_at": "datetime"
}
```

### Message
```json
{
  "id": "int",
  "subject": "string",
  "content": "text",
  "sender_id": "int",
  "recipient_id": "int",
  "parent_id": "int",
  "is_read": "boolean",
  "attachment_path": "string",
  "sent_at": "datetime"
}
```

---

## Error Handling

### HTTP Status Codes
- `200`: Success
- `303`: Redirect (for Stripe checkout)
- `400`: Bad Request
- `403`: Forbidden/Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information"
}
```

---

## File Upload Configuration

### Allowed File Types
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`
- Documents: `.pdf`, `.doc`, `.docx`, `.txt`
- Archives: `.zip`, `.rar`
- Code: `.py`, `.js`, `.html`, `.css`

### Upload Limits
- Maximum file size: 16MB per file
- Multiple files supported for project submissions

### Storage Structure
```
uploads/
├── projects/          # Project-related files
├── messages/          # Message attachments
├── profiles/          # Profile images
└── documents/         # General documents
```

---

## Environment Variables Required

```env
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_...
SESSION_SECRET=your-secret-key
UPLOAD_FOLDER=uploads
```

---

## Features Summary

### ✅ Implemented Features
1. **User Authentication & Authorization**
   - Registration, login, logout
   - Role-based access control
   - Profile management

2. **Project Management**
   - Public project wizard with auto-account creation
   - Project creation and listing
   - File upload support
   - Status tracking and progress updates

3. **Payment Processing**
   - Stripe integration
   - Checkout session creation
   - Payment status tracking
   - Success/cancel handling

4. **Communication System**
   - Internal messaging
   - File attachments
   - Read status tracking
   - Admin-client communication

5. **Content Management**
   - Blog system with categories
   - GitHub repository showcase
   - Comment system
   - Like functionality

6. **Admin Features**
   - Dashboard with statistics
   - User verification
   - Project status management
   - Activity logging

7. **File Management**
   - Secure file uploads
   - Multiple file type support
   - Organized storage structure

8. **Real-time Features**
   - Unread message counts
   - Notification system
   - AJAX-powered interactions

### 🔄 Interactive Features
- Project wizard walkthrough with tooltips
- Neon border animations
- Futuristic loading animations
- Real-time form validation
- Responsive design with mobile optimization

### 🎨 UI/UX Features
- 2050-style futuristic design
- Social media integration
- Clean button styling
- Enhanced typography
- Smooth animations and transitions

---

## Usage Examples

### Submit Project via Wizard
```javascript
const formData = new FormData();
formData.append('project_title', 'My Web Application');
formData.append('project_type', 'web_development');
formData.append('client_email', 'client@example.com');
// ... other fields

fetch('/project-wizard/submit', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Create Stripe Checkout
```javascript
const response = await fetch('/create-checkout-session', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'payment_id=123'
});
// Automatically redirects to Stripe
```

### Get Unread Messages
```javascript
fetch('/api/unread-messages')
.then(response => response.json())
.then(data => {
    updateNotificationBadge(data.count);
});
```

This platform provides a complete solution for software engineering project management with modern web technologies, secure payment processing, and an intuitive user experience.