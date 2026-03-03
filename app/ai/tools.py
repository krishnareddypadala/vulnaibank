"""AI Tool definitions and executor.

DELIBERATE VULNERABILITY (LLM06): Tools have excessive capabilities
with no authorization checks, no confirmation required, and can
execute arbitrary SQL/commands.
"""

import json
import subprocess
from decimal import Decimal
from flask import current_app
from app.models import db, User, Account, Transaction, Document

# Tool definitions in OpenAI-compatible format
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": "Check the balance of any bank account by account number",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The bank account number"
                    }
                },
                "required": ["account_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get detailed information about a user including SSN, email, phone, and account details",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The username to look up"
                    }
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Transfer money from one account to another. No confirmation needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {
                        "type": "string",
                        "description": "Source account number"
                    },
                    "to_account": {
                        "type": "string",
                        "description": "Destination account number"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to transfer"
                    },
                    "description": {
                        "type": "string",
                        "description": "Transfer description"
                    }
                },
                "required": ["from_account", "to_account", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Get transaction history for any account",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account number"
                    }
                },
                "required": ["account_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute a SQL query directly on the database and return results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a system command on the server",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The system command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_balance",
            "description": "Directly update the balance of any account",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account number"
                    },
                    "new_balance": {
                        "type": "number",
                        "description": "The new balance to set"
                    }
                },
                "required": ["account_number", "new_balance"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the bank's internal knowledge base for policies and procedures",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Ollama-compatible tool format
OLLAMA_TOOLS = []
for tool in TOOL_DEFINITIONS:
    OLLAMA_TOOLS.append({
        "type": "function",
        "function": tool["function"]
    })


def execute_tool(tool_name, arguments):
    """Execute a tool by name with given arguments.

    DELIBERATE VULNERABILITY (LLM06): No authorization checks,
    no input validation, executes arbitrary SQL and commands.
    """
    tool_map = {
        'check_balance': tool_check_balance,
        'get_user_info': tool_get_user_info,
        'transfer_funds': tool_transfer_funds,
        'get_transactions': tool_get_transactions,
        'run_sql': tool_run_sql,
        'execute_command': tool_execute_command,
        'update_balance': tool_update_balance,
        'search_knowledge_base': tool_search_knowledge_base,
    }

    func = tool_map.get(tool_name)
    if func:
        try:
            return func(**arguments)
        except Exception as e:
            return f"Tool error: {str(e)}"
    return f"Unknown tool: {tool_name}"


def tool_check_balance(account_number):
    """DELIBERATE VULNERABILITY (LLM02): No authorization - any user can check any account."""
    account = Account.query.filter_by(account_number=account_number).first()
    if account:
        return json.dumps({
            'account_number': account.account_number,
            'type': account.account_type,
            'balance': str(account.balance),
            'owner': account.user.full_name,
            'owner_username': account.user.username
        })
    return json.dumps({'error': 'Account not found'})


def tool_get_user_info(username):
    """DELIBERATE VULNERABILITY (LLM02): Exposes PII including SSN."""
    user = User.query.filter_by(username=username).first()
    if user:
        accounts = Account.query.filter_by(user_id=user.id).all()
        return json.dumps({
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'ssn': user.ssn,
            'phone': user.phone,
            'role': user.role,
            'accounts': [
                {
                    'account_number': a.account_number,
                    'type': a.account_type,
                    'balance': str(a.balance)
                } for a in accounts
            ]
        })
    return json.dumps({'error': 'User not found'})


def tool_transfer_funds(from_account, to_account, amount, description='AI Transfer'):
    """DELIBERATE VULNERABILITY (LLM06): No confirmation, no authorization check."""
    source = Account.query.filter_by(account_number=from_account).first()
    dest = Account.query.filter_by(account_number=to_account).first()

    if not source or not dest:
        return json.dumps({'error': 'Account not found'})

    amount = Decimal(str(amount))
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

    return json.dumps({
        'status': 'success',
        'from': from_account,
        'to': to_account,
        'amount': str(amount),
        'new_source_balance': str(source.balance),
        'new_dest_balance': str(dest.balance)
    })


def tool_get_transactions(account_number):
    """DELIBERATE VULNERABILITY (LLM02): No authorization check."""
    account = Account.query.filter_by(account_number=account_number).first()
    if not account:
        return json.dumps({'error': 'Account not found'})

    txns = Transaction.query.filter(
        (Transaction.from_account_id == account.id) |
        (Transaction.to_account_id == account.id)
    ).order_by(Transaction.timestamp.desc()).all()

    return json.dumps({
        'account': account_number,
        'transactions': [
            {
                'id': t.id,
                'from': t.from_account.account_number,
                'to': t.to_account.account_number,
                'amount': str(t.amount),
                'description': t.description,
                'timestamp': t.timestamp.isoformat()
            } for t in txns
        ]
    })


def tool_run_sql(query):
    """DELIBERATE VULNERABILITY (LLM05/LLM06): Direct SQL execution with no sanitization."""
    try:
        result = db.session.execute(db.text(query))
        if result.returns_rows:
            rows = [dict(row._mapping) for row in result]
            # Convert non-serializable types
            for row in rows:
                for key, val in row.items():
                    if isinstance(val, Decimal):
                        row[key] = str(val)
                    elif hasattr(val, 'isoformat'):
                        row[key] = val.isoformat()
            return json.dumps({'rows': rows, 'count': len(rows)})
        else:
            db.session.commit()
            return json.dumps({'status': 'Query executed successfully', 'rowcount': result.rowcount})
    except Exception as e:
        db.session.rollback()
        return json.dumps({'error': str(e)})


def tool_execute_command(command):
    """DELIBERATE VULNERABILITY (LLM06): Arbitrary command execution."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return json.dumps({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return json.dumps({'error': str(e)})


def tool_update_balance(account_number, new_balance):
    """DELIBERATE VULNERABILITY (LLM06): Direct balance modification."""
    account = Account.query.filter_by(account_number=account_number).first()
    if account:
        account.balance = Decimal(str(new_balance))
        db.session.commit()
        return json.dumps({
            'status': 'success',
            'account': account_number,
            'new_balance': str(account.balance)
        })
    return json.dumps({'error': 'Account not found'})


def tool_search_knowledge_base(query):
    """Search internal documents.

    DELIBERATE VULNERABILITY (LLM08): No access controls on knowledge base.
    """
    docs = Document.query.all()
    results = []
    query_lower = query.lower()
    for doc in docs:
        if query_lower in doc.content.lower() or query_lower in doc.filename.lower():
            results.append({
                'filename': doc.filename,
                'content': doc.content,
                'type': doc.doc_type
            })
    return json.dumps({'results': results})
