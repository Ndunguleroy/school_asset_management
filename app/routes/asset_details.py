from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Asset, Allocation, Maintenance, AllocationRequest

asset_details_bp = Blueprint('asset_details', __name__)

@asset_details_bp.route('/asset/<int:id>/details')
@login_required
def view(id):
    asset = Asset.query.get_or_404(id)

    # Get current allocation if any
    current_allocation = Allocation.query.filter(
        Allocation.asset_id == id,
        Allocation.status.in_(['active', 'overdue'])
    ).first()

    # Get allocation history based on role
    if current_user.role == 'staff':
        allocation_history = Allocation.query.filter_by(
            asset_id=id,
            user_id=current_user.id
        ).order_by(Allocation.allocated_at.desc()).all()
    elif current_user.role == 'department_head':
        allocation_history = Allocation.query.filter_by(
            asset_id=id,
            department_id=current_user.department_id
        ).order_by(Allocation.allocated_at.desc()).all()
    else:
        allocation_history = Allocation.query.filter_by(
            asset_id=id
        ).order_by(Allocation.allocated_at.desc()).all()

    # Maintenance history — only admin and department head
    maintenance_history = []
    if current_user.role in ['admin', 'department_head']:
        maintenance_history = Maintenance.query.filter_by(
            asset_id=id
        ).order_by(Maintenance.date_performed.desc()).all()

    # Check if staff can request this asset
    can_request = False
    if current_user.role == 'staff' and asset.status == 'available':
        existing_request = AllocationRequest.query.filter_by(
            asset_id=id,
            requested_by=current_user.id,
            status='pending'
        ).first()
        can_request = not existing_request

    return render_template('assets/asset_details.html',
        asset=asset,
        current_allocation=current_allocation,
        allocation_history=allocation_history,
        maintenance_history=maintenance_history,
        can_request=can_request
    )