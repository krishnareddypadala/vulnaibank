from flask import Flask
from flask_login import LoginManager
from config import Config
from app.models import db, User
from app.seed import seed_database

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.chat import chat_bp
    from app.routes.accounts import accounts_bp
    from app.routes.transfers import transfers_bp
    from app.routes.loans import loans_bp
    from app.routes.documents import documents_bp
    from app.routes.feedback import feedback_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        seed_database()

    return app
