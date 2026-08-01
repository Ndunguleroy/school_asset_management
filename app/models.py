from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(
        db.Enum('admin', 'department_head', 'staff', 'asset_officer'),
        default='staff'
    )
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    department = db.relationship('Department', backref='users')

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    technician_name = db.Column(db.String(100))
    technician_email = db.Column(db.String(100))
    technician_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    asset_tag = db.Column(db.String(100), unique=True)
    serial_number = db.Column(db.String(100), unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    condition = db.Column(
        db.Enum('new', 'good', 'fair', 'poor', 'damaged', 'lost', 'disposed'),
        default='good'
    )
    status = db.Column(
        db.Enum('available', 'allocated', 'under_maintenance', 'disposed', 'lost', 'damaged'),
        default='available'
    )
    location = db.Column(db.String(200))
    warranty_expiry = db.Column(db.Date)
    date_acquired = db.Column(db.Date)
    description = db.Column(db.Text)
    last_verified_at = db.Column(db.DateTime)
    last_verified_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.relationship('Category', backref='assets')
    department = db.relationship('Department', backref='assets')
    verified_by = db.relationship('User', foreign_keys=[last_verified_by])

class Allocation(db.Model):
    __tablename__ = 'allocations'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    borrow_start_date = db.Column(db.Date, nullable=True)
    expected_return_date = db.Column(db.Date, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    status = db.Column(
        db.Enum('active', 'returned', 'overdue', 'pending_approval'),
        default='active'
    )
    asset = db.relationship('Asset', backref='allocations')
    user = db.relationship('User', backref='allocations', foreign_keys=[user_id])
    department = db.relationship('Department', backref='allocations')

class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    performed_by = db.Column(db.String(100))
    maintenance_type = db.Column(db.String(100))
    cost = db.Column(db.Numeric(10, 2))
    date_performed = db.Column(db.Date, nullable=False)
    next_maintenance_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    asset = db.relationship('Asset', backref='maintenance_records')

class AllocationRequest(db.Model):
    __tablename__ = 'allocation_requests'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    request_type = db.Column(db.Enum('department', 'staff'), default='department')
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'processed'), default='pending')
    reason = db.Column(db.Text)
    borrow_start_date = db.Column(db.Date, nullable=True)
    expected_return_date = db.Column(db.Date, nullable=True)
    borrow_days = db.Column(db.Integer, nullable=True)
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    asset = db.relationship('Asset', backref='allocation_requests')
    requester = db.relationship('User', backref='allocation_requests', foreign_keys=[requested_by])
    department = db.relationship('Department', backref='allocation_requests')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='audit_logs')

class AssetMovement(db.Model):
    __tablename__ = 'asset_movements'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    from_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    to_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    moved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reason = db.Column(db.Text)
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)
    asset = db.relationship('Asset', backref='movements')
    from_department = db.relationship('Department', foreign_keys=[from_department_id])
    to_department = db.relationship('Department', foreign_keys=[to_department_id])
    officer = db.relationship('User', foreign_keys=[moved_by])