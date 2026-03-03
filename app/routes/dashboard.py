from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Account, Transaction, Loan

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_balance = sum(float(a.balance) for a in accounts)

    # Recent transactions
    account_ids = [a.id for a in accounts]
    recent_txns = Transaction.query.filter(
        (Transaction.from_account_id.in_(account_ids)) |
        (Transaction.to_account_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc()).limit(5).all()

    # Pending loans
    pending_loans = Loan.query.filter_by(user_id=current_user.id, status='pending').count()

    return render_template('dashboard.html',
                           accounts=accounts,
                           total_balance=total_balance,
                           recent_transactions=recent_txns,
                           pending_loans=pending_loans)
