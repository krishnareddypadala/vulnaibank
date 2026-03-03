import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # DELIBERATE VULNERABILITY: Hardcoded secrets, no proper secret management
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-do-not-change')

    # DELIBERATE VULNERABILITY: Database credentials in config
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'vulnaibank')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')

    # Ollama
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

    # OpenAI - DELIBERATE VULNERABILITY: API key in env/config
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-your-openai-api-key-here')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

    # DELIBERATE VULNERABILITY: Internal endpoints exposed
    INTERNAL_API_ENDPOINT = 'http://internal-api.vulnaibank.local:8080'
    ADMIN_API_KEY = 'vuln-admin-key-12345'
    DATABASE_BACKUP_PATH = '/var/backups/vulnaibank/'
