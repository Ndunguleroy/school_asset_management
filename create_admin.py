from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check if admin already exists
    existing = User.query.filter_by(email='admin@school.ac.ke').first()
    if existing:
        print('Admin account already exists.')
    else:
        admin = User(
            full_name='System Admin',
            email='admin@school.ac.ke',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin account created successfully!')
        print('')
        print('Email   : admin@school.ac.ke')
        print('Password: admin123')
        print('')
        print('Please change the password after first login.')