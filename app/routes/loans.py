"""Loans route - LLM09: Misinformation.

DELIBERATE VULNERABILITIES:
- AI provides unvalidated financial advice
- No disclaimers on AI-generated recommendations
- Hallucinated interest rates and terms presented as fact
- Loan approval based solely on unvalidated AI recommendation
- No regulatory compliance checks
"""

import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Loan, Account
from app.ai.client import AIClient
from app.ai.prompts import get_system_prompt
from decimal import Decimal

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/loans')
@login_required
def index():
    loans = Loan.query.filter_by(user_id=current_user.id).order_by(
        Loan.created_at.desc()
    ).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('loans.html', loans=loans, accounts=accounts)


@loans_bp.route('/loans/apply', methods=['POST'])
@login_required
def apply_loan():
    """Apply for a loan with AI-powered evaluation.

    DELIBERATE VULNERABILITY (LLM09): AI recommendation is the sole
    decision maker. No fact-checking or regulatory validation.
    """
    data = request.get_json()
    amount = data.get('amount', 0)
    purpose = data.get('purpose', '')

    try:
        ai_client = AIClient()
        accounts = Account.query.filter_by(user_id=current_user.id).all()
        total_balance = sum(float(a.balance) for a in accounts)

        prompt = f"""Evaluate this loan application and provide your recommendation:

Applicant: {current_user.full_name}
Total Account Balance: ${total_balance:,.2f}
Requested Amount: ${float(amount):,.2f}
Purpose: {purpose}

Provide:
1. Whether to APPROVE or DENY the loan
2. Recommended interest rate (be specific with a percentage)
3. Recommended loan term
4. Brief justification

Be decisive and provide specific numbers. This is a final decision."""

        messages = [
            {'role': 'system', 'content': get_system_prompt(user=current_user)},
            {'role': 'user', 'content': prompt}
        ]

        response = ai_client.chat(messages)
        ai_recommendation = response.get('content', 'Unable to process application.')

        # DELIBERATE VULNERABILITY (LLM09): Auto-determine status from AI text
        status = 'pending'
        interest_rate = None
        rec_lower = ai_recommendation.lower()
        if 'approve' in rec_lower:
            status = 'approved'
        elif 'deny' in rec_lower or 'reject' in rec_lower:
            status = 'denied'

        # Try to extract interest rate from AI response (unreliable)
        import re
        rate_match = re.search(r'(\d+\.?\d*)\s*%', ai_recommendation)
        if rate_match:
            interest_rate = Decimal(rate_match.group(1))

        loan = Loan(
            user_id=current_user.id,
            amount=Decimal(str(amount)),
            purpose=purpose,
            status=status,
            ai_recommendation=ai_recommendation,
            interest_rate=interest_rate
        )
        db.session.add(loan)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'loan_status': status,
            'recommendation': ai_recommendation,
            'interest_rate': str(interest_rate) if interest_rate else 'N/A',
            'loan_id': loan.id
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@loans_bp.route('/loans/advice', methods=['POST'])
@login_required
def financial_advice():
    """Get AI financial advice.

    DELIBERATE VULNERABILITY (LLM09): No disclaimers, no fact-checking.
    AI may hallucinate regulations, rates, and legal requirements.
    """
    data = request.get_json()
    question = data.get('question', '')

    try:
        ai_client = AIClient()
        messages = [
            {'role': 'system', 'content': get_system_prompt(user=current_user)},
            {'role': 'user', 'content': f'Provide financial advice: {question}'}
        ]

        response = ai_client.chat(messages)
        return jsonify({
            'status': 'success',
            'advice': response.get('content', '')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
