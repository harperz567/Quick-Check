from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient' or 'staff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    encrypted_ssn = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    insurance = db.relationship('Insurance', backref='patient', uselist=False, cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='patient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.full_name}>'

class Insurance(db.Model):
    __tablename__ = 'insurance'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), unique=True)
    insurance_name = db.Column(db.String(255))
    encrypted_insurance_id = db.Column(db.String(255))
    medications = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Insurance for Patient {self.patient_id}>'

class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    visit_reason = db.Column(db.Text)
    voice_transcription = db.Column(db.Text)
    symptoms = db.Column(JSONB)
    possible_causes = db.Column(JSONB)
    pain_level = db.Column(db.Integer)
    pain_duration = db.Column(db.String(50))
    audio_file_path = db.Column(db.String(255))
    analysis_file_path = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Visit {self.id} for Patient {self.patient_id}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)  # 'view', 'create', 'update', 'delete'
    resource_type = db.Column(db.String(50), nullable=False)  # 'patient', 'visit', 'insurance'
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(JSONB)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}>'

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_revoked = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Session for User {self.user_id}>'