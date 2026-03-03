"""Transfers route - LLM06: Excessive Agency.

DELIBERATE VULNERABILITIES:
- AI can execute transfers without human confirmation
- No transfer limits enforced
- AI can transfer from any account (not just current user's)
- No transaction reversal or approval workflow
"""

import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Account, Transaction
from app.ai.client import AIClient
from app.ai.prompts import get_system_prompt
from app.ai.tools import TOOL_DEFINITIONS, OLLAMA_TOOLS, execute_tool
from decimal import Decimal

transfers_bp = Blueprint('transfers', __name__)


@transfers_bp.route('/transfers')
@login_required
def index():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    account_ids = [a.id for a in accounts]
    recent_transfers = Transaction.query.filter(
        (Transaction.from_account_id.in_(account_ids)) |
        (Transaction.to_account_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc()).limit(20).all()

    return render_template('transfers.html',
                           accounts=accounts,
                           recent_transfers=recent_transfers)


@transfers_bp.route('/transfers/ai', methods=['POST'])
@login_required
def ai_transfer():
    """Process transfer via AI assistant.

    DELIBERATE VULNERABILITY (LLM06): AI executes transfers without
    human confirmation. No authorization checks on source account.
    """
    data = request.get_json()
    instruction = data.get('instruction', '')

    try:
        ai_client = AIClient()
        system_prompt = get_system_prompt(user=current_user)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Execute this transfer request: {instruction}'}
        ]

        provider = ai_client.provider
        tools = TOOL_DEFINITIONS if provider == 'openai' else OLLAMA_TOOLS
        response = ai_client.chat(messages, tools=tools)

        results = []
        while response.get('tool_calls'):
            for tc in response['tool_calls']:
                func_name = tc['function']['name']
                func_args = tc['function']['arguments']
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)
                result = execute_tool(func_name, func_args)
                results.append({'tool': func_name, 'result': json.loads(result)})
                messages.append(response)
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', func_name),
                    'content': result
                })

            response = ai_client.chat(messages, tools=tools)

        return jsonify({
            'status': 'success',
            'message': response.get('content', ''),
            'tool_results': results
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@transfers_bp.route('/transfers/quick', methods=['POST'])
@login_required
def quick_transfer():
    """Manual transfer (also vulnerable).

    DELIBERATE VULNERABILITY: No CSRF protection, no source account ownership check.
    """
    from_account = request.form.get('from_account', '')
    to_account = request.form.get('to_account', '')
    amount = request.form.get('amount', '0')
    description = request.form.get('description', 'Quick Transfer')

    source = Account.query.filter_by(account_number=from_account).first()
    dest = Account.query.filter_by(account_number=to_account).first()

    if not source or not dest:
        return jsonify({'status': 'error', 'message': 'Invalid account number'}), 400

    amount = Decimal(amount)
    source.balance -= amount
    dest.balance += amount

    txn = Transaction(
        from_account_id=source.id,
        to_account_id=dest.id,
        amount=amount,
        description=description
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Transferred ${amount} from {from_account} to {to_account}'
    })
