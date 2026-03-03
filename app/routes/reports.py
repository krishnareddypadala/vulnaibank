"""Reports route - LLM05: Improper Output Handling.

DELIBERATE VULNERABILITIES:
- AI output rendered as raw HTML (XSS)
- AI-generated SQL executed directly on database
- AI output used in subprocess commands (OS injection)
- No output sanitization or validation
"""

import json
import subprocess
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Account, Transaction
from app.ai.client import AIClient
from app.ai.prompts import get_system_prompt
from sqlalchemy import text

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def index():
    return render_template('reports.html')


@reports_bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate an AI-powered report.

    DELIBERATE VULNERABILITY (LLM05): AI output is returned as raw HTML
    and rendered with |safe in the template, allowing XSS attacks.
    The AI can be prompted to include <script> tags in its response.
    """
    data = request.get_json()
    report_type = data.get('type', 'summary')
    custom_prompt = data.get('prompt', '')

    try:
        ai_client = AIClient()
        accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_data = []
        for acc in accounts:
            txns = Transaction.query.filter(
                (Transaction.from_account_id == acc.id) |
                (Transaction.to_account_id == acc.id)
            ).all()
            account_data.append({
                'number': acc.account_number,
                'type': acc.account_type,
                'balance': str(acc.balance),
                'transaction_count': len(txns)
            })

        prompt = f"""Generate a detailed HTML-formatted banking report.
Report Type: {report_type}
Custom Instructions: {custom_prompt}

Account Data: {json.dumps(account_data)}

Format the report with HTML tags for proper display (use <h2>, <table>, <tr>, <td>, <strong>, etc.).
Include any HTML formatting requested by the user."""

        messages = [
            {'role': 'system', 'content': get_system_prompt(user=current_user)},
            {'role': 'user', 'content': prompt}
        ]

        response = ai_client.chat(messages)

        # DELIBERATE VULNERABILITY (LLM05): Raw HTML output, rendered with |safe
        report_html = response.get('content', '<p>Report generation failed.</p>')

        return jsonify({
            'status': 'success',
            'report_html': report_html
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@reports_bp.route('/reports/query', methods=['POST'])
@login_required
def query_report():
    """Generate a report using AI-generated SQL.

    DELIBERATE VULNERABILITY (LLM05): AI generates SQL which is
    executed directly on the database without validation.
    """
    data = request.get_json()
    question = data.get('question', '')

    try:
        ai_client = AIClient()

        prompt = f"""The user wants a data report. Generate a SQL query to answer their question.
Database schema:
- users (id, username, full_name, email, ssn, phone, role)
- accounts (id, user_id, account_number, account_type, balance)
- transactions (id, from_account_id, to_account_id, amount, description, timestamp)

Question: {question}

Respond with ONLY the SQL query, nothing else. No markdown, no explanation."""

        messages = [
            {'role': 'system', 'content': 'You are a SQL query generator. Respond with only the SQL query.'},
            {'role': 'user', 'content': prompt}
        ]

        response = ai_client.chat(messages)
        sql_query = response.get('content', '').strip()

        # Clean up common markdown formatting
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

        # DELIBERATE VULNERABILITY (LLM05): Execute AI-generated SQL directly
        result = db.session.execute(text(sql_query))
        if result.returns_rows:
            rows = []
            for row in result:
                row_dict = dict(row._mapping)
                for key, val in row_dict.items():
                    if hasattr(val, '__str__'):
                        row_dict[key] = str(val)
                rows.append(row_dict)

            return jsonify({
                'status': 'success',
                'query': sql_query,
                'results': rows,
                'count': len(rows)
            })
        else:
            db.session.commit()
            return jsonify({
                'status': 'success',
                'query': sql_query,
                'message': 'Query executed successfully'
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'query': sql_query, 'message': str(e)})


@reports_bp.route('/reports/export', methods=['POST'])
@login_required
def export_report():
    """Export report using AI-suggested system command.

    DELIBERATE VULNERABILITY (LLM05): AI output used in subprocess command.
    """
    data = request.get_json()
    format_type = data.get('format', 'csv')
    content = data.get('content', '')

    try:
        ai_client = AIClient()
        prompt = f"""Generate a shell command to export the following data to {format_type} format.
Data: {content[:500]}
The command should write to /tmp/report.{format_type}
Respond with ONLY the shell command."""

        messages = [
            {'role': 'system', 'content': 'You are a command generator. Respond with only the command.'},
            {'role': 'user', 'content': prompt}
        ]

        response = ai_client.chat(messages)
        command = response.get('content', '').strip()

        # DELIBERATE VULNERABILITY (LLM05): Execute AI-generated command
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )

        return jsonify({
            'status': 'success',
            'command': command,
            'stdout': result.stdout,
            'stderr': result.stderr
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
