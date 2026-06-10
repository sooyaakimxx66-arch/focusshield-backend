from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pymysql
import os
pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

# ✅ Reads from Railway environment variable
db_url = os.environ.get('DATABASE_URL', '')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'focusshield_secret'

db = SQLAlchemy(app)


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name              = db.Column(db.String(255), nullable=False)
    email             = db.Column(db.String(255), unique=True, nullable=False)
    phone             = db.Column(db.String(50),  nullable=True)
    password          = db.Column(db.String(255), nullable=False)
    role              = db.Column(db.String(20),  nullable=False, default='student')  # student | teacher | parent
    class_name        = db.Column(db.String(50),  nullable=True)
    linked_student_id = db.Column(db.Integer, nullable=True)   # for parent accounts
    points            = db.Column(db.Integer, default=0)
    streak            = db.Column(db.Integer, default=0)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'
    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email    = db.Column(db.String(255), nullable=False)
    login_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name       = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20),  nullable=False)
    event      = db.Column(db.String(10),  nullable=False)   # 'login' | 'logout'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Motivation(db.Model):
    __tablename__ = 'motivation'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quote      = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    __tablename__ = 'notes'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title      = db.Column(db.String(255), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Homework(db.Model):
    __tablename__ = 'homework'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject     = db.Column(db.String(100), nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    color       = db.Column(db.String(20),  nullable=True)
    due_date    = db.Column(db.Date, nullable=True)
    created_by  = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class HomeworkStatus(db.Model):
    __tablename__ = 'homework_status'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id  = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    completed   = db.Column(db.Boolean, default=False)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Test(db.Model):
    __tablename__ = 'tests'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title      = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_id       = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    question      = db.Column(db.String(500), nullable=False)
    option_a      = db.Column(db.String(255), nullable=False)
    option_b      = db.Column(db.String(255), nullable=False)
    option_c      = db.Column(db.String(255), nullable=False)
    option_d      = db.Column(db.String(255), nullable=False)
    correct_index = db.Column(db.Integer, nullable=False)   # 0=A .. 3=D

class TestAttempt(db.Model):
    __tablename__ = 'test_attempts'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_id    = db.Column(db.Integer, db.ForeignKey('tests.id'),  nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    score      = db.Column(db.Integer, nullable=False)
    total      = db.Column(db.Integer, nullable=False)
    xp         = db.Column(db.Integer, default=0)
    best_combo = db.Column(db.Integer, default=0)
    taken_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    __tablename__ = 'badges'
    id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name    = db.Column(db.String(100), nullable=False)
    icon    = db.Column(db.String(50),  nullable=True)
    earned  = db.Column(db.Boolean, default=False)

class FocusSession(db.Model):
    __tablename__ = 'focus_sessions'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    minutes    = db.Column(db.Integer, nullable=False)
    completed  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        required = ['name', 'email', 'password', 'confirm_password']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        if data['password'] != data['confirm_password']:
            return jsonify({'error': 'Passwords do not match'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        role = data.get('role', 'student')
        linked_student_id = data.get('linked_student_id')

        # Parent accounts must link to an existing student via their email
        if role == 'parent':
            child_email = (data.get('child_email') or '').strip()
            if not child_email:
                return jsonify({'error': "Child's email is required"}), 400
            child = User.query.filter_by(email=child_email, role='student').first()
            if not child:
                return jsonify(
                    {'error': 'No student account found with that email'}), 404
            linked_student_id = child.id

        new_user = User(
            name=data['name'], email=data['email'],
            phone=data.get('phone'),
            password=generate_password_hash(data['password']),
            role=role,
            class_name=data.get('class_name'),
            linked_student_id=linked_student_id
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully', 'id': new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Track current session + activity history
        db.session.add(ActiveSession(email=user.email))
        db.session.add(ActivityLog(user_id=user.id, name=user.name,
                                   role=user.role, event='login'))
        db.session.commit()

        return jsonify({'message': 'Login successful', 'user': {
            'id': user.id, 'name': user.name, 'email': user.email,
            'role': user.role, 'class_name': user.class_name,
            'linked_student_id': user.linked_student_id,
            'points': user.points, 'streak': user.streak
        }}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    try:
        data  = request.get_json()
        email = data.get('email') if data else None
        if not email:
            return jsonify({'error': 'Email required'}), 400
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.add(ActivityLog(user_id=user.id, name=user.name,
                                       role=user.role, event='logout'))
        ActiveSession.query.filter_by(email=email).delete()
        db.session.commit()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    try:
        last = ActiveSession.query.order_by(ActiveSession.id.desc()).first()
        if not last:
            return jsonify({'error': 'No active user found'}), 404
        user = User.query.filter_by(email=last.email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'id': user.id, 'name': user.name, 'email': user.email,
            'role': user.role, 'class_name': user.class_name,
            'linked_student_id': user.linked_student_id,
            'points': user.points, 'streak': user.streak
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────

@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'id': user.id, 'name': user.name, 'email': user.email,
            'phone': user.phone, 'role': user.role,
            'class_name': user.class_name, 'points': user.points,
            'streak': user.streak,
            'created_at': user.created_at.strftime('%d %b %Y')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.name       = data.get('name',       user.name)
        user.phone      = data.get('phone',      user.phone)
        user.class_name = data.get('class_name', user.class_name)
        db.session.commit()
        return jsonify({'message': 'Profile updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/change_password/<int:user_id>', methods=['POST'])
def change_password(user_id):
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not check_password_hash(user.password, data.get('current_password', '')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        user.password = generate_password_hash(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# ACTIVITY LOG (login / logout history)
# ─────────────────────────────────────────

@app.route('/activity', methods=['GET'])
def get_activity():
    """Recent login/logout events. Optional ?student_id= to filter one student."""
    try:
        student_id = request.args.get('student_id', type=int)
        limit      = int(request.args.get('limit', 50))
        query = ActivityLog.query
        if student_id:
            query = query.filter_by(user_id=student_id)
        logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
        return jsonify([{
            'id': l.id, 'user_id': l.user_id, 'name': l.name,
            'role': l.role, 'event': l.event,
            'time': l.created_at.strftime('%d %b, %I:%M %p')
        } for l in logs]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# MOTIVATION (today's quote)
# ─────────────────────────────────────────

@app.route('/motivation', methods=['GET'])
def get_motivation():
    try:
        latest = Motivation.query.order_by(Motivation.id.desc()).first()
        quote = latest.quote if latest else 'Stay focused and keep learning!'
        return jsonify({'quote': quote}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/motivation', methods=['POST'])
def set_motivation():
    try:
        data = request.get_json()
        if not data or not data.get('quote'):
            return jsonify({'error': 'Quote required'}), 400
        m = Motivation(quote=data['quote'], created_by=data.get('created_by'))
        db.session.add(m)
        db.session.commit()
        return jsonify({'message': "Today's motivation updated", 'id': m.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# NOTES (teacher -> students)
# ─────────────────────────────────────────

@app.route('/notes', methods=['GET'])
def get_notes():
    try:
        notes = Note.query.order_by(Note.created_at.desc()).all()
        return jsonify([{
            'id': n.id, 'title': n.title, 'body': n.body,
            'created_at': n.created_at.strftime('%d %b, %I:%M %p')
        } for n in notes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/notes', methods=['POST'])
def add_note():
    try:
        data = request.get_json()
        if not data or not (data.get('title') or data.get('body')):
            return jsonify({'error': 'Title or body required'}), 400
        n = Note(title=data.get('title', 'Note'), body=data.get('body', ''),
                 created_by=data.get('created_by'))
        db.session.add(n)
        db.session.commit()
        return jsonify({'message': 'Note posted', 'id': n.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        db.session.delete(note)
        db.session.commit()
        return jsonify({'message': 'Note deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# HOMEWORK
# ─────────────────────────────────────────

@app.route('/homework/<int:student_id>', methods=['GET'])
def get_homework(student_id):
    """Homework list with this student's completion status."""
    try:
        items = Homework.query.order_by(Homework.created_at.desc()).all()
        result = []
        for h in items:
            status = HomeworkStatus.query.filter_by(
                homework_id=h.id, student_id=student_id).first()
            result.append({
                'id': h.id, 'subject': h.subject, 'title': h.title,
                'description': h.description, 'color': h.color,
                'due_date': h.due_date.strftime('%d %b %Y') if h.due_date else None,
                'completed': bool(status.completed) if status else False
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/homework', methods=['POST'])
def add_homework():
    try:
        data     = request.get_json()
        required = ['subject', 'title']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        due = datetime.strptime(data['due_date'], '%Y-%m-%d').date() \
            if data.get('due_date') else None
        h = Homework(
            subject=data['subject'], title=data['title'],
            description=data.get('description', ''), color=data.get('color', ''),
            due_date=due, created_by=data.get('created_by')
        )
        db.session.add(h)
        db.session.commit()
        return jsonify({'message': 'Homework assigned', 'id': h.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/homework/<int:homework_id>/complete', methods=['POST'])
def complete_homework(homework_id):
    try:
        data       = request.get_json()
        student_id = data.get('student_id')
        completed  = bool(data.get('completed', True))
        if not student_id:
            return jsonify({'error': 'student_id required'}), 400
        status = HomeworkStatus.query.filter_by(
            homework_id=homework_id, student_id=student_id).first()
        if status:
            status.completed = completed
        else:
            db.session.add(HomeworkStatus(homework_id=homework_id,
                                          student_id=student_id,
                                          completed=completed))
        db.session.commit()
        return jsonify({'message': 'Homework status updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/homework/<int:homework_id>', methods=['DELETE'])
def delete_homework(homework_id):
    try:
        h = Homework.query.get(homework_id)
        if not h:
            return jsonify({'error': 'Homework not found'}), 404
        HomeworkStatus.query.filter_by(homework_id=homework_id).delete()
        db.session.delete(h)
        db.session.commit()
        return jsonify({'message': 'Homework deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# TESTS (MCQ)
# ─────────────────────────────────────────

@app.route('/tests', methods=['GET'])
def get_tests():
    try:
        tests = Test.query.order_by(Test.created_at.desc()).all()
        return jsonify([{
            'id': t.id, 'title': t.title,
            'question_count': Question.query.filter_by(test_id=t.id).count(),
            'created_at': t.created_at.strftime('%d %b %Y')
        } for t in tests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    """A test with its questions (for a student to take)."""
    try:
        test = Test.query.get(test_id)
        if not test:
            return jsonify({'error': 'Test not found'}), 404
        questions = Question.query.filter_by(test_id=test_id).all()
        return jsonify({
            'id': test.id, 'title': test.title,
            'questions': [{
                'id': q.id, 'question': q.question,
                'options': [q.option_a, q.option_b, q.option_c, q.option_d],
                'correct_index': q.correct_index
            } for q in questions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tests', methods=['POST'])
def create_test():
    """Create a test along with its questions in one call."""
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'error': 'Title required'}), 400
        test = Test(title=data['title'], created_by=data.get('created_by'))
        db.session.add(test)
        db.session.flush()   # get test.id before adding questions
        for q in data.get('questions', []):
            opts = q.get('options', ['', '', '', ''])
            db.session.add(Question(
                test_id=test.id, question=q.get('question', ''),
                option_a=opts[0], option_b=opts[1],
                option_c=opts[2], option_d=opts[3],
                correct_index=q.get('correct_index', 0)
            ))
        db.session.commit()
        return jsonify({'message': 'Test created', 'id': test.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/tests/<int:test_id>', methods=['DELETE'])
def delete_test(test_id):
    try:
        test = Test.query.get(test_id)
        if not test:
            return jsonify({'error': 'Test not found'}), 404
        Question.query.filter_by(test_id=test_id).delete()
        db.session.delete(test)
        db.session.commit()
        return jsonify({'message': 'Test deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/test_attempts', methods=['POST'])
def submit_attempt():
    """Save a student's result and award the earned XP to their points."""
    try:
        data     = request.get_json()
        required = ['test_id', 'student_id', 'score', 'total']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        attempt = TestAttempt(
            test_id=data['test_id'], student_id=data['student_id'],
            score=data['score'], total=data['total'],
            xp=data.get('xp', 0), best_combo=data.get('best_combo', 0)
        )
        db.session.add(attempt)
        # Add earned XP to the student's points
        student = User.query.get(data['student_id'])
        if student:
            student.points = (student.points or 0) + int(data.get('xp', 0))
        db.session.commit()
        return jsonify({'message': 'Attempt saved', 'id': attempt.id,
                        'new_points': student.points if student else None}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# REWARDS (points, streak, badges)
# ─────────────────────────────────────────

@app.route('/rewards/<int:user_id>', methods=['GET'])
def get_rewards(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        badges = Badge.query.filter_by(user_id=user_id).all()
        return jsonify({
            'points': user.points, 'streak': user.streak,
            'badges': [{
                'name': b.name, 'icon': b.icon, 'earned': bool(b.earned)
            } for b in badges]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# FOCUS SESSIONS
# ─────────────────────────────────────────

@app.route('/focus_sessions', methods=['POST'])
def add_focus_session():
    try:
        data = request.get_json()
        required = ['student_id', 'minutes']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        fs = FocusSession(
            student_id=data['student_id'], minutes=data['minutes'],
            completed=bool(data.get('completed', True))
        )
        db.session.add(fs)
        db.session.commit()
        return jsonify({'message': 'Focus session saved', 'id': fs.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/focus/<int:student_id>/summary', methods=['GET'])
def focus_summary(student_id):
    try:
        sessions = FocusSession.query.filter_by(student_id=student_id).all()
        total_minutes = sum(s.minutes for s in sessions if s.completed)
        return jsonify({
            'sessions_completed': len([s for s in sessions if s.completed]),
            'total_minutes': total_minutes,
            'total_hours': round(total_minutes / 60, 1)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# DASHBOARDS (aggregate endpoints)
# ─────────────────────────────────────────

@app.route('/dashboard/student/<int:user_id>', methods=['GET'])
def student_dashboard(user_id):
    """Everything the student home screen needs in one call."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        latest_quote = Motivation.query.order_by(Motivation.id.desc()).first()

        homework = []
        for h in Homework.query.order_by(Homework.created_at.desc()).all():
            status = HomeworkStatus.query.filter_by(
                homework_id=h.id, student_id=user_id).first()
            homework.append({
                'id': h.id, 'subject': h.subject, 'title': h.title,
                'color': h.color,
                'completed': bool(status.completed) if status else False
            })

        return jsonify({
            'name': user.name, 'points': user.points, 'streak': user.streak,
            'motivation': latest_quote.quote if latest_quote else '',
            'homework': homework,
            'notes_count': Note.query.count()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard/parent/<int:parent_id>', methods=['GET'])
def parent_dashboard(parent_id):
    """Linked child's progress, focus time and completion."""
    try:
        parent = User.query.get(parent_id)
        if not parent or not parent.linked_student_id:
            return jsonify({'error': 'No linked student'}), 404
        sid   = parent.linked_student_id
        child = User.query.get(sid)

        homework  = Homework.query.count()
        done      = HomeworkStatus.query.filter_by(student_id=sid, completed=True).count()

        sessions  = FocusSession.query.filter_by(student_id=sid).all()
        focus_min = sum(s.minutes for s in sessions if s.completed)

        attempts  = TestAttempt.query.filter_by(student_id=sid).all()
        avg_pct   = round(sum((a.score / a.total) * 100 for a in attempts) / len(attempts), 0) \
            if attempts else 0

        return jsonify({
            'child_name': child.name if child else 'Student',
            'class_name': child.class_name if child else '',
            'streak': child.streak if child else 0,
            'tasks_done': done, 'tasks_total': homework,
            'focus_hours': round(focus_min / 60, 1),
            'avg_score_pct': avg_pct
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics', methods=['GET'])
def teacher_analytics():
    """Class-wide summary for the teacher analytics screen."""
    try:
        students = User.query.filter_by(role='student').all()
        student_ids = [s.id for s in students]
        total_students = len(students)

        # Homework completion rate across all students
        total_hw = Homework.query.count()
        if total_hw and total_students:
            done = HomeworkStatus.query.filter_by(completed=True).count()
            completion_rate = round(done / (total_hw * total_students), 2)
        else:
            completion_rate = 0

        # Average score (out of 10) from attempts
        attempts = TestAttempt.query.all()
        if attempts:
            avg_score = round(sum((a.score / a.total) * 10 for a in attempts) / len(attempts), 1)
        else:
            avg_score = 0

        # Student ranking by points
        ranking = sorted(
            [{'name': s.name, 'points': s.points or 0} for s in students],
            key=lambda x: x['points'], reverse=True
        )[:5]

        # Real average score (%) per test, from actual attempts
        test_performance = []
        for t in Test.query.order_by(Test.id).all():
            atts = TestAttempt.query.filter_by(test_id=t.id).all()
            avg_pct = round(
                sum((a.score / a.total) * 100 for a in atts) / len(atts)) \
                if atts else 0
            test_performance.append({
                'title': t.title,
                'avg_pct': avg_pct,
                'attempts': len(atts),
            })

        return jsonify({
            'total_students': total_students,
            'completion_rate': completion_rate,
            'avg_score': avg_score,
            'ranking': ranking,
            'test_performance': test_performance
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
