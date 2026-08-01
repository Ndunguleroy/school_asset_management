from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Category, Asset
from app import db

categories = Blueprint('categories', __name__)

@categories.route('/categories')
@login_required
def index():
    # Staff cannot access categories
    if current_user.role == 'staff':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('staff.dashboard'))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template('categories/categories.html', categories=all_categories)

@categories.route('/categories/<int:id>/assets')
@login_required
def view_assets(id):
    if current_user.role == 'staff':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('staff.dashboard'))

    category = Category.query.get_or_404(id)

    if current_user.role == 'department_head':
        category_assets = Asset.query.filter_by(
            category_id=id,
            department_id=current_user.department_id
        ).order_by(Asset.name).all()
    else:
        category_assets = Asset.query.filter_by(category_id=id).order_by(Asset.name).all()

    return render_template('categories/category_assets.html',
        category=category,
        assets=category_assets
    )

@categories.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'admin':
        flash('You do not have permission to add categories.', 'danger')
        return redirect(url_for('categories.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        technician_name = request.form.get('technician_name')
        technician_email = request.form.get('technician_email')
        technician_phone = request.form.get('technician_phone')

        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('Category already exists.', 'danger')
            return redirect(url_for('categories.add'))

        new_category = Category(
            name=name,
            description=description,
            technician_name=technician_name,
            technician_email=technician_email,
            technician_phone=technician_phone
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/add_category.html')

@categories.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit categories.', 'danger')
        return redirect(url_for('categories.index'))

    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.technician_name = request.form.get('technician_name')
        category.technician_email = request.form.get('technician_email')
        category.technician_phone = request.form.get('technician_phone')
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/edit_category.html', category=category)

@categories.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete categories.', 'danger')
        return redirect(url_for('categories.index'))

    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('categories.index'))