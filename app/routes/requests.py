from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import AllocationRequest, Asset, Department, Allocation, AuditLog, User
from app import db
from datetime import datetime

requests_bp = Blueprint('requests', __name__)

def log_action(user_id, action, details):
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )
    db.session.add(log)

@requests_bp.route('/requests')
@login_required
def index():
    if current_user.role == 'admin':
        # Admin sees all pending requests and department head requests
        pending = AllocationRequest.query.filter_by(
            status='pending'
        ).order_by(AllocationRequest.created_at.desc()).all()

        resolved = AllocationRequest.query.filter(
            AllocationRequest.status != 'pending'
        ).order_by(AllocationRequest.updated_at.desc()).all()

    elif current_user.role == 'department_head':
        # Department head sees only staff requests from their department
        # Their own requests are shown separately
        pending_staff = AllocationRequest.query.filter_by(
            status='pending',
            department_id=current_user.department_id,
            request_type='staff'
        ).order_by(AllocationRequest.created_at.desc()).all()

        my_requests = AllocationRequest.query.filter_by(
            requested_by=current_user.id
        ).order_by(AllocationRequest.created_at.desc()).all()

        resolved_staff = AllocationRequest.query.filter(
            AllocationRequest.status != 'pending',
            AllocationRequest.department_id == current_user.department_id,
            AllocationRequest.request_type == 'staff'
        ).order_by(AllocationRequest.updated_at.desc()).all()

        return render_template('requests/requests.html',
            pending=pending_staff,
            resolved=resolved_staff,
            my_requests=my_requests,
            is_department_head=True
        )
    else:
        pending = []
        resolved = []

    return render_template('requests/requests.html',
        pending=pending,
        resolved=resolved,
        is_department_head=False
    )

@requests_bp.route('/requests/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['department_head']:
        flash('Only department heads can submit department allocation requests.', 'danger')
        return redirect(url_for('requests.index'))

    assets = Asset.query.filter_by(status='available').all()
    department = Department.query.get(current_user.department_id)

    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        reason = request.form.get('reason')

        asset = Asset.query.get(asset_id)
        if not asset or asset.status != 'available':
            flash('This asset is not available.', 'danger')
            return redirect(url_for('requests.add'))

        existing = AllocationRequest.query.filter_by(
            asset_id=asset_id,
            requested_by=current_user.id,
            status='pending'
        ).first()

        if existing:
            flash('You already have a pending request for this asset.', 'warning')
            return redirect(url_for('requests.add'))

        new_request = AllocationRequest(
            asset_id=asset_id,
            requested_by=current_user.id,
            department_id=current_user.department_id,
            request_type='department',
            reason=reason,
            status='pending'
        )
        db.session.add(new_request)
        log_action(
            current_user.id,
            'DEPARTMENT_REQUEST_SUBMITTED',
            f'Department head {current_user.full_name} requested asset {asset.name} — routed to Admin'
        )
        db.session.commit()
        flash('Request submitted to the Administrator for approval.', 'success')
        return redirect(url_for('requests.index'))

    return render_template('requests/add_request.html',
        assets=assets,
        department=department
    )

@requests_bp.route('/requests/approve/<int:id>', methods=['POST'])
@login_required
def approve(id):
    allocation_request = AllocationRequest.query.get_or_404(id)
    admin_notes = request.form.get('admin_notes')

    # Enforce approval hierarchy
    if allocation_request.request_type == 'staff':
        # Staff requests can only be approved by their department head
        if current_user.role != 'department_head':
            flash('Only department heads can approve staff requests.', 'danger')
            log_action(
                current_user.id,
                'UNAUTHORIZED_APPROVAL_ATTEMPT',
                f'{current_user.full_name} attempted to approve a staff request without permission'
            )
            db.session.commit()
            return redirect(url_for('requests.index'))

        if allocation_request.department_id != current_user.department_id:
            flash('You can only approve requests from your own department.', 'danger')
            log_action(
                current_user.id,
                'UNAUTHORIZED_APPROVAL_ATTEMPT',
                f'{current_user.full_name} attempted to approve a request from another department'
            )
            db.session.commit()
            return redirect(url_for('requests.index'))

    elif allocation_request.request_type == 'department':
        # Department head requests can only be approved by admin
        if current_user.role != 'admin':
            flash('Only administrators can approve department head requests.', 'danger')
            log_action(
                current_user.id,
                'UNAUTHORIZED_APPROVAL_ATTEMPT',
                f'{current_user.full_name} attempted to approve a department request without admin rights'
            )
            db.session.commit()
            return redirect(url_for('requests.index'))

    # Check asset still available
    asset = Asset.query.get(allocation_request.asset_id)
    if asset.status != 'available':
        flash('This asset is no longer available.', 'danger')
        allocation_request.status = 'rejected'
        allocation_request.admin_notes = 'Asset no longer available at time of approval.'
        allocation_request.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('requests.index'))

    # Create allocation
    new_allocation = Allocation(
        asset_id=allocation_request.asset_id,
        user_id=allocation_request.requested_by,
        department_id=allocation_request.department_id,
        borrow_start_date=allocation_request.borrow_start_date,
        expected_return_date=allocation_request.expected_return_date,
        notes=f'Approved by {current_user.full_name}. {admin_notes or ""}',
        status='active'
    )

    asset.status = 'allocated'
    allocation_request.status = 'approved'
    allocation_request.admin_notes = admin_notes
    allocation_request.updated_at = datetime.utcnow()

    db.session.add(new_allocation)
    log_action(
        current_user.id,
        'REQUEST_APPROVED',
        f'{current_user.full_name} approved {allocation_request.request_type} request '
        f'for asset {asset.name} to {allocation_request.requester.full_name}'
    )
    db.session.commit()
    flash('Request approved and asset allocated successfully!', 'success')
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/reject/<int:id>', methods=['POST'])
@login_required
def reject(id):
    allocation_request = AllocationRequest.query.get_or_404(id)
    admin_notes = request.form.get('admin_notes')

    # Enforce rejection hierarchy
    if allocation_request.request_type == 'staff':
        if current_user.role != 'department_head':
            flash('Only department heads can reject staff requests.', 'danger')
            log_action(
                current_user.id,
                'UNAUTHORIZED_REJECTION_ATTEMPT',
                f'{current_user.full_name} attempted to reject a staff request without permission'
            )
            db.session.commit()
            return redirect(url_for('requests.index'))

        if allocation_request.department_id != current_user.department_id:
            flash('You can only reject requests from your own department.', 'danger')
            return redirect(url_for('requests.index'))

    elif allocation_request.request_type == 'department':
        if current_user.role != 'admin':
            flash('Only administrators can reject department head requests.', 'danger')
            log_action(
                current_user.id,
                'UNAUTHORIZED_REJECTION_ATTEMPT',
                f'{current_user.full_name} attempted to reject a department request without admin rights'
            )
            db.session.commit()
            return redirect(url_for('requests.index'))

    allocation_request.status = 'rejected'
    allocation_request.admin_notes = admin_notes
    allocation_request.updated_at = datetime.utcnow()

    log_action(
        current_user.id,
        'REQUEST_REJECTED',
        f'{current_user.full_name} rejected {allocation_request.request_type} request '
        f'for asset ID {allocation_request.asset_id}. Reason: {admin_notes or "No reason given"}'
    )
    db.session.commit()
    flash('Request rejected.', 'info')
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    allocation_request = AllocationRequest.query.get_or_404(id)

    if current_user.role != 'admin' and allocation_request.requested_by != current_user.id:
        flash('You do not have permission to delete this request.', 'danger')
        return redirect(url_for('requests.index'))

    if allocation_request.status == 'pending' or current_user.role == 'admin':
        db.session.delete(allocation_request)
        db.session.commit()
        flash('Request deleted successfully.', 'success')
    else:
        flash('You can only delete pending requests.', 'danger')

    return redirect(url_for('requests.index'))