from app import create_app, db
from app.models import Category, Department

app = create_app()

with app.app_context():

    # Add default categories
    categories = [
        Category(name='Computers', description='Desktop and laptop computers'),
        Category(name='Printers', description='Printers and photocopiers'),
        Category(name='Projectors', description='Projectors and display equipment'),
        Category(name='Furniture', description='Desks, chairs and other furniture'),
        Category(name='Laboratory Equipment', description='Scientific and technical lab tools'),
        Category(name='Vehicles', description='School owned vehicles'),
        Category(name='Networking Equipment', description='Routers, switches and cables'),
        Category(name='Audio Visual', description='Speakers, microphones and screens'),
    ]

    # Add default departments
    departments = [
        Department(name='Information Technology', school='School of Technology'),
        Department(name='Computer Science', school='School of Technology'),
        Department(name='Electrical Engineering', school='School of Technology'),
        Department(name='Education', school='School of Education'),
        Department(name='Early Childhood', school='School of Education'),
        Department(name='Business Administration', school='School of Business'),
        Department(name='Accounting', school='School of Business'),
        Department(name='Marketing', school='School of Business'),
        Department(name='Administration', school='General'),
        Department(name='Library', school='General'),
    ]

    db.session.bulk_save_objects(categories)
    db.session.bulk_save_objects(departments)
    db.session.commit()

    print("Default categories and departments added successfully!")