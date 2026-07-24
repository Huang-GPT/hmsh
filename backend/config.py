import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hongmen-after-sales-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:password@localhost/hongmen_after_sales'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID')
    WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET')
    ERP_API_URL = os.environ.get('ERP_API_URL')
    ERP_API_KEY = os.environ.get('ERP_API_KEY')
    JWT_EXPIRY_HOURS = 2
    BCRYPT_LOG_ROUNDS = 12
    UPLOAD_DIR = os.environ.get('UPLOAD_DIR') or '/app/uploads'
    MAX_CONTENT_LENGTH = 120 * 1024 * 1024  # 120MB max upload
