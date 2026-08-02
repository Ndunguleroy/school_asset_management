from app import create_app, db
from app.models import User, Department, Category, Asset
from werkzeug.security import generate_password_hash
from datetime import date

app = create_app()

with app.app_context():

    # ─── DEPARTMENTS ────────────────────────────────────────────
    departments_data = [
        {'name': 'Information Technology', 'school': 'School of Technology'},
        {'name': 'Computer Science', 'school': 'School of Technology'},
        {'name': 'Electrical Engineering', 'school': 'School of Technology'},
        {'name': 'Education', 'school': 'School of Education'},
        {'name': 'Early Childhood', 'school': 'School of Education'},
        {'name': 'Business Administration', 'school': 'School of Business'},
        {'name': 'Accounting', 'school': 'School of Business'},
        {'name': 'Marketing', 'school': 'School of Business'},
        {'name': 'Administration', 'school': 'General'},
        {'name': 'Library', 'school': 'General'},
    ]

    for d in departments_data:
        exists = Department.query.filter_by(name=d['name']).first()
        if not exists:
            db.session.add(Department(name=d['name'], school=d['school']))

    db.session.commit()
    print("Departments seeded.")

    # ─── CATEGORIES ─────────────────────────────────────────────
    categories_data = [
        {
            'name': 'Computers',
            'description': 'Desktop and laptop computers',
            'technician_name': 'James Mwangi',
            'technician_email': 'james.mwangi@school.ac.ke',
            'technician_phone': '0712345601'
        },
        {
            'name': 'Printers',
            'description': 'Printers and photocopiers',
            'technician_name': 'Grace Wanjiku',
            'technician_email': 'grace.wanjiku@school.ac.ke',
            'technician_phone': '0712345602'
        },
        {
            'name': 'Projectors',
            'description': 'Projectors and display equipment',
            'technician_name': 'Brian Otieno',
            'technician_email': 'brian.otieno@school.ac.ke',
            'technician_phone': '0712345603'
        },
        {
            'name': 'Furniture',
            'description': 'Desks, chairs and other furniture',
            'technician_name': 'Mary Akinyi',
            'technician_email': 'mary.akinyi@school.ac.ke',
            'technician_phone': '0712345604'
        },
        {
            'name': 'Laboratory Equipment',
            'description': 'Scientific and technical lab tools',
            'technician_name': 'Peter Kamau',
            'technician_email': 'peter.kamau@school.ac.ke',
            'technician_phone': '0712345605'
        },
        {
            'name': 'Vehicles',
            'description': 'School owned vehicles',
            'technician_name': 'Samuel Njoroge',
            'technician_email': 'samuel.njoroge@school.ac.ke',
            'technician_phone': '0712345606'
        },
        {
            'name': 'Networking Equipment',
            'description': 'Routers, switches and cables',
            'technician_name': 'Alice Wambui',
            'technician_email': 'alice.wambui@school.ac.ke',
            'technician_phone': '0712345607'
        },
        {
            'name': 'Audio Visual',
            'description': 'Speakers, microphones and screens',
            'technician_name': 'David Kipchoge',
            'technician_email': 'david.kipchoge@school.ac.ke',
            'technician_phone': '0712345608'
        },
    ]

    for c in categories_data:
        exists = Category.query.filter_by(name=c['name']).first()
        if not exists:
            db.session.add(Category(
                name=c['name'],
                description=c['description'],
                technician_name=c['technician_name'],
                technician_email=c['technician_email'],
                technician_phone=c['technician_phone']
            ))

    db.session.commit()
    print("Categories seeded.")

    # ─── USERS ──────────────────────────────────────────────────
    users_data = [
        {
            'full_name': 'System Admin',
            'email': 'admin@school.ac.ke',
            'password': 'admin123',
            'role': 'admin',
            'department': 'Administration'
        },
        {
            'full_name': 'Asset Officer',
            'email': 'officer@school.ac.ke',
            'password': 'officer123',
            'role': 'asset_officer',
            'department': 'Administration'
        },
        {
            'full_name': 'John Kamau',
            'email': 'john.kamau@school.ac.ke',
            'password': 'password123',
            'role': 'department_head',
            'department': 'Information Technology'
        },
        {
            'full_name': 'Jane Wanjiru',
            'email': 'jane.wanjiru@school.ac.ke',
            'password': 'password123',
            'role': 'department_head',
            'department': 'Business Administration'
        },
        {
            'full_name': 'Mark Odhiambo',
            'email': 'mark.odhiambo@school.ac.ke',
            'password': 'password123',
            'role': 'staff',
            'department': 'Computer Science'
        },
        {
            'full_name': 'Sarah Chebet',
            'email': 'sarah.chebet@school.ac.ke',
            'password': 'password123',
            'role': 'staff',
            'department': 'Education'
        },
    ]

    for u in users_data:
        exists = User.query.filter_by(email=u['email']).first()
        if not exists:
            dept = Department.query.filter_by(name=u['department']).first()
            db.session.add(User(
                full_name=u['full_name'],
                email=u['email'],
                password=generate_password_hash(u['password']),
                role=u['role'],
                department_id=dept.id if dept else None,
                is_active=True
            ))

    db.session.commit()
    print("Users seeded.")

    # ─── ASSETS ─────────────────────────────────────────────────
    assets_data = [
        {
            'name': 'Dell Latitude Laptop',
            'asset_tag': 'TAG-001',
            'serial_number': 'DL-001',
            'category': 'Computers',
            'department': 'Information Technology',
            'condition': 'good',
            'status': 'available',
            'location': 'Block A Room 101',
            'date_acquired': date(2023, 1, 15),
            'warranty_expiry': date(2026, 1, 15),
            'description': 'Dell Latitude 5520 laptop'
        },
        {
            'name': 'HP ProDesk Desktop',
            'asset_tag': 'TAG-002',
            'serial_number': 'HP-001',
            'category': 'Computers',
            'department': 'Computer Science',
            'condition': 'good',
            'status': 'available',
            'location': 'Block B Lab 1',
            'date_acquired': date(2023, 2, 10),
            'warranty_expiry': date(2026, 2, 10),
            'description': 'HP ProDesk 400 desktop computer'
        },
        {
            'name': 'Lenovo ThinkPad',
            'asset_tag': 'TAG-003',
            'serial_number': 'LN-001',
            'category': 'Computers',
            'department': 'Business Administration',
            'condition': 'new',
            'status': 'available',
            'location': 'Block C Room 201',
            'date_acquired': date(2024, 1, 5),
            'warranty_expiry': date(2027, 1, 5),
            'description': 'Lenovo ThinkPad E15 laptop'
        },
        {
            'name': 'Lenovo IdeaPad',
            'asset_tag': 'TAG-004',
            'serial_number': 'LN-002',
            'category': 'Computers',
            'department': 'Electrical Engineering',
            'condition': 'good',
            'status': 'available',
            'location': 'Block D Lab 2',
            'date_acquired': date(2023, 5, 20),
            'warranty_expiry': date(2026, 5, 20),
            'description': 'Lenovo IdeaPad 3 laptop'
        },
        {
            'name': 'Canon PIXMA Printer',
            'asset_tag': 'TAG-005',
            'serial_number': 'CP-001',
            'category': 'Printers',
            'department': 'Administration',
            'condition': 'good',
            'status': 'available',
            'location': 'Admin Block Room 001',
            'date_acquired': date(2022, 6, 20),
            'warranty_expiry': date(2025, 6, 20),
            'description': 'Canon PIXMA office printer'
        },
        {
            'name': 'HP LaserJet Printer',
            'asset_tag': 'TAG-006',
            'serial_number': 'HPP-001',
            'category': 'Printers',
            'department': 'Library',
            'condition': 'fair',
            'status': 'available',
            'location': 'Library Main Hall',
            'date_acquired': date(2021, 7, 8),
            'warranty_expiry': date(2024, 7, 8),
            'description': 'HP LaserJet Pro printer'
        },
        {
            'name': 'Epson EB Projector',
            'asset_tag': 'TAG-007',
            'serial_number': 'EP-001',
            'category': 'Projectors',
            'department': 'Education',
            'condition': 'good',
            'status': 'available',
            'location': 'Lecture Hall 1',
            'date_acquired': date(2022, 8, 15),
            'warranty_expiry': date(2025, 8, 15),
            'description': 'Epson EB-X41 projector'
        },
        {
            'name': 'BenQ MH560 Projector',
            'asset_tag': 'TAG-008',
            'serial_number': 'BQ-001',
            'category': 'Projectors',
            'department': 'Business Administration',
            'condition': 'fair',
            'status': 'available',
            'location': 'Boardroom 1',
            'date_acquired': date(2021, 3, 10),
            'warranty_expiry': date(2024, 3, 10),
            'description': 'BenQ MH560 projector'
        },
        {
            'name': 'Office Desk Set',
            'asset_tag': 'TAG-009',
            'serial_number': 'OD-001',
            'category': 'Furniture',
            'department': 'Administration',
            'condition': 'good',
            'status': 'available',
            'location': 'Admin Block Room 002',
            'date_acquired': date(2020, 5, 1),
            'warranty_expiry': None,
            'description': 'Standard office desk and chair set'
        },
        {
            'name': 'Student Chair Set',
            'asset_tag': 'TAG-010',
            'serial_number': 'SC-001',
            'category': 'Furniture',
            'department': 'Education',
            'condition': 'fair',
            'status': 'available',
            'location': 'Lecture Hall 2',
            'date_acquired': date(2019, 8, 10),
            'warranty_expiry': None,
            'description': 'Set of 30 student chairs'
        },
        {
            'name': 'Binocular Microscope',
            'asset_tag': 'TAG-011',
            'serial_number': 'LM-001',
            'category': 'Laboratory Equipment',
            'department': 'Electrical Engineering',
            'condition': 'good',
            'status': 'available',
            'location': 'Science Lab 1',
            'date_acquired': date(2022, 9, 20),
            'warranty_expiry': date(2025, 9, 20),
            'description': 'Binocular compound microscope'
        },
        {
            'name': 'Oscilloscope',
            'asset_tag': 'TAG-012',
            'serial_number': 'OS-001',
            'category': 'Laboratory Equipment',
            'department': 'Electrical Engineering',
            'condition': 'good',
            'status': 'available',
            'location': 'Electronics Lab',
            'date_acquired': date(2022, 11, 5),
            'warranty_expiry': date(2025, 11, 5),
            'description': 'Digital oscilloscope 4 channel'
        },
        {
            'name': 'Cisco Catalyst Switch',
            'asset_tag': 'TAG-013',
            'serial_number': 'CS-001',
            'category': 'Networking Equipment',
            'department': 'Information Technology',
            'condition': 'new',
            'status': 'available',
            'location': 'Server Room',
            'date_acquired': date(2024, 2, 1),
            'warranty_expiry': date(2027, 2, 1),
            'description': 'Cisco Catalyst 2960 24 port switch'
        },
        {
            'name': 'TP Link Router',
            'asset_tag': 'TAG-014',
            'serial_number': 'TR-001',
            'category': 'Networking Equipment',
            'department': 'Information Technology',
            'condition': 'good',
            'status': 'available',
            'location': 'Server Room',
            'date_acquired': date(2023, 3, 15),
            'warranty_expiry': date(2026, 3, 15),
            'description': 'TP Link AC1750 wireless router'
        },
        {
            'name': 'Sony Wireless Microphone',
            'asset_tag': 'TAG-015',
            'serial_number': 'SM-001',
            'category': 'Audio Visual',
            'department': 'Education',
            'condition': 'good',
            'status': 'available',
            'location': 'Lecture Hall 1',
            'date_acquired': date(2023, 4, 12),
            'warranty_expiry': date(2026, 4, 12),
            'description': 'Sony wireless microphone set'
        },
        {
            'name': 'Samsung Smart TV',
            'asset_tag': 'TAG-016',
            'serial_number': 'SS-001',
            'category': 'Audio Visual',
            'department': 'Business Administration',
            'condition': 'good',
            'status': 'available',
            'location': 'Boardroom 2',
            'date_acquired': date(2023, 6, 1),
            'warranty_expiry': date(2026, 6, 1),
            'description': 'Samsung 65 inch Smart TV'
        },
        {
            'name': 'Toyota Hiace Van',
            'asset_tag': 'TAG-017',
            'serial_number': 'TH-001',
            'category': 'Vehicles',
            'department': 'Administration',
            'condition': 'good',
            'status': 'available',
            'location': 'Parking Lot',
            'date_acquired': date(2020, 11, 30),
            'warranty_expiry': None,
            'description': 'School transport van 14 seater'
        },
        {
            'name': 'Isuzu Double Cab',
            'asset_tag': 'TAG-018',
            'serial_number': 'ID-001',
            'category': 'Vehicles',
            'department': 'Administration',
            'condition': 'good',
            'status': 'available',
            'location': 'Parking Lot',
            'date_acquired': date(2021, 4, 15),
            'warranty_expiry': None,
            'description': 'Administration pickup truck'
        },
        {
            'name': 'MacBook Pro',
            'asset_tag': 'TAG-019',
            'serial_number': 'MB-001',
            'category': 'Computers',
            'department': 'Marketing',
            'condition': 'new',
            'status': 'available',
            'location': 'Block C Room 301',
            'date_acquired': date(2024, 3, 10),
            'warranty_expiry': date(2027, 3, 10),
            'description': 'Apple MacBook Pro M3'
        },
        {
            'name': 'Accounting Workstation',
            'asset_tag': 'TAG-020',
            'serial_number': 'AW-001',
            'category': 'Computers',
            'department': 'Accounting',
            'condition': 'good',
            'status': 'available',
            'location': 'Block C Room 401',
            'date_acquired': date(2023, 8, 20),
            'warranty_expiry': date(2026, 8, 20),
            'description': 'HP workstation for accounting software'
        },
    ]

    for a in assets_data:
        exists = Asset.query.filter_by(serial_number=a['serial_number']).first()
        if not exists:
            category = Category.query.filter_by(name=a['category']).first()
            department = Department.query.filter_by(name=a['department']).first()
            if category and department:
                db.session.add(Asset(
                    name=a['name'],
                    asset_tag=a['asset_tag'],
                    serial_number=a['serial_number'],
                    category_id=category.id,
                    department_id=department.id,
                    condition=a['condition'],
                    status=a['status'],
                    location=a['location'],
                    date_acquired=a['date_acquired'],
                    warranty_expiry=a['warranty_expiry'],
                    description=a['description']
                ))

    db.session.commit()
    print("Assets seeded.")

    print("")
    print("All seed data added successfully!")
    print("")
    print("Login credentials:")
    print("Admin        — admin@school.ac.ke          / admin123")
    print("Asset Officer — officer@school.ac.ke        / officer123")
    print("Dept Head    — john.kamau@school.ac.ke     / password123")
    print("Dept Head    — jane.wanjiru@school.ac.ke   / password123")
    print("Staff        — mark.odhiambo@school.ac.ke  / password123")
    print("Staff        — sarah.chebet@school.ac.ke   / password123")