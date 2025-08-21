# backend/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from ..services import auth_service

auth_routes = Blueprint('auth', __name__,
                        template_folder='../templates',
                        url_prefix='/auth')

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # Redirect to the new homepage if already logged in
        return redirect(url_for('products.list_products'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        new_user, message = auth_service.create_user(username, password)
        if new_user:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')

    return render_template('register.html', title='Register')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to the new homepage if already logged in
        return redirect(url_for('products.list_products'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me') is not None
        user = auth_service.authenticate_user(username, password)
        if user:
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            # If there's no safe next page, redirect to the products list
            if not next_page or urlparse(next_page).netloc != '':
                # --- THIS IS THE FIX ---
                next_page = url_for('products.list_products')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', title='Sign In')

@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))