from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Allocation, Asset, User, Department, AuditLog
from app import db
from datetime import datetime, date

allocations = Blueprint('allocations', __name__)

def log_action(user_id, action, details):
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(log)

@allocations.route('/allocations')
@login_required
def index():
    if current_user.role == 'staff':
        return redirect(url_for('staff.dashboard'))
    if current_user.role == 'asset_officer':
        return redirect(url_for('asset_officer.allocations'))

    if current_user.role == 'department_head':
        active = Allocation.query.filter(
            Allocation.department_id == current_user.department_id,
            Allocation.status.in_(['active', 'overdue'])
        ).order_by(Allocation.allocated_at.desc()).all()

        returned = Allocation.query.filter(
            Allocation.department_id == current_user.department_id,
            Allocation.status == 'returned'
        ).order_by(Allocation.returned_at.desc()).all()
    else:
        active = Allocation.query.filter(
            Allocation.status.in_(['active', 'overdue'])
        ).order_by(Allocation.allocated_at.desc()).all()

        returned = Allocation.query.filter(
            Allocation.status == 'returned'
        ).order_by(Allocation.returned_at.desc()).all()

    today = date.today()

    # Update overdue
    for allocation in active:
        if allocation.expected_return_date and allocation.expected_return_date < today:
            if allocation.status != 'overdue':
                allocation.status = 'overdue'
    db.session.commit()

    return render_template('allocations/allocations.html',
        active=active,
        returned=returned,
        today=today
    )

@allocations.route('/allocations/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'admin':
        flash('You do not have permission to allocate assets.', 'danger')
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        return redirect(url_for('allocations.index'))

    assets = Asset.query.filter_by(status='available').all()
    users = User.query.all()
    departments = Department.query.all()

    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        user_id = request.form.get('user_id')
        department_id = request.form.get('department_id')
        notes = request.form.get('notes')
        borrow_start_date = request.form.get('borrow_start_date')
        expected_return_date = request.form.get('expected_return_date')

        asset = Asset.query.get(asset_id)
        if not asset or asset.status != 'available':
            flash('This asset is not available.', 'danger')
            return redirect(url_for('allocations.add'))

        new_allocation = Allocation(
            asset_id=asset_id,
            user_id=user_id,
            department_id=department_id,
            borrow_start_date=borrow_start_date if borrow_start_date else None,
            expected_return_date=expected_return_date if expected_return_date else None,
            notes=notes,
            status='active'
        )
        asset.status = 'allocated'
        db.session.add(new_allocation)
        log_action(
            current_user.id,
            'ASSET_ALLOCATED',
            f'Admin {current_user.full_name} allocated asset {asset.name} to user ID {user_id}'
        )
        db.session.commit()
        flash('Asset allocated successfully!', 'success')
        return redirect(url_for('allocations.index'))

    return render_template('allocations/add_allocation.html',
        assets=assets,
        users=users,
        departments=departments
    )

@allocations.route('/allocations/view/<int:id>')
@login_required
def view(id):
    allocation = Allocation.query.get_or_404(id)

    if current_user.role == 'staff':
        if allocation.user_id != current_user.id:
            flash('You can only view your own allocations.', 'danger')
            return redirect(url_for('staff.dashboard'))

    if current_user.role == 'department_head':
        if allocation.department_id != current_user.department_id:
            flash('You do not have permission to view this allocation.', 'danger')
            return redirect(url_for('allocations.index'))

    today = date.today()
    return render_template('allocations/view_allocation.html',
        allocation=allocation,
        today=today
    )

@allocations.route('/allocations/return/<int:id>', methods=['POST'])
@login_required
def return_asset(id):
    allocation = Allocation.query.get_or_404(id)

    if current_user.role == 'staff':
        flash('Please use the return option from your dashboard.', 'warning')
        return redirect(url_for('staff.dashboard'))

    if current_user.role not in ['admin']:
        flash('You do not have permission to return assets.', 'danger')
        return redirect(url_for('allocations.index'))

    allocation.returned_at = datetime.utcnow()
    allocation.status = 'returned'
    asset = Asset.query.get(allocation.asset_id)
    asset.status = 'available'

    log_action(
        current_user.id,
        'ASSET_RETURNED',
        f'Admin {current_user.full_name} processed return of asset {asset.name}'
    )
    db.session.commit()
    flash('Asset returned successfully!', 'success')
    return redirect(url_for('allocations.index'))

@allocations.route('/allocations/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete allocations.', 'danger')
        return redirect(url_for('allocations.index'))

    allocation = Allocation.query.get_or_404(id)
    asset = Asset.query.get(allocation.asset_id)
    asset.status = 'available'
    db.session.delete(allocation)
    db.session.commit()
    flash('Allocation deleted successfully!', 'success')
    return redirect(url_for('allocations.index'))