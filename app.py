from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys
import socket
import webbrowser
import threading
import time

# Initialize Flask app
app = Flask(__name__, static_folder='..', static_url_path='')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///university_activities.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
try:
    from models import db, User, Activity, Application, ActivityRegistration, EmployeeRequest
    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    jwt = JWTManager(app)
except ImportError as e:
    print(f"❌ خطأ في استيراد models: {e}")
    print("❌ Error importing models")
    sys.exit(1)

# Create database tables
with app.app_context():
    db.create_all()
    # Create default activities if none exist
    if Activity.query.count() == 0:
        default_activities = [
            Activity(
                name='نشاط رياضي',
                description='أنشطة رياضية متنوعة للطلاب',
                category='رياضي',
                available_slots=50,
                location='الصالة الرياضية',
                start_date=datetime.now() + timedelta(days=7),
                end_date=datetime.now() + timedelta(days=37)
            ),
            Activity(
                name='نشاط ثقافي',
                description='فعاليات ثقافية وأدبية',
                category='ثقافي',
                available_slots=100,
                location='القاعة الكبرى',
                start_date=datetime.now() + timedelta(days=10),
                end_date=datetime.now() + timedelta(days=40)
            ),
            Activity(
                name='نشاط فني',
                description='ورش عمل فنية وإبداعية',
                category='فني',
                available_slots=30,
                location='مركز الفنون',
                start_date=datetime.now() + timedelta(days=5),
                end_date=datetime.now() + timedelta(days=35)
            ),
            Activity(
                name='نشاط علمي',
                description='محاضرات وندوات علمية',
                category='علمي',
                available_slots=75,
                location='مختبر العلوم',
                start_date=datetime.now() + timedelta(days=14),
                end_date=datetime.now() + timedelta(days=44)
            ),
            Activity(
                name='نشاط اجتماعي',
                description='أنشطة تطوعية واجتماعية',
                category='اجتماعي',
                available_slots=60,
                location='مركز الطلاب',
                start_date=datetime.now() + timedelta(days=3),
                end_date=datetime.now() + timedelta(days=33)
            ),
            Activity(
                name='نشاط تقني',
                description='ورش برمجة وتقنية معلومات',
                category='تقني',
                available_slots=40,
                location='معمل الحاسوب',
                start_date=datetime.now() + timedelta(days=12),
                end_date=datetime.now() + timedelta(days=42)
            )
        ]
        for activity in default_activities:
            db.session.add(activity)
        db.session.commit()
        print("✅ Default activities created successfully!")

# ==================== AUTH ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user (student or employee)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['fullName', 'username', 'email', 'password', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
        
        # Check if username exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'اسم المستخدم موجود بالفعل'}), 400
        
        # Check if email exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'البريد الإلكتروني موجود بالفعل'}), 400
        
        # Create new user
        new_user = User(
            full_name=data['fullName'],
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data['role']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء الحساب بنجاح'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(field in data for field in ['username', 'password', 'role']):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
        
        # Find user
        user = User.query.filter_by(username=data['username'], role=data['role']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
        
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'token': access_token,
            'user': {
                'id': user.id,
                'fullName': user.full_name,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# ==================== ACTIVITY ENDPOINTS ====================

@app.route('/api/activities', methods=['GET'])
@jwt_required()
def get_activities():
    """Get all activities with registration status"""
    try:
        user_id = get_jwt_identity()
        activities = Activity.query.filter_by(is_active=True).all()
        
        result = []
        for activity in activities:
            # Check if user is registered
            registration = ActivityRegistration.query.filter_by(
                activity_id=activity.id,
                user_id=user_id
            ).first()
            
            result.append({
                'id': activity.id,
                'name': activity.name,
                'description': activity.description,
                'category': activity.category,
                'availableSlots': activity.available_slots,
                'registeredCount': activity.registered_count,
                'location': activity.location,
                'startDate': activity.start_date.isoformat() if activity.start_date else None,
                'endDate': activity.end_date.isoformat() if activity.end_date else None,
                'isRegistered': registration is not None,
                'registrationStatus': registration.status if registration else None
            })
        
        return jsonify({'success': True, 'activities': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/activities/<int:activity_id>/register', methods=['POST'])
@jwt_required()
def register_for_activity(activity_id):
    """Register user for an activity"""
    try:
        user_id = get_jwt_identity()
        
        # Check if activity exists
        activity = Activity.query.get(activity_id)
        if not activity:
            return jsonify({'success': False, 'message': 'النشاط غير موجود'}), 404
        
        # Check if activity is full
        if activity.registered_count >= activity.available_slots:
            return jsonify({'success': False, 'message': 'النشاط ممتلئ'}), 400
        
        # Check if already registered
        existing = ActivityRegistration.query.filter_by(
            activity_id=activity_id,
            user_id=user_id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'أنت مسجل بالفعل في هذا النشاط'}), 400
        
        # Create registration
        registration = ActivityRegistration(
            activity_id=activity_id,
            user_id=user_id,
            status='مسجل'
        )
        
        # Update activity registered count
        activity.registered_count += 1
        
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم التسجيل في النشاط بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/activities/my-registrations', methods=['GET'])
@jwt_required()
def get_my_registrations():
    """Get user's activity registrations"""
    try:
        user_id = get_jwt_identity()
        
        registrations = ActivityRegistration.query.filter_by(user_id=user_id).all()
        
        result = []
        for reg in registrations:
            activity = Activity.query.get(reg.activity_id)
            result.append({
                'id': reg.id,
                'activity': {
                    'id': activity.id,
                    'name': activity.name,
                    'description': activity.description,
                    'category': activity.category,
                    'location': activity.location
                },
                'status': reg.status,
                'registeredAt': reg.registered_at.isoformat()
            })
        
        return jsonify({'success': True, 'registrations': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# ==================== APPLICATION ENDPOINTS ====================

@app.route('/api/applications/submit', methods=['POST'])
@jwt_required()
def submit_application():
    """Submit a new application"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['activityType', 'activityNumber', 'college', 'department', 'specialization', 'phone']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
        
        # Get user info
        user = User.query.get(user_id)
        
        # Create new application
        new_application = Application(
            user_id=user_id,
            student_name=data.get('name', user.full_name),
            activity_type=data['activityType'],
            activity_number=data['activityNumber'],
            college=data['college'],
            department=data['department'],
            specialization=data['specialization'],
            phone=data['phone'],
            details=data.get('details', ''),
            status='قيد الانتظار'
        )
        
        db.session.add(new_application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال الطلب بنجاح',
            'application': {
                'id': new_application.id,
                'status': new_application.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/applications/my-applications', methods=['GET'])
@jwt_required()
def get_my_applications():
    """Get current user's applications"""
    try:
        user_id = get_jwt_identity()
        applications = Application.query.filter_by(user_id=user_id).order_by(Application.submitted_at.desc()).all()
        
        result = []
        for app in applications:
            result.append({
                'id': app.id,
                'studentName': app.student_name,
                'activityType': app.activity_type,
                'activityNumber': app.activity_number,
                'college': app.college,
                'department': app.department,
                'specialization': app.specialization,
                'phone': app.phone,
                'details': app.details,
                'status': app.status,
                'submittedAt': app.submitted_at.isoformat(),
                'updatedAt': app.updated_at.isoformat()
            })
        
        return jsonify({'success': True, 'applications': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/applications/all', methods=['GET'])
@jwt_required()
def get_all_applications():
    """Get all applications (employee only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        applications = Application.query.order_by(Application.submitted_at.desc()).all()
        
        result = []
        for app in applications:
            result.append({
                'id': app.id,
                'studentName': app.student_name,
                'activityType': app.activity_type,
                'activityNumber': app.activity_number,
                'college': app.college,
                'department': app.department,
                'specialization': app.specialization,
                'phone': app.phone,
                'details': app.details,
                'status': app.status,
                'submittedAt': app.submitted_at.isoformat(),
                'updatedAt': app.updated_at.isoformat()
            })
        
        return jsonify({'success': True, 'applications': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(application_id):
    """Update application status (employee only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'الحالة مطلوبة'}), 400
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'success': False, 'message': 'الطلب غير موجود'}), 404
        
        application.status = new_status
        application.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم {new_status} الطلب بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/applications/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get application statistics (employee only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        total = Application.query.count()
        pending = Application.query.filter_by(status='قيد الانتظار').count()
        approved = Application.query.filter_by(status='مقبول').count()
        rejected = Application.query.filter_by(status='مرفوض').count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'pending': pending,
                'approved': approved,
                'rejected': rejected
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# ==================== EMPLOYEE REQUEST ENDPOINTS ====================

@app.route('/api/employee/requests/send', methods=['POST'])
@jwt_required()
def send_employee_request():
    """Send a request from employee to student(s)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['requestType', 'title', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'جميع الحقول المطلوبة يجب ملؤها'}), 400
        
        # Parse deadline if provided
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'success': False, 'message': 'تنسيق التاريخ غير صالح'}), 400
        
        # Create new request
        new_request = EmployeeRequest(
            employee_id=user_id,
            student_id=data.get('studentId'),  # Can be null for general requests
            request_type=data['requestType'],
            title=data['title'],
            description=data['description'],
            activity_name=data.get('activityName'),
            activity_code=data.get('activityCode'),
            deadline=deadline,
            status='قيد الانتظار'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال الطلب بنجاح',
            'request': new_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/employee/requests/my-requests', methods=['GET'])
@jwt_required()
def get_employee_sent_requests():
    """Get employee's sent requests"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        requests = EmployeeRequest.query.filter_by(employee_id=user_id).order_by(EmployeeRequest.created_at.desc()).all()
        
        result = [req.to_dict() for req in requests]
        
        return jsonify({'success': True, 'requests': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/student/requests', methods=['GET'])
@jwt_required()
def get_student_requests():
    """Get student's received requests from employees"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'student':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        # Get requests specifically for this student OR general requests (student_id is null)
        requests = EmployeeRequest.query.filter(
            (EmployeeRequest.student_id == user_id) | (EmployeeRequest.student_id == None)
        ).order_by(EmployeeRequest.created_at.desc()).all()
        
        result = [req.to_dict() for req in requests]
        
        return jsonify({'success': True, 'requests': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/student/requests/<int:request_id>/respond', methods=['PUT'])
@jwt_required()
def respond_to_employee_request(request_id):
    """Student responds to employee request (approve/reject)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'student':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        response_message = data.get('responseMessage', '')
        
        if not new_status or new_status not in ['مقبول', 'مرفوض']:
            return jsonify({'success': False, 'message': 'الحالة غير صالحة'}), 400
        
        employee_request = EmployeeRequest.query.get(request_id)
        if not employee_request:
            return jsonify({'success': False, 'message': 'الطلب غير موجود'}), 404
        
        # Check if request is for this student or general
        if employee_request.student_id and employee_request.student_id != user_id:
            return jsonify({'success': False, 'message': 'غير مصرح لك بالرد على هذا الطلب'}), 403
        
        # Update request status
        employee_request.status = new_status
        employee_request.response_message = response_message
        employee_request.updated_at = datetime.utcnow()
        employee_request.responded_at = datetime.utcnow()
        
        # If it was a general request, associate it with this student
        if not employee_request.student_id:
            employee_request.student_id = user_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم {new_status} الطلب بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/employee/requests/statistics', methods=['GET'])
@jwt_required()
def get_employee_request_statistics():
    """Get employee request statistics"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        total = EmployeeRequest.query.filter_by(employee_id=user_id).count()
        pending = EmployeeRequest.query.filter_by(employee_id=user_id, status='قيد الانتظار').count()
        approved = EmployeeRequest.query.filter_by(employee_id=user_id, status='مقبول').count()
        rejected = EmployeeRequest.query.filter_by(employee_id=user_id, status='مرفوض').count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'pending': pending,
                'approved': approved,
                'rejected': rejected
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# ==================== EMPLOYEE ENDPOINTS ====================

@app.route('/api/employee/activities', methods=['GET'])
@jwt_required()
def get_employee_activities():
    """Get all activities with registration details (employee only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403
        
        activities = Activity.query.all()
        
        result = []
        for activity in activities:
            registrations = ActivityRegistration.query.filter_by(activity_id=activity.id).all()
            
            student_list = []
            for reg in registrations:
                student = User.query.get(reg.user_id)
                student_list.append({
                    'id': student.id,
                    'name': student.full_name,
                    'email': student.email,
                    'registeredAt': reg.registered_at.isoformat(),
                    'status': reg.status
                })
            
            result.append({
                'id': activity.id,
                'name': activity.name,
                'description': activity.description,
                'category': activity.category,
                'availableSlots': activity.available_slots,
                'registeredCount': activity.registered_count,
                'location': activity.location,
                'startDate': activity.start_date.isoformat() if activity.start_date else None,
                'endDate': activity.end_date.isoformat() if activity.end_date else None,
                'isActive': activity.is_active,
                'students': student_list
            })
        
        return jsonify({'success': True, 'activities': result}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@app.route('/api/employee/activities/add', methods=['POST'])
@jwt_required()
def add_activity():
    """Add a new activity (employee only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if user.role != 'employee':
            return jsonify({'success': False, 'message': 'غير مصرح لك'}), 403

        data = request.get_json()

        required_fields = ['name', 'description', 'category', 'availableSlots', 'location', 'startDate', 'endDate']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400

        # Convert date strings to datetime objects
        try:
            start_date = datetime.fromisoformat(data['startDate'])
            end_date = datetime.fromisoformat(data['endDate'])
        except ValueError:
            return jsonify({'success': False, 'message': 'تنسيق التاريخ غير صالح. يرجى استخدام تنسيق ISO 8601.'}), 400

        new_activity = Activity(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            available_slots=data['availableSlots'],
            location=data['location'],
            start_date=start_date,
            end_date=end_date,
            is_active=data.get('isActive', True) # Default to True
        )

        db.session.add(new_activity)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إنشاء النشاط بنجاح',
            'activity': {
                'id': new_activity.id,
                'name': new_activity.name,
                'description': new_activity.description,
                'category': new_activity.category,
                'availableSlots': new_activity.available_slots,
                'location': new_activity.location,
                'startDate': new_activity.start_date.isoformat(),
                'endDate': new_activity.end_date.isoformat(),
                'isActive': new_activity.is_active
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# ==================== FRONTEND ROUTES ====================

@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory('..', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('..', path)

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'University Activities Backend API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'المسار غير موجود'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'خطأ في الخادم'}), 500

# ==================== HELPER FUNCTIONS ====================

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def open_browser_delayed(url, delay=2):
    """Open browser after delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except:
        pass

# ==================== RUN APP ====================

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8080))
    local_ip = get_local_ip()
    
    print("=" * 70)
    print("   🎓 نظام إدارة الأنشطة الطلابية - جامعة العين")
    print("   🎓 University Activities Management System")
    print("=" * 70)
    print()
    print("🚀 Starting server...")
    print()
    print("=" * 70)
    print("✅ النظام جاهز! / System Ready!")
    print("=" * 70)
    print()
    print("📍 للوصول من هذا الجهاز / Access from this device:")
    print(f"   🌐 http://localhost:{port}")
    print()
    print("📍 للوصول من أي جهاز في الشبكة / Access from any device:")
    print(f"   🌐 http://{local_ip}:{port}")
    print()
    print("📡 API Endpoints:")
    print(f"   • http://localhost:{port}/api/health")
    print(f"   • http://{local_ip}:{port}/api/health")
    print()
    print("⚠️  لا تغلق هذه النافذة! / Do not close this window!")
    print("⚠️  للإيقاف اضغط Ctrl+C / To stop press Ctrl+C")
    print("=" * 70)
    print()
    
    # Open browser in background thread
    browser_thread = threading.Thread(target=open_browser_delayed, args=(f"http://localhost:{port}",))
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e) or "WinError 10048" in str(e):
            print(f"\n❌ خطأ: المنفذ {port} قيد الاستخدام بالفعل")
            print(f"❌ Error: Port {port} is already in use")
            print("\n💡 حلول ممكنة:")
            print("1. أغلق البرنامج الآخر الذي يستخدم هذا المنفذ")
            print(f"2. استخدم منفذ آخر: SET PORT=8081 && python app.py")
            print(f"3. للبحث عن البرنامج: netstat -ano | findstr :{port}")
        else:
            print(f"❌ خطأ في بدء الخادم: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 إيقاف النظام... / Stopping system...")
        print("👋 شكراً لاستخدامك النظام! / Thank you!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)
