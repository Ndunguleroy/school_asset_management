from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Asset, Category, Department, Allocation, Maintenance
from sqlalchemy import func
from app import db

reports = Blueprint('reports', __name__)

def _reports_allowed():
    return current_user.role in ['admin', 'department_head']

@reports.route('/reports')
@login_required
def index():
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to access reports.', 'danger')
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        if current_user.role == 'asset_officer':
            return redirect(url_for('asset_officer.reports'))
        return redirect(url_for('assets.index'))

    return render_template('reports/reports.html')

@reports.route('/reports/inventory')
@login_required
def inventory():
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to access this report.', 'danger')
        return redirect(url_for('assets.index'))

    if current_user.role == 'department_head':
        all_assets = Asset.query.filter_by(
            department_id=current_user.department_id
        ).order_by(Asset.name).all()
        total_assets = len(all_assets)
        available = sum(1 for a in all_assets if a.status == 'available')
        allocated = sum(1 for a in all_assets if a.status == 'allocated')
        under_maintenance = sum(1 for a in all_assets if a.status == 'under_maintenance')
        disposed = sum(1 for a in all_assets if a.status == 'disposed')
    else:
        all_assets = Asset.query.order_by(Asset.department_id).all()
        total_assets = Asset.query.count()
        available = Asset.query.filter_by(status='available').count()
        allocated = Asset.query.filter_by(status='allocated').count()
        under_maintenance = Asset.query.filter_by(status='under_maintenance').count()
        disposed = Asset.query.filter_by(status='disposed').count()

    categories = Category.query.all()
    departments = Department.query.all()

    return render_template('reports/inventory.html',
        assets=all_assets,
        total_assets=total_assets,
        available=available,
        allocated=allocated,
        under_maintenance=under_maintenance,
        disposed=disposed,
        categories=categories,
        departments=departments
    )

@reports.route('/reports/maintenance')
@login_required
def maintenance():
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to access this report.', 'danger')
        return redirect(url_for('assets.index'))

    all_maintenance = Maintenance.query.order_by(Maintenance.date_performed.desc()).all()
    total_records = Maintenance.query.count()
    active = Maintenance.query.join(Asset).filter(Asset.status == 'under_maintenance').count()
    completed = Maintenance.query.join(Asset).filter(Asset.status != 'under_maintenance').count()

    return render_template('reports/maintenance.html',
        maintenance=all_maintenance,
        total_records=total_records,
        active=active,
        completed=completed
    )

@reports.route('/reports/allocations')
@login_required
def allocations():
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to access this report.', 'danger')
        return redirect(url_for('assets.index'))

    all_allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).all()
    total = Allocation.query.count()
    active = Allocation.query.filter_by(returned_at=None).count()
    returned = Allocation.query.filter(Allocation.returned_at != None).count()

    return render_template('reports/allocations.html',
        allocations=all_allocations,
        total=total,
        active=active,
        returned=returned
    )

@reports.route('/reports/maintenance-cost')
@login_required
def maintenance_cost():
    if current_user.role != 'admin':
        flash('You do not have permission to access this report.', 'danger')
        return redirect(url_for('assets.index'))

    asset_costs = db.session.query(
        Asset.name,
        Asset.serial_number,
        Category.name.label('category'),
        Department.name.label('department'),
        func.count(Maintenance.id).label('total_records'),
        func.coalesce(func.sum(Maintenance.cost), 0).label('total_cost')
    ).join(Maintenance, Maintenance.asset_id == Asset.id)\
     .join(Category, Category.id == Asset.category_id)\
     .join(Department, Department.id == Asset.department_id)\
     .group_by(Asset.id)\
     .order_by(func.sum(Maintenance.cost).desc())\
     .all()

    category_costs = db.session.query(
        Category.name.label('category'),
        func.count(Maintenance.id).label('total_records'),
        func.coalesce(func.sum(Maintenance.cost), 0).label('total_cost')
    ).join(Asset, Asset.category_id == Category.id)\
     .join(Maintenance, Maintenance.asset_id == Asset.id)\
     .group_by(Category.id)\
     .order_by(func.sum(Maintenance.cost).desc())\
     .all()

    overall_total = db.session.query(
        func.coalesce(func.sum(Maintenance.cost), 0)
    ).scalar()

    total_records = Maintenance.query.count()

    return render_template('reports/maintenance_cost.html',
        asset_costs=asset_costs,
        category_costs=category_costs,
        overall_total=overall_total,
        total_records=total_records
    )

@reports.route('/reports/asset-condition')
@login_required
def asset_condition():
    if current_user.role not in ['admin', 'department_head']:
        flash('You do not have permission to access this report.', 'danger')
        return redirect(url_for('assets.index'))

    new_count = Asset.query.filter_by(condition='new').count()
    good_count = Asset.query.filter_by(condition='good').count()
    fair_count = Asset.query.filter_by(condition='fair').count()
    poor_count = Asset.query.filter_by(condition='poor').count()
    total = Asset.query.count()

    category_condition = db.session.query(
        Category.name.label('category'),
        func.sum(func.IF(Asset.condition == 'new', 1, 0)).label('new'),
        func.sum(func.IF(Asset.condition == 'good', 1, 0)).label('good'),
        func.sum(func.IF(Asset.condition == 'fair', 1, 0)).label('fair'),
        func.sum(func.IF(Asset.condition == 'poor', 1, 0)).label('poor'),
        func.count(Asset.id).label('total')
    ).join(Asset, Asset.category_id == Category.id)\
     .group_by(Category.id)\
     .order_by(Category.name)\
     .all()

    attention_assets = Asset.query.filter(
        Asset.condition.in_(['poor', 'fair'])
    ).order_by(Asset.condition).all()

    return render_template('reports/asset_condition.html',
        new_count=new_count,
        good_count=good_count,
        fair_count=fair_count,
        poor_count=poor_count,
        total=total,
        category_condition=category_condition,
        attention_assets=attention_assets
    )