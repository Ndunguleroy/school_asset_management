from app import create_app, db
from app.models import User, Department, Category, Asset, Allocation, Maintenance, AllocationRequest, AuditLog, AssetMovement

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)