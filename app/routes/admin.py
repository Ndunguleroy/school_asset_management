from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Department, AuditLog, Allocation, AllocationRequest, AssetMovement
from app import db
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('assets.index'))
        return f(*args, **kwargs)
    return decorated_function

def send_signup_email(user):
    try:
        import resend
        import os
        resend.api_key = os.environ.get('RESEND_API_KEY')

        params = {
            "from": "School AMS <onboarding@resend.dev>",
            "to": [user.email],
            "subject": "Your School AMS Account Has Been Created",
            "html": f"""
                <h2>Hello {user.full_name},</h2>
                <p>Your account has been created on the
                <strong>School Asset Management System</strong>.</p>
                <p><strong>Your account details:</strong></p>
                <ul>
                    <li>Name: {user.full_name}</li>
                    <li>Email: {user.email}</li>
                    <li>Role: {user.role.replace('_', ' ').title()}</li>
                </ul>
                <p>To activate your account please click the link below
                and set your password:</p>
                <p>
                    <a href="https://school-asset-management.vercel.app/signup"
                       style="background:#0d6efd;color:white;padding:10px 20px;
                       text-decoration:none;border-radius:5px;">
                        Activate My Account
                    </a>
                </p>
                <p>Use the email address above when setting up your password.</p>
                <p>You will not be able to log in until you have set your password.</p>
                <br>
                <p>Regards,<br>School Asset Management System</p>
            """
        }

        resend.Emails.send(params)
        return True
    except Exception as e:
        print('Resend email error:', e)
        return False

@admin.route('/admin/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.role, User.full_name).all()
    return render_template('admin/users.html', users=all_users)

@admin.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role')
        department_id = request.form.get('department_id')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('admin.add_user'))

        new_user = User(
            full_name=full_name,
            email=email,
            role=role,
            department_id=department_id if department_id else None,
            is_active=False,
            password=None
        )
        db.session.add(new_user)
        db.session.commit()

        email_sent = send_signup_email(new_user)
        if email_sent:
            flash(f'Account created and invitation email sent to {email}.', 'success')
        else:
            flash(f'Account created but email could not be sent. Please inform {full_name} manually.', 'warning')

        return redirect(url_for('admin.users'))

    return render_template('admin/add_user.html', departments=departments)

@admin.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        department_id = request.form.get('department_id')
        user.department_id = department_id if department_id else None
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', user=user, departments=departments)

@admin.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        # Nullify user references in related records
        # instead of deleting them to preserve history
        Allocation.query.filter_by(user_id=user.id).update(
            {'user_id': None},
            synchronize_session=False
        )
        AllocationRequest.query.filter_by(requested_by=user.id).update(
            {'requested_by': None},
            synchronize_session=False
        )
        AuditLog.query.filter_by(user_id=user.id).update(
            {'user_id': None},
            synchronize_session=False
        )
        AssetMovement.query.filter_by(moved_by=user.id).update(
            {'moved_by': None},
            synchronize_session=False
        )

        # Nullify asset last_verified_by
        from app.models import Asset
        Asset.query.filter_by(last_verified_by=user.id).update(
            {'last_verified_by': None},
            synchronize_session=False
        )

        db.session.delete(user)
        db.session.commit()
        flash(f'{user.full_name} has been deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Could not delete user. Error: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))

@admin.route('/admin/users/reset/<int:id>', methods=['POST'])
@login_required
@admin_required
def reset_user(id):
    user = User.query.get_or_404(id)
    user.password = None
    user.is_active = False
    db.session.commit()

    email_sent = send_signup_email(user)
    if email_sent:
        flash('Password reset and invitation email resent successfully.', 'success')
    else:
        flash('Password reset but email could not be sent.', 'warning')

    return redirect(url_for('admin.users'))

@admin.route('/admin/users/resend/<int:id>', methods=['POST'])
@login_required
@admin_required
def resend_email(id):
    user = User.query.get_or_404(id)
    email_sent = send_signup_email(user)
    if email_sent:
        flash(f'Invitation email resent to {user.email}.', 'success')
    else:
        flash('Email could not be sent. Please check your mail settings.', 'danger')
    return redirect(url_for('admin.users'))