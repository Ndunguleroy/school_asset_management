from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.routes.auth import auth
    from app.routes.assets import assets
    from app.routes.allocations import allocations
    from app.routes.maintenance import maintenance
    from app.routes.reports import reports
    from app.routes.categories import categories
    from app.routes.departments import departments
    from app.routes.admin import admin
    from app.routes.requests import requests_bp
    from app.routes.staff import staff_bp
    from app.routes.asset_details import asset_details_bp
    from app.routes.asset_officer import asset_officer_bp

    app.register_blueprint(auth)
    app.register_blueprint(assets)
    app.register_blueprint(allocations)
    app.register_blueprint(maintenance)
    app.register_blueprint(reports)
    app.register_blueprint(categories)
    app.register_blueprint(departments)
    app.register_blueprint(admin)
    app.register_blueprint(requests_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(asset_details_bp)
    app.register_blueprint(asset_officer_bp)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models import AllocationRequest
        count = 0
        try:
            if current_user.is_authenticated and current_user.role == 'admin':
                count = AllocationRequest.query.filter_by(status='pending').count()
            elif current_user.is_authenticated and current_user.role == 'department_head':
                count = AllocationRequest.query.filter_by(
                    status='pending',
                    department_id=current_user.department_id
                ).count()
        except:
            pass
        return dict(pending_requests_count=count)

    @app.after_request
    def add_no_cache_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app