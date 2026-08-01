from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Allocation, AllocationRequest, Asset, AuditLog, Department
from app import db
from datetime import datetime, date, timedelta
from functools import wraps

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            flash('This page is for staff members only.', 'danger')
            return redirect(url_for('assets.index'))
        return f(*args, **kwargs)
    return decorated_function

def log_action(action, details):
    log = AuditLog(
        user_id=current_user.id,
        action=action,
        details=details
    )
    db.session.add(log)

@staff_bp.route('/staff/dashboard')
@login_required
@staff_required
def dashboard():
    # Get active allocations for this staff member
    active_allocations = Allocation.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Update overdue status
    today = date.today()
    for allocation in active_allocations:
        if allocation.expected_return_date and allocation.expected_return_date < today:
            allocation.status = 'overdue'
    db.session.commit()

    # Refresh after update
    active_allocations = Allocation.query.filter_by(
        user_id=current_user.id
    ).filter(Allocation.status.in_(['active', 'overdue'])).all()

    returned_allocations = Allocation.query.filter_by(
        user_id=current_user.id,
        status='returned'
    ).order_by(Allocation.returned_at.desc()).limit(5).all()

    pending_requests = AllocationRequest.query.filter_by(
        requested_by=current_user.id,
        status='pending'
    ).all()

    return render_template('staff/dashboard.html',
        active_allocations=active_allocations,
        returned_allocations=returned_allocations,
        pending_requests=pending_requests,
        today=today
    )

@staff_bp.route('/staff/request', methods=['GET', 'POST'])
@login_required
@staff_required
def request_asset():
    # Only available assets
    available_assets = Asset.query.filter_by(status='available').all()
    departments = Department.query.all()

    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        reason = request.form.get('reason')
        borrow_start_date = request.form.get('borrow_start_date')
        expected_return_date = request.form.get('expected_return_date')
        borrow_days = request.form.get('borrow_days')

        # Backend validation — asset must be available
        asset = Asset.query.get(asset_id)
        if not asset or asset.status != 'available':
            flash('This asset is not available for borrowing.', 'danger')
            return redirect(url_for('staff.request_asset'))

        # Check if already requested
        existing = AllocationRequest.query.filter_by(
            asset_id=asset_id,
            requested_by=current_user.id,
            status='pending'
        ).first()
        if existing:
            flash('You already have a pending request for this asset.', 'warning')
            return redirect(url_for('staff.request_asset'))

        # Calculate expected return if borrow days provided
        if borrow_days and not expected_return_date:
            start = datetime.strptime(borrow_start_date, '%Y-%m-%d').date()
            expected_return = start + timedelta(days=int(borrow_days))
            expected_return_date = expected_return.strftime('%Y-%m-%d')

        new_request = AllocationRequest(
            asset_id=asset_id,
            requested_by=current_user.id,
            department_id=current_user.department_id,
            request_type='staff',
            reason=reason,
            borrow_start_date=borrow_start_date,
            expected_return_date=expected_return_date,
            borrow_days=borrow_days if borrow_days else None,
            status='pending'
        )
        db.session.add(new_request)

        log_action(
            'ASSET_REQUEST',
            f'Staff {current_user.full_name} requested asset {asset.name} (ID: {asset.id})'
        )

        db.session.commit()
        flash('Asset request submitted. Waiting for approval.', 'success')
        return redirect(url_for('staff.dashboard'))

    return render_template('staff/request_asset.html',
        assets=available_assets,
        departments=departments,
        today=date.today().strftime('%Y-%m-%d')
    )

@staff_bp.route('/staff/return/<int:allocation_id>', methods=['POST'])
@login_required
@staff_required
def return_asset(allocation_id):
    allocation = Allocation.query.get_or_404(allocation_id)

    # Backend enforcement — only the allocated user can return
    if allocation.user_id != current_user.id:
        flash('You can only return assets allocated to you.', 'danger')
        log_action(
            'UNAUTHORIZED_RETURN_ATTEMPT',
            f'Staff {current_user.full_name} attempted to return asset allocated to another user'
        )
        db.session.commit()
        return redirect(url_for('staff.dashboard'))

    if allocation.status == 'returned':
        flash('This asset has already been returned.', 'warning')
        return redirect(url_for('staff.dashboard'))

    # Process return
    allocation.returned_at = datetime.utcnow()
    allocation.status = 'returned'

    asset = Asset.query.get(allocation.asset_id)
    asset.status = 'available'

    log_action(
        'ASSET_RETURNED',
        f'Staff {current_user.full_name} returned asset {asset.name} (ID: {asset.id})'
    )

    db.session.commit()
    flash('Asset returned successfully!', 'success')
    return redirect(url_for('staff.dashboard'))

@staff_bp.route('/staff/history')
@login_required
@staff_required
def history():
    all_allocations = Allocation.query.filter_by(
        user_id=current_user.id
    ).order_by(Allocation.allocated_at.desc()).all()

    all_requests = AllocationRequest.query.filter_by(
        requested_by=current_user.id
    ).order_by(AllocationRequest.created_at.desc()).all()

    today = date.today()
    return render_template('staff/history.html',
        allocations=all_allocations,
        requests=all_requests,
        today=today
    )

@staff_bp.route('/staff/request/cancel/<int:request_id>', methods=['POST'])
@login_required
@staff_required
def cancel_request(request_id):
    allocation_request = AllocationRequest.query.get_or_404(request_id)

    if allocation_request.requested_by != current_user.id:
        flash('You can only cancel your own requests.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if allocation_request.status != 'pending':
        flash('You can only cancel pending requests.', 'warning')
        return redirect(url_for('staff.dashboard'))

    db.session.delete(allocation_request)
    log_action(
        'REQUEST_CANCELLED',
        f'Staff {current_user.full_name} cancelled request for asset ID {allocation_request.asset_id}'
    )
    db.session.commit()
    flash('Request cancelled successfully.', 'success')
    return redirect(url_for('staff.dashboard'))