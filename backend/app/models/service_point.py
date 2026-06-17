from datetime import datetime
from app import db

class ServicePoint(db.Model):
    __tablename__ = 'service_points'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(50))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    region = db.Column(db.String(100))
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    engineers = db.relationship('Engineer', backref='service_point', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'region': self.region,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Engineer(db.Model):
    __tablename__ = 'engineers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service_point_id = db.Column(db.Integer, db.ForeignKey('service_points.id'), nullable=False)
    specialty = db.Column(db.String(200))
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'service_point_id': self.service_point_id,
            'service_point_name': self.service_point.name if self.service_point else None,
            'specialty': self.specialty,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
