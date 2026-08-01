from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        if current_user.role == 'asset_officer':
            return redirect(url_for('asset_officer.dashboard'))
        return redirect(url_for('assets.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with this email.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.password:
            flash('You have not set up your password yet. Please sign up first.', 'warning')
            return redirect(url_for('auth.signup'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Your account is not active. Please contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash('Welcome back, ' + user.full_name + '!', 'success')

        if user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        if user.role == 'asset_officer':
            return redirect(url_for('asset_officer.dashboard'))
        return redirect(url_for('assets.index'))

    return render_template('auth/login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        if current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        if current_user.role == 'asset_officer':
            return redirect(url_for('asset_officer.dashboard'))
        return redirect(url_for('assets.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('This email is not registered in the system. Please contact your administrator.', 'danger')
            return redirect(url_for('auth.signup'))

        if user.password:
            flash('This account already has a password set. Please log in instead.', 'warning')
            return redirect(url_for('auth.login'))

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('auth.signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.signup'))

        user.password = generate_password_hash(password)
        user.is_active = True
        db.session.commit()

        flash('Account activated successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))