"""Accounts route - LLM02: Sensitive Information Disclosure.

DELIBERATE VULNERABILITIES:
- AI can access any user's account data without authorization
- PII (Aadhaar, email) exposed through AI queries
- No data access controls
- User data queryable by anyone through AI assistant
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Account, Transaction
from sqlalchemy import text

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/accounts')
@login_required
def index():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts.html', accounts=accounts)


@accounts_bp.route('/accounts/<account_number>')
@login_required
def account_detail(account_number):
    """DELIBERATE VULNERABILITY (LLM02): No authorization check - any user can view any account."""
    account = Account.query.filter_by(account_number=account_number).first_or_404()

    transactions = Transaction.query.filter(
        (Transaction.from_account_id == account.id) |
        (Transaction.to_account_id == account.id)
    ).order_by(Transaction.timestamp.desc()).all()

    return render_template('accounts.html',
                           accounts=[account],
                           selected_account=account,
                           transactions=transactions)


@accounts_bp.route('/accounts/search', methods=['POST'])
@login_required
def search_accounts():
    """DELIBERATE VULNERABILITY (LLM02/LLM05): SQL injection via direct query execution."""
    search_term = request.form.get('search', '')

    # DELIBERATE VULNERABILITY: Raw SQL with string formatting
    query = f"SELECT u.username, u.full_name, u.email, u.ssn, a.account_number, a.balance " \
            f"FROM users u JOIN accounts a ON u.id = a.user_id " \
            f"WHERE u.username LIKE '%{search_term}%' OR a.account_number LIKE '%{search_term}%'"

    try:
        result = db.session.execute(text(query))
        rows = [dict(row._mapping) for row in result]
        return jsonify({'results': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@accounts_bp.route('/accounts/all')
@login_required
def all_accounts():
    """DELIBERATE VULNERABILITY (LLM02): Exposes all user data without authorization."""
    if current_user.role != 'admin':
        # Weak check - still returns data via API
        pass

    users = User.query.all()
    data = []
    for user in users:
        accounts = Account.query.filter_by(user_id=user.id).all()
        data.append({
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'ssn': user.ssn,
            'phone': user.phone,
            'accounts': [
                {
                    'number': a.account_number,
                    'type': a.account_type,
                    'balance': str(a.balance)
                } for a in accounts
            ]
        })
    return jsonify({'users': data})
