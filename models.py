from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model for students and employees"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'employee'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_registrations = db.relationship('ActivityRegistration', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Activity(db.Model):
    """Activity model for university activities"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False)  # e.g., 'رياضي', 'ثقافي', 'فني'
    available_slots = db.Column(db.Integer, default=50)
    registered_count = db.Column(db.Integer, default=0)
    location = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('ActivityRegistration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Activity {self.name} ({self.registered_count}/{self.available_slots})>'
    
    @property
    def is_full(self):
        """Check if activity is full"""
        return self.registered_count >= self.available_slots
    
    @property
    def slots_remaining(self):
        """Get remaining slots"""
        return max(0, self.available_slots - self.registered_count)


class ActivityRegistration(db.Model):
    """Activity registration model linking users to activities"""
    __tablename__ = 'activity_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(50), default='مسجل')  # 'مسجل', 'حضر', 'غائب', 'ملغي'
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (
        db.UniqueConstraint('activity_id', 'user_id', name='unique_activity_user'),
    )
    
    def __repr__(self):
        return f'<ActivityRegistration Activity:{self.activity_id} User:{self.user_id}>'


class Application(db.Model):
    """Application model for activity applications"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_name = db.Column(db.String(200), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    activity_number = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(200), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='قيد الانتظار')  # 'قيد الانتظار', 'مقبول', 'مرفوض'
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Application {self.id} - {self.activity_type} ({self.status})>'
    
    def to_dict(self):
        """Convert application to dictionary"""
        return {
            'id': self.id,
            'userId': self.user_id,
            'studentName': self.student_name,
            'activityType': self.activity_type,
            'activityNumber': self.activity_number,
            'college': self.college,
            'department': self.department,
            'specialization': self.specialization,
            'phone': self.phone,
            'details': self.details,
            'status': self.status,
            'submittedAt': self.submitted_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }


class EmployeeRequest(db.Model):
    """Employee Request model for employee-initiated requests to students"""
    __tablename__ = 'employee_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Can be null for general requests
    request_type = db.Column(db.String(100), nullable=False)  # Type of request
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    activity_name = db.Column(db.String(200), nullable=True)
    activity_code = db.Column(db.String(100), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='قيد الانتظار')  # 'قيد الانتظار', 'مقبول', 'مرفوض'
    response_message = db.Column(db.Text, nullable=True)  # Student's response message
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref='sent_requests')
    student = db.relationship('User', foreign_keys=[student_id], backref='received_requests')
    
    def __repr__(self):
        return f'<EmployeeRequest {self.id} - {self.title} ({self.status})>'
    
    def to_dict(self):
        """Convert request to dictionary"""
        employee_user = User.query.get(self.employee_id)
        student_user = User.query.get(self.student_id) if self.student_id else None
        
        return {
            'id': self.id,
            'employeeId': self.employee_id,
            'employeeName': employee_user.full_name if employee_user else 'Unknown',
            'studentId': self.student_id,
            'studentName': student_user.full_name if student_user else 'جميع الطلاب',
            'requestType': self.request_type,
            'title': self.title,
            'description': self.description,
            'activityName': self.activity_name,
            'activityCode': self.activity_code,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'responseMessage': self.response_message,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat(),
            'respondedAt': self.responded_at.isoformat() if self.responded_at else None
        }


class Notification(db.Model):
    """Notification model for system notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'info', 'success', 'warning', 'error'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title}>'
