from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Asset, Category, Department, Allocation, AssetMovement, \
    AllocationRequest, Maintenance, AuditLog
from app import db
from datetime import datetime, date
from functools import wraps

asset_officer_bp = Blueprint('asset_officer', __name__)

def officer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'asset_officer']:
            flash('You do not have permission to access this page.', 'danger')
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

@asset_officer_bp.route('/officer/dashboard')
@login_required
@officer_required
def dashboard():
    total_assets = Asset.query.count()
    available = Asset.query.filter_by(status='available').count()
    allocated = Asset.query.filter_by(status='allocated').count()
    under_maintenance = Asset.query.filter_by(status='under_maintenance').count()
    damaged = Asset.query.filter_by(status='damaged').count()
    lost = Asset.query.filter_by(status='lost').count()
    disposed = Asset.query.filter_by(status='disposed').count()

    # Pending approved allocation requests to process
    pending_allocations = AllocationRequest.query.filter_by(
        status='approved'
    ).all()

    # Assets with expired or expiring warranty
    today = date.today()
    expiring_warranty = Asset.query.filter(
        Asset.warranty_expiry != None,
        Asset.warranty_expiry >= today
    ).order_by(Asset.warranty_expiry).limit(5).all()

    # Recent movements
    recent_movements = AssetMovement.query.order_by(
        AssetMovement.moved_at.desc()
    ).limit(5).all()

    # Assets not verified in last 30 days
    from datetime import timedelta
    unverified = Asset.query.filter(
        (Asset.last_verified_at == None) |
        (Asset.last_verified_at < datetime.utcnow() - timedelta(days=30))
    ).count()

    return render_template('asset_officer/dashboard.html',
        total_assets=total_assets,
        available=available,
        allocated=allocated,
        under_maintenance=under_maintenance,
        damaged=damaged,
        lost=lost,
        disposed=disposed,
        pending_allocations=pending_allocations,
        expiring_warranty=expiring_warranty,
        recent_movements=recent_movements,
        unverified=unverified,
        today=today
    )

@asset_officer_bp.route('/officer/assets')
@login_required
@officer_required
def all_assets():
    status_filter = request.args.get('status', '')
    department_filter = request.args.get('department', '')
    category_filter = request.args.get('category', '')

    query = Asset.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if department_filter:
        query = query.filter_by(department_id=department_filter)
    if category_filter:
        query = query.filter_by(category_id=category_filter)

    all_assets = query.order_by(Asset.name).all()
    departments = Department.query.order_by(Department.name).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template('asset_officer/all_assets.html',
        assets=all_assets,
        departments=departments,
        categories=categories,
        status_filter=status_filter,
        department_filter=department_filter,
        category_filter=category_filter
    )

@asset_officer_bp.route('/officer/assets/register', methods=['GET', 'POST'])
@login_required
@officer_required
def register_asset():
    categories = Category.query.all()
    departments = Department.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        asset_tag = request.form.get('asset_tag')
        serial_number = request.form.get('serial_number')
        category_id = request.form.get('category_id')
        department_id = request.form.get('department_id')
        condition = request.form.get('condition')
        location = request.form.get('location')
        warranty_expiry = request.form.get('warranty_expiry')
        date_acquired = request.form.get('date_acquired')
        description = request.form.get('description')

        new_asset = Asset(
            name=name,
            asset_tag=asset_tag if asset_tag else None,
            serial_number=serial_number if serial_number else None,
            category_id=category_id,
            department_id=department_id,
            condition=condition,
            status='available',
            location=location,
            warranty_expiry=warranty_expiry if warranty_expiry else None,
            date_acquired=date_acquired if date_acquired else None,
            description=description
        )
        db.session.add(new_asset)
        log_action(
            'ASSET_REGISTERED',
            f'Asset Officer {current_user.full_name} registered new asset: {name}'
        )
        db.session.commit()
        flash('Asset registered successfully!', 'success')
        return redirect(url_for('asset_officer.all_assets'))

    return render_template('asset_officer/register_asset.html',
        categories=categories,
        departments=departments
    )

@asset_officer_bp.route('/officer/assets/update/<int:id>', methods=['GET', 'POST'])
@login_required
@officer_required
def update_asset(id):
    asset = Asset.query.get_or_404(id)
    categories = Category.query.all()
    departments = Department.query.all()

    if request.method == 'POST':
        asset.name = request.form.get('name')
        asset.asset_tag = request.form.get('asset_tag') or None
        asset.serial_number = request.form.get('serial_number') or None
        asset.category_id = request.form.get('category_id')
        asset.department_id = request.form.get('department_id')
        asset.condition = request.form.get('condition')
        asset.status = request.form.get('status')
        asset.location = request.form.get('location')
        asset.warranty_expiry = request.form.get('warranty_expiry') or None
        asset.date_acquired = request.form.get('date_acquired') or None
        asset.description = request.form.get('description')

        log_action(
            'ASSET_UPDATED',
            f'Asset Officer {current_user.full_name} updated asset: {asset.name} (ID: {asset.id})'
        )
        db.session.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('asset_officer.all_assets'))

    return render_template('asset_officer/update_asset.html',
        asset=asset,
        categories=categories,
        departments=departments
    )

@asset_officer_bp.route('/officer/assets/move/<int:id>', methods=['GET', 'POST'])
@login_required
@officer_required
def move_asset(id):
    asset = Asset.query.get_or_404(id)
    departments = Department.query.all()

    if request.method == 'POST':
        to_department_id = request.form.get('to_department_id')
        reason = request.form.get('reason')

        if int(to_department_id) == asset.department_id:
            flash('Asset is already in this department.', 'warning')
            return redirect(url_for('asset_officer.move_asset', id=id))

        movement = AssetMovement(
            asset_id=asset.id,
            from_department_id=asset.department_id,
            to_department_id=to_department_id,
            moved_by=current_user.id,
            reason=reason
        )

        from_dept = Department.query.get(asset.department_id)
        to_dept = Department.query.get(to_department_id)

        asset.department_id = to_department_id

        db.session.add(movement)
        log_action(
            'ASSET_MOVED',
            f'Asset Officer {current_user.full_name} moved asset {asset.name} '
            f'from {from_dept.name} to {to_dept.name}'
        )
        db.session.commit()
        flash(f'Asset moved to {to_dept.name} successfully!', 'success')
        return redirect(url_for('asset_officer.all_assets'))

    return render_template('asset_officer/move_asset.html',
        asset=asset,
        departments=departments
    )

@asset_officer_bp.route('/officer/assets/verify/<int:id>', methods=['POST'])
@login_required
@officer_required
def verify_asset(id):
    asset = Asset.query.get_or_404(id)
    condition = request.form.get('condition')

    asset.last_verified_at = datetime.utcnow()
    asset.last_verified_by = current_user.id
    if condition:
        asset.condition = condition

    log_action(
        'ASSET_VERIFIED',
        f'Asset Officer {current_user.full_name} verified asset {asset.name} (ID: {asset.id})'
    )
    db.session.commit()
    flash('Asset verified successfully!', 'success')
    return redirect(url_for('asset_officer.all_assets'))

@asset_officer_bp.route('/officer/allocations')
@login_required
@officer_required
def allocations():
    # Show approved requests that need to be processed
    approved_requests = AllocationRequest.query.filter_by(
        status='approved'
    ).order_by(AllocationRequest.updated_at.desc()).all()

    # Show active allocations
    active_allocations = Allocation.query.filter(
        Allocation.status.in_(['active', 'overdue'])
    ).order_by(Allocation.allocated_at.desc()).all()

    today = date.today()
    return render_template('asset_officer/allocations.html',
        approved_requests=approved_requests,
        active_allocations=active_allocations,
        today=today
    )

@asset_officer_bp.route('/officer/allocations/process/<int:id>', methods=['POST'])
@login_required
@officer_required
def process_allocation(id):
    allocation_request = AllocationRequest.query.get_or_404(id)

    if allocation_request.status != 'approved':
        flash('Only approved requests can be processed.', 'warning')
        return redirect(url_for('asset_officer.allocations'))

    asset = Asset.query.get(allocation_request.asset_id)

    if asset.status != 'available':
        flash('This asset is no longer available.', 'danger')
        return redirect(url_for('asset_officer.allocations'))

    # Create the allocation
    new_allocation = Allocation(
        asset_id=allocation_request.asset_id,
        user_id=allocation_request.requested_by,
        department_id=allocation_request.department_id,
        borrow_start_date=allocation_request.borrow_start_date,
        expected_return_date=allocation_request.expected_return_date,
        notes=f'Processed by Asset Officer {current_user.full_name}',
        status='active'
    )

    asset.status = 'allocated'
    allocation_request.status = 'processed'

    db.session.add(new_allocation)
    log_action(
        'ALLOCATION_PROCESSED',
        f'Asset Officer {current_user.full_name} processed allocation of '
        f'{asset.name} to {allocation_request.requester.full_name}'
    )
    db.session.commit()
    flash('Allocation processed and asset assigned successfully!', 'success')
    return redirect(url_for('asset_officer.allocations'))

@asset_officer_bp.route('/officer/returns')
@login_required
@officer_required
def returns():
    active_allocations = Allocation.query.filter(
        Allocation.status.in_(['active', 'overdue'])
    ).order_by(Allocation.allocated_at.desc()).all()

    today = date.today()
    return render_template('asset_officer/returns.html',
        allocations=active_allocations,
        today=today
    )

@asset_officer_bp.route('/officer/returns/process/<int:id>', methods=['POST'])
@login_required
@officer_required
def process_return(id):
    allocation = Allocation.query.get_or_404(id)
    condition_after = request.form.get('condition_after')
    notes = request.form.get('notes')

    asset = Asset.query.get(allocation.asset_id)

    # Update allocation
    allocation.returned_at = datetime.utcnow()
    allocation.status = 'returned'
    if notes:
        allocation.notes = (allocation.notes or '') + f' | Return note: {notes}'

    # Update asset condition and status
    asset.condition = condition_after
    asset.status = 'available'
    asset.last_verified_at = datetime.utcnow()
    asset.last_verified_by = current_user.id

    log_action(
        'RETURN_PROCESSED',
        f'Asset Officer {current_user.full_name} processed return of asset '
        f'{asset.name}. Condition after return: {condition_after}'
    )
    db.session.commit()
    flash('Return processed and asset condition updated!', 'success')
    return redirect(url_for('asset_officer.returns'))

@asset_officer_bp.route('/officer/stocktake')
@login_required
@officer_required
def stocktake():
    from datetime import timedelta
    today = date.today()

    all_assets = Asset.query.order_by(Asset.department_id, Asset.name).all()
    departments = Department.query.order_by(Department.name).all()

    unverified = Asset.query.filter(
        (Asset.last_verified_at == None) |
        (Asset.last_verified_at < datetime.utcnow() - timedelta(days=30))
    ).all()

    return render_template('asset_officer/stocktake.html',
        assets=all_assets,
        departments=departments,
        unverified=unverified,
        today=today
    )

@asset_officer_bp.route('/officer/movements')
@login_required
@officer_required
def movements():
    all_movements = AssetMovement.query.order_by(
        AssetMovement.moved_at.desc()
    ).all()
    return render_template('asset_officer/movements.html',
        movements=all_movements
    )

@asset_officer_bp.route('/officer/reports')
@login_required
@officer_required
def reports():
    total_assets = Asset.query.count()
    available = Asset.query.filter_by(status='available').count()
    allocated = Asset.query.filter_by(status='allocated').count()
    under_maintenance = Asset.query.filter_by(status='under_maintenance').count()
    damaged = Asset.query.filter_by(status='damaged').count()
    lost = Asset.query.filter_by(status='lost').count()
    disposed = Asset.query.filter_by(status='disposed').count()

    assets_by_department = []
    departments = Department.query.all()
    for dept in departments:
        count = Asset.query.filter_by(department_id=dept.id).count()
        assets_by_department.append({'name': dept.name, 'count': count})

    assets_by_category = []
    categories = Category.query.all()
    for cat in categories:
        count = Asset.query.filter_by(category_id=cat.id).count()
        assets_by_category.append({'name': cat.name, 'count': count})

    all_assets = Asset.query.order_by(Asset.department_id, Asset.name).all()

    return render_template('asset_officer/reports.html',
        total_assets=total_assets,
        available=available,
        allocated=allocated,
        under_maintenance=under_maintenance,
        damaged=damaged,
        lost=lost,
        disposed=disposed,
        assets_by_department=assets_by_department,
        assets_by_category=assets_by_category,
        all_assets=all_assets
    )