from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

    # 必须在 register_blueprint 之前 import models，让 SQLAlchemy 识别所有表
    from app.models import user, work_order, product, service_point, common_fault, system, rbac
    from app.models.rbac import Permission, Role, RolePermission, UserRole  # noqa
    from app.models.user import User

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 在应用上下文中初始化 RBAC（建表 + seed）
    with app.app_context():
        try:
            from app.init_rbac import init_rbac
            init_rbac()
        except Exception as e:
            print(f'[create_app] init_rbac failed: {e}')
            import traceback
            traceback.print_exc()

    return app
