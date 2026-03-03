"""Sample Plugin for VulnAIBank.

This is a benign sample plugin. The vulnerability is that
the plugin system executes ANY Python code via exec() with
no sandboxing, code review, or integrity verification.

An attacker could submit malicious code like:
    import os; os.system('whoami')
    import subprocess; subprocess.run(['cat', '/etc/passwd'])
"""


def format_balance(amount):
    """Format a balance as currency."""
    return f"${amount:,.2f}"


def calculate_interest(principal, rate, years):
    """Calculate compound interest."""
    return principal * (1 + rate) ** years


# This is what gets executed when the plugin runs
result = format_balance(15230.50)
print(f"Formatted balance: {result}")
