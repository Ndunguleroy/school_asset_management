from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Department, Asset
from app import db

departments = Blueprint('departments', __name__)

@departments.route('/departments')
@login_required
def index():
    if current_user.role == 'staff':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('staff.dashboard'))

    all_departments = Department.query.order_by(Department.school, Department.name).all()

    default_department = None
    if current_user.role == 'department_head':
        default_department = Department.query.get(current_user.department_id)

    return render_template('departments/departments.html',
        departments=all_departments,
        default_department=default_department
    )

@departments.route('/departments/<int:id>/assets')
@login_required
def view_assets(id):
    if current_user.role == 'staff':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('staff.dashboard'))

    department = Department.query.get_or_404(id)
    department_assets = Asset.query.filter_by(department_id=id).order_by(Asset.name).all()

    is_own_department = (
        current_user.role in ['admin', 'asset_officer'] or
        current_user.department_id == id
    )

    all_departments = Department.query.order_by(Department.school, Department.name).all()

    return render_template('departments/department_assets.html',
        department=department,
        assets=department_assets,
        is_own_department=is_own_department,
        all_departments=all_departments
    )

@departments.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'admin':
        flash('You do not have permission to add departments.', 'danger')
        return redirect(url_for('departments.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        school = request.form.get('school')

        existing = Department.query.filter_by(name=name).first()
        if existing:
            flash('Department already exists.', 'danger')
            return redirect(url_for('departments.add'))

        new_department = Department(name=name, school=school)
        db.session.add(new_department)
        db.session.commit()
        flash('Department added successfully!', 'success')
        return redirect(url_for('departments.index'))

    return render_template('departments/add_department.html')

@departments.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit departments.', 'danger')
        return redirect(url_for('departments.index'))

    department = Department.query.get_or_404(id)

    if request.method == 'POST':
        department.name = request.form.get('name')
        department.school = request.form.get('school')
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('departments.index'))

    return render_template('departments/edit_department.html', department=department)

@departments.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete departments.', 'danger')
        return redirect(url_for('departments.index'))

    department = Department.query.get_or_404(id)
    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully!', 'success')
    return redirect(url_for('departments.index'))