from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Asset, Category, Department, Allocation, Maintenance
from app import db

assets = Blueprint('assets', __name__)

def _can_manage_assets():
    return current_user.role in ['admin', 'asset_officer']

def _can_view_all_assets():
    return current_user.role in ['admin', 'asset_officer', 'department_head']

@assets.route('/assets')
@login_required
def index():
    # Staff go to their own dashboard
    if current_user.role == 'staff':
        return redirect(url_for('staff.dashboard'))
    # Asset officer goes to their own dashboard
    if current_user.role == 'asset_officer':
        return redirect(url_for('asset_officer.dashboard'))

    if current_user.role == 'department_head':
        dept_id = current_user.department_id
        total_assets = Asset.query.filter_by(department_id=dept_id).count()
        available_assets = Asset.query.filter_by(department_id=dept_id, status='available').count()
        allocated_assets = Asset.query.filter_by(department_id=dept_id, status='allocated').count()
        under_maintenance = Asset.query.filter_by(department_id=dept_id, status='under_maintenance').count()
        recent_assets = Asset.query.filter_by(department_id=dept_id).order_by(Asset.created_at.desc()).limit(5).all()
    else:
        total_assets = Asset.query.count()
        available_assets = Asset.query.filter_by(status='available').count()
        allocated_assets = Asset.query.filter_by(status='allocated').count()
        under_maintenance = Asset.query.filter_by(status='under_maintenance').count()
        recent_assets = Asset.query.order_by(Asset.created_at.desc()).limit(5).all()

    total_categories = Category.query.count()
    total_departments = Department.query.count()
    total_allocations = Allocation.query.count()
    total_maintenance = Maintenance.query.count()

    return render_template('assets/dashboard.html',
        total_assets=total_assets,
        total_categories=total_categories,
        total_departments=total_departments,
        total_allocations=total_allocations,
        total_maintenance=total_maintenance,
        available_assets=available_assets,
        allocated_assets=allocated_assets,
        under_maintenance=under_maintenance,
        recent_assets=recent_assets
    )

@assets.route('/assets/all')
@login_required
def all_assets():
    if current_user.role == 'staff':
        return redirect(url_for('staff.dashboard'))
    if current_user.role == 'asset_officer':
        return redirect(url_for('asset_officer.all_assets'))

    if current_user.role == 'department_head':
        all_assets_list = Asset.query.filter_by(
            department_id=current_user.department_id
        ).order_by(Asset.created_at.desc()).all()
    else:
        all_assets_list = Asset.query.order_by(Asset.created_at.desc()).all()

    return render_template('assets/all_assets.html', assets=all_assets_list)

@assets.route('/assets/add', methods=['GET', 'POST'])
@assets.route('/assets/add/category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def add(category_id=None):
    # Only admin and department head can add assets through this route
    # Asset officers use their own route
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to add assets.', 'danger')
        return redirect(url_for('assets.index'))

    categories = Category.query.all()

    if current_user.role == 'department_head':
        departments = Department.query.filter_by(id=current_user.department_id).all()
    else:
        departments = Department.query.all()

    locked_category = None
    if category_id:
        locked_category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name')
        serial_number = request.form.get('serial_number')
        condition = request.form.get('condition')
        status = request.form.get('status')
        date_acquired = request.form.get('date_acquired')
        description = request.form.get('description')

        category_id_to_use = category_id if category_id else request.form.get('category_id')

        if current_user.role == 'department_head':
            department_id = current_user.department_id
        else:
            department_id = request.form.get('department_id')

        # Backend enforcement
        if current_user.role == 'department_head':
            if int(department_id) != int(current_user.department_id):
                flash('You can only add assets to your own department.', 'danger')
                return redirect(url_for('assets.add'))

        new_asset = Asset(
            name=name,
            serial_number=serial_number if serial_number else None,
            category_id=category_id_to_use,
            department_id=department_id,
            condition=condition,
            status=status,
            date_acquired=date_acquired if date_acquired else None,
            description=description
        )
        db.session.add(new_asset)
        db.session.commit()
        flash('Asset added successfully!', 'success')

        if category_id:
            return redirect(url_for('categories.view_assets', id=category_id))
        return redirect(url_for('assets.all_assets'))

    return render_template('assets/add_asset.html',
        categories=categories,
        departments=departments,
        locked_category=locked_category
    )

@assets.route('/assets/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    asset = Asset.query.get_or_404(id)

    # Asset officer uses their own update route
    if current_user.role == 'asset_officer':
        return redirect(url_for('asset_officer.update_asset', id=id))

    if current_user.role == 'staff':
        flash('You do not have permission to edit assets.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if current_user.role == 'department_head':
        if asset.department_id != current_user.department_id:
            flash('You can only edit assets in your department.', 'danger')
            return redirect(url_for('assets.index'))

    categories = Category.query.all()

    if current_user.role == 'department_head':
        departments = Department.query.filter_by(id=current_user.department_id).all()
    else:
        departments = Department.query.all()

    if request.method == 'POST':
        asset.name = request.form.get('name')
        asset.serial_number = request.form.get('serial_number') or None
        asset.category_id = request.form.get('category_id')
        asset.condition = request.form.get('condition')
        asset.status = request.form.get('status')
        asset.date_acquired = request.form.get('date_acquired') or None
        asset.description = request.form.get('description')

        if current_user.role == 'admin':
            asset.department_id = request.form.get('department_id')
        else:
            requested_dept = request.form.get('department_id')
            if requested_dept and int(requested_dept) != int(current_user.department_id):
                flash('You cannot move assets to another department.', 'danger')
                return redirect(url_for('assets.edit', id=id))

        db.session.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('assets.all_assets'))

    return render_template('assets/edit_asset.html',
        asset=asset,
        categories=categories,
        departments=departments
    )

@assets.route('/assets/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete assets.', 'danger')
        return redirect(url_for('assets.index'))

    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('assets.all_assets'))