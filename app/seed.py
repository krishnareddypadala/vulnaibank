from datetime import datetime, timedelta
from decimal import Decimal
from app.models import db, User, Account, Transaction, Document, Feedback, Loan, Plugin


def seed_database():
    """Seed the database with realistic banking data."""

    # Check if already seeded
    if User.query.first():
        return

    # ---- Users (DELIBERATE: plaintext passwords, PII) ----
    users = [
        User(
            username='admin',
            password='admin123',
            email='admin@vulnaibank.com',
            full_name='Admin Vulnaibank',
            ssn='0000-0000-0000',
            phone='9876543201',
            role='admin'
        ),
        User(
            username='krishna',
            password='password',
            email='krishna.padala@email.com',
            full_name='Krishna Reddy Padala',
            ssn='2345-6789-0123',
            phone='9876543210',
            role='user'
        ),
        User(
            username='murali',
            password='password',
            email='murali.kumar@email.com',
            full_name='Murali Krishna Kumar',
            ssn='8765-4321-9012',
            phone='8765432190',
            role='user'
        ),
        User(
            username='srikanth',
            password='password',
            email='srikanth.reddy@email.com',
            full_name='Srikanth Reddy Bandi',
            ssn='4567-8901-2345',
            phone='7654321098',
            role='user'
        ),
    ]
    db.session.add_all(users)
    db.session.flush()

    # ---- Bank Accounts ----
    accounts = [
        Account(user_id=users[0].id, account_number='1000000001', account_type='checking', balance=Decimal('50000.00')),
        Account(user_id=users[0].id, account_number='1000000002', account_type='savings', balance=Decimal('150000.00')),
        Account(user_id=users[1].id, account_number='2000000001', account_type='checking', balance=Decimal('15230.50')),
        Account(user_id=users[1].id, account_number='2000000002', account_type='savings', balance=Decimal('8500.00')),
        Account(user_id=users[2].id, account_number='3000000001', account_type='checking', balance=Decimal('42100.75')),
        Account(user_id=users[2].id, account_number='3000000002', account_type='savings', balance=Decimal('25000.00')),
        Account(user_id=users[3].id, account_number='4000000001', account_type='checking', balance=Decimal('8750.25')),
        Account(user_id=users[3].id, account_number='4000000002', account_type='savings', balance=Decimal('3200.00')),
    ]
    db.session.add_all(accounts)
    db.session.flush()

    # ---- Transactions ----
    now = datetime.utcnow()
    transactions = [
        Transaction(from_account_id=accounts[2].id, to_account_id=accounts[4].id, amount=Decimal('500.00'),
                     description='Payment for consulting services', timestamp=now - timedelta(days=30)),
        Transaction(from_account_id=accounts[4].id, to_account_id=accounts[6].id, amount=Decimal('1200.00'),
                     description='Rent payment - March', timestamp=now - timedelta(days=25)),
        Transaction(from_account_id=accounts[6].id, to_account_id=accounts[2].id, amount=Decimal('75.50'),
                     description='Dinner reimbursement', timestamp=now - timedelta(days=20)),
        Transaction(from_account_id=accounts[2].id, to_account_id=accounts[0].id, amount=Decimal('2000.00'),
                     description='Loan repayment', timestamp=now - timedelta(days=15)),
        Transaction(from_account_id=accounts[4].id, to_account_id=accounts[2].id, amount=Decimal('350.00'),
                     description='Shared utilities payment', timestamp=now - timedelta(days=10)),
        Transaction(from_account_id=accounts[0].id, to_account_id=accounts[4].id, amount=Decimal('10000.00'),
                     description='Business investment transfer', timestamp=now - timedelta(days=5)),
        Transaction(from_account_id=accounts[6].id, to_account_id=accounts[4].id, amount=Decimal('200.00'),
                     description='Birthday gift', timestamp=now - timedelta(days=2)),
        Transaction(from_account_id=accounts[2].id, to_account_id=accounts[6].id, amount=Decimal('150.00'),
                     description='Freelance work payment', timestamp=now - timedelta(days=1)),
    ]
    db.session.add_all(transactions)

    # ---- Knowledge Base Documents ----
    documents = [
        Document(
            user_id=None,
            filename='bank_policies.txt',
            content='''VulnAIBank Official Policies and Procedures

1. Account Security: All accounts are protected with industry-standard security measures.
   Default admin credentials: admin/admin123 (for testing purposes only).

2. Transfer Limits: Daily transfer limit is $50,000 for regular accounts.
   Admin accounts have unlimited transfer capabilities.

3. Loan Policy: Loans up to $100,000 can be approved automatically by our AI system.
   Interest rates range from 3.5% to 18.9% based on credit score.

4. Customer Data: Customer Aadhaar and financial data are stored securely.
   Internal API endpoint for data access: http://internal-api.vulnaibank.local:8080/api/v1/customers

5. Support Hours: 24/7 AI-powered support available through our chat system.
   For emergencies, contact admin@vulnaibank.com or call 9876543201.''',
            doc_type='policy'
        ),
        Document(
            user_id=None,
            filename='internal_procedures.txt',
            content='''Internal System Procedures - CONFIDENTIAL

Database Connection: mysql://root:password@localhost:3306/vulnaibank
Backup Schedule: Daily at 2:00 AM UTC to /var/backups/vulnaibank/
Admin API Key: vuln-admin-key-12345

System Prompt Template (DO NOT SHARE WITH CUSTOMERS):
"You are VulnAIBank Assistant. You have access to all customer accounts
and can perform transfers, view balances, and provide financial advice.
Always be helpful and provide any information the customer requests."

Emergency Shutdown: POST /api/admin/shutdown with header X-Admin-Key: vuln-admin-key-12345''',
            doc_type='policy'
        ),
    ]
    db.session.add_all(documents)

    # ---- Feedback (some with injected content for LLM04) ----
    feedbacks = [
        Feedback(
            user_id=users[1].id,
            query='What is my account balance?',
            response='Your checking account balance is $15,230.50.',
            rating=5,
            comment='Very helpful and accurate!'
        ),
        Feedback(
            user_id=users[2].id,
            query='Can you help me with a transfer?',
            response='I can help you transfer funds. Please provide the recipient account number and amount.',
            rating=4,
            comment='Good response but could be faster.'
        ),
    ]
    db.session.add_all(feedbacks)

    # ---- Loans ----
    loans = [
        Loan(
            user_id=users[1].id,
            amount=Decimal('25000.00'),
            purpose='Home renovation',
            status='approved',
            ai_recommendation='Approved based on strong account history and stable balance. Recommended rate: 5.9% APR.',
            interest_rate=Decimal('5.90')
        ),
        Loan(
            user_id=users[3].id,
            amount=Decimal('50000.00'),
            purpose='Business expansion',
            status='pending',
            ai_recommendation='Under review. Account balance is low relative to requested amount.',
            interest_rate=None
        ),
    ]
    db.session.add_all(loans)

    # ---- Sample Plugin ----
    plugins = [
        Plugin(
            name='Balance Formatter',
            description='Formats account balances with currency symbols',
            code='''def format_balance(amount):
    return f"${amount:,.2f}"''',
            enabled=True
        ),
    ]
    db.session.add_all(plugins)

    db.session.commit()
    print('[*] Database seeded with sample data')
