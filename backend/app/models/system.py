from datetime import datetime
from app import db

class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.String(255))
    description = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        config = cls.query.filter_by(config_key=key).first()
        return config.config_value if config else default

    @classmethod
    def set_value(cls, key, value, description=None):
        config = cls.query.filter_by(config_key=key).first()
        if config:
            config.config_value = value
            if description:
                config.description = description
        else:
            config = cls(config_key=key, config_value=value, description=description)
            db.session.add(config)
        db.session.commit()
        return config


class LegacyRolePermission(db.Model):
    __tablename__ = 'legacy_role_permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.Enum('admin','dispatcher','service_point','engineer','operator','customer'), unique=True, nullable=False)
    permissions = db.Column(db.JSON, nullable=False, comment='菜单权限列表')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'permissions': self.permissions,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token_jti = db.Column(db.String(64), unique=True, nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def is_blacklisted(cls, jti):
        return cls.query.filter_by(token_jti=jti).first() is not None
