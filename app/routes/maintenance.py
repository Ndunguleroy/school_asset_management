from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Maintenance, Asset, Category
from app import db

maintenance = Blueprint('maintenance', __name__)

@maintenance.route('/maintenance')
@login_required
def index():
    if current_user.role == 'staff':
        flash('You do not have permission to access maintenance records.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if current_user.role == 'asset_officer':
        return redirect(url_for('asset_officer.dashboard'))

    if current_user.role == 'department_head':
        dept_asset_ids = [
            a.id for a in Asset.query.filter_by(
                department_id=current_user.department_id
            ).all()
        ]
        active = Maintenance.query.join(Asset).filter(
            Asset.id.in_(dept_asset_ids),
            Asset.status == 'under_maintenance'
        ).order_by(Maintenance.date_performed.desc()).all()

        completed = Maintenance.query.join(Asset).filter(
            Asset.id.in_(dept_asset_ids),
            Asset.status != 'under_maintenance'
        ).order_by(Maintenance.date_performed.desc()).all()
    else:
        active = Maintenance.query.join(Asset).filter(
            Asset.status == 'under_maintenance'
        ).order_by(Maintenance.date_performed.desc()).all()

        completed = Maintenance.query.join(Asset).filter(
            Asset.status != 'under_maintenance'
        ).order_by(Maintenance.date_performed.desc()).all()

    return render_template('maintenance/maintenance.html',
        active=active,
        completed=completed
    )

@maintenance.route('/maintenance/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin']:
        flash('You do not have permission to add maintenance records.', 'danger')
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        return redirect(url_for('maintenance.index'))

    assets = Asset.query.all()
    categories = Category.query.filter(Category.technician_name != None).all()

    asset_technician_map = {
        a.id: {
            'technician': a.category.technician_name,
            'category': a.category.name
        } for a in assets if a.category and a.category.technician_name
    }

    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        performed_by = request.form.get('performed_by')
        maintenance_type = request.form.get('maintenance_type')
        cost = request.form.get('cost')
        date_performed = request.form.get('date_performed')
        next_maintenance_date = request.form.get('next_maintenance_date')
        notes = request.form.get('notes')

        new_maintenance = Maintenance(
            asset_id=asset_id,
            performed_by=performed_by,
            maintenance_type=maintenance_type,
            cost=cost if cost else None,
            date_performed=date_performed,
            next_maintenance_date=next_maintenance_date if next_maintenance_date else None,
            notes=notes
        )

        asset = Asset.query.get(asset_id)
        asset.status = 'under_maintenance'

        db.session.add(new_maintenance)
        db.session.commit()
        flash('Maintenance record added successfully!', 'success')
        return redirect(url_for('maintenance.index'))

    return render_template('maintenance/add_maintenance.html',
        assets=assets,
        categories=categories,
        asset_technician_map=asset_technician_map
    )

@maintenance.route('/maintenance/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin']:
        flash('You do not have permission to edit maintenance records.', 'danger')
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        return redirect(url_for('maintenance.index'))

    record = Maintenance.query.get_or_404(id)
    assets = Asset.query.all()
    categories = Category.query.filter(Category.technician_name != None).all()

    if record.asset.status != 'under_maintenance':
        flash('Completed maintenance records cannot be edited.', 'danger')
        return redirect(url_for('maintenance.index'))

    if request.method == 'POST':
        record.asset_id = request.form.get('asset_id')
        record.performed_by = request.form.get('performed_by')
        record.maintenance_type = request.form.get('maintenance_type')
        record.cost = request.form.get('cost') or None
        record.date_performed = request.form.get('date_performed')
        record.next_maintenance_date = request.form.get('next_maintenance_date') or None
        record.notes = request.form.get('notes')

        db.session.commit()
        flash('Maintenance record updated successfully!', 'success')
        return redirect(url_for('maintenance.index'))

    return render_template('maintenance/edit_maintenance.html',
        record=record,
        assets=assets,
        categories=categories
    )

@maintenance.route('/maintenance/complete/<int:id>', methods=['POST'])
@login_required
def complete(id):
    if current_user.role not in ['admin']:
        flash('You do not have permission to complete maintenance records.', 'danger')
        return redirect(url_for('maintenance.index'))

    record = Maintenance.query.get_or_404(id)
    asset = Asset.query.get(record.asset_id)
    asset.status = 'available'
    db.session.commit()
    flash('Maintenance completed. Asset is now available!', 'success')
    return redirect(url_for('maintenance.index'))

@maintenance.route('/maintenance/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin']:
        flash('You do not have permission to delete maintenance records.', 'danger')
        return redirect(url_for('maintenance.index'))

    record = Maintenance.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Maintenance record deleted successfully!', 'success')
    return redirect(url_for('maintenance.index'))