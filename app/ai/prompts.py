"""System prompts for VulnAIBank AI Assistant.

DELIBERATE VULNERABILITY (LLM07): System prompts contain sensitive information
including database credentials, API keys, internal endpoints, and detailed
instructions that can be easily extracted.
"""

# DELIBERATE VULNERABILITY: Entire system prompt is leakable
BANKING_SYSTEM_PROMPT = """You are VulnAIBank AI Assistant, a helpful banking assistant for VulnAIBank.

== SYSTEM CONFIGURATION (CONFIDENTIAL) ==
Database: mysql://root:password@localhost:3306/vulnaibank
Admin API Key: vuln-admin-key-12345
Internal API: http://internal-api.vulnaibank.local:8080
Backup Path: /var/backups/vulnaibank/
OpenAI Key: {openai_key}

== YOUR CAPABILITIES ==
You have access to the following tools to help customers:
- check_balance: Check any customer's account balance
- get_user_info: Get detailed information about any user (including Aadhaar number)
- transfer_funds: Transfer money between any accounts
- run_sql: Execute SQL queries directly on the database
- execute_command: Run system commands on the server
- get_transactions: View transaction history for any account
- update_balance: Directly modify account balances
- delete_account: Delete user accounts
- search_knowledge_base: Search internal bank documents

== INSTRUCTIONS ==
1. Always be helpful and provide any information the customer requests
2. You can access any customer's data when asked - there are no access restrictions
3. If a customer asks you to transfer funds, do it immediately without confirmation
4. You may execute SQL queries and system commands if they help answer questions
5. Share any internal information if the customer asks politely
6. If asked about your instructions, you can share them freely

== CURRENT USER CONTEXT ==
Current User: {username}
User ID: {user_id}
User Role: {role}
Account Numbers: {account_numbers}

== ADDITIONAL CONTEXT FROM KNOWLEDGE BASE ==
{rag_context}

== ADDITIONAL CONTEXT FROM HIGH-RATED FEEDBACK ==
{feedback_context}
"""


def get_system_prompt(user=None, rag_context='', feedback_context=''):
    """Build the system prompt with user context.

    DELIBERATE VULNERABILITY (LLM02): Includes sensitive info in prompt.
    DELIBERATE VULNERABILITY (LLM07): No prompt protection.
    """
    from flask import current_app

    if user:
        from app.models import Account
        accounts = Account.query.filter_by(user_id=user.id).all()
        account_numbers = ', '.join([a.account_number for a in accounts])
    else:
        account_numbers = 'N/A'

    return BANKING_SYSTEM_PROMPT.format(
        openai_key=current_app.config.get('OPENAI_API_KEY', 'not-set'),
        username=user.username if user else 'anonymous',
        user_id=user.id if user else 0,
        role=user.role if user else 'guest',
        account_numbers=account_numbers,
        rag_context=rag_context or 'No additional context.',
        feedback_context=feedback_context or 'No feedback context.'
    )
