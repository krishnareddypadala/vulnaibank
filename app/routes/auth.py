from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # DELIBERATE VULNERABILITY: Plaintext password comparison
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        full_name = request.form.get('full_name', '')
        ssn = request.form.get('ssn', '')
        phone = request.form.get('phone', '')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')

        # DELIBERATE VULNERABILITY: No input validation, plaintext password
        user = User(
            username=username,
            password=password,
            email=email,
            full_name=full_name,
            ssn=ssn,
            phone=phone,
            role='user'
        )
        db.session.add(user)
        db.session.flush()

        # Auto-create checking account
        from app.models import Account
        import random
        account = Account(
            user_id=user.id,
            account_number=f'{random.randint(5000000000, 9999999999)}',
            account_type='checking',
            balance=1000.00  # Starting bonus
        )
        db.session.add(account)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
