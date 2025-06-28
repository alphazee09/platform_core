from app import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create an admin user
    admin_email = "admin@example.com"
    admin_username = "admin"
    admin_password = "adminpassword"
    if not User.query.filter_by(email=admin_email).first():
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            role=UserRole.ADMIN,
            is_verified=True
        )
        db.session.add(admin_user)
        print(f"Admin user {admin_username} created.")
    else:
        print(f"Admin user {admin_username} already exists.")

    # Create a regular user
    user_email = "user@example.com"
    user_username = "user"
    user_password = "userpassword"
    if not User.query.filter_by(email=user_email).first():
        regular_user = User(
            username=user_username,
            email=user_email,
            password_hash=generate_password_hash(user_password),
            role=UserRole.CLIENT,
            is_verified=True
        )
        db.session.add(regular_user)
        print(f"Regular user {user_username} created.")
    else:
        print(f"Regular user {user_username} already exists.")

    db.session.commit()
    print("Database seeding complete.")

