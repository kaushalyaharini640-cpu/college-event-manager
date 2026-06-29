import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'college-event-secret-key')

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('MONGO_DB_NAME', 'college_event_management')

mongo_client = None
mongo_db = None
storage_mode = None

memory_store = {
    'students': [],
    'admins': [
        {
            'name': 'Admin User',
            'email': 'admin@college.edu',
            'password': generate_password_hash('admin123')
        }
    ],
    'events': [
        {
            'id': 1,
            'name': 'AI Innovation Hackathon',
            'category': 'Hackathon',
            'date': '15 July 2026',
            'time': '10:00 AM',
            'venue': 'Innovation Lab',
            'organizer': 'Computer Science Dept.',
            'description': 'A hands-on coding challenge for students to build smart solutions using AI and automation.'
        },
        {
            'id': 2,
            'name': 'Career Growth Seminar',
            'category': 'Seminar',
            'date': '22 July 2026',
            'time': '2:00 PM',
            'venue': 'Main Auditorium',
            'organizer': 'Placement Cell',
            'description': 'An interactive seminar on resume building, internships, and interview preparation.'
        },
        {
            'id': 3,
            'name': 'Cultural Fest Evening',
            'category': 'Cultural Event',
            'date': '30 July 2026',
            'time': '6:30 PM',
            'venue': 'Open Air Stage',
            'organizer': 'Student Affairs',
            'description': 'A vibrant evening with performances, music, dance, and student-led showcases.'
        }
    ],
    'registrations': []
}


def connect_database():
    global mongo_client, mongo_db, storage_mode
    if storage_mode is not None:
        return

    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[DB_NAME]
        storage_mode = 'mongodb'
        seed_database()
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception):
        storage_mode = 'memory'
        seed_memory_store()


def seed_memory_store():
    if not memory_store['events']:
        memory_store['events'] = [
            {
                'id': 1,
                'name': 'AI Innovation Hackathon',
                'category': 'Hackathon',
                'date': '15 July 2026',
                'time': '10:00 AM',
                'venue': 'Innovation Lab',
                'organizer': 'Computer Science Dept.',
                'description': 'A hands-on coding challenge for students to build smart solutions using AI and automation.'
            },
            {
                'id': 2,
                'name': 'Career Growth Seminar',
                'category': 'Seminar',
                'date': '22 July 2026',
                'time': '2:00 PM',
                'venue': 'Main Auditorium',
                'organizer': 'Placement Cell',
                'description': 'An interactive seminar on resume building, internships, and interview preparation.'
            },
            {
                'id': 3,
                'name': 'Cultural Fest Evening',
                'category': 'Cultural Event',
                'date': '30 July 2026',
                'time': '6:30 PM',
                'venue': 'Open Air Stage',
                'organizer': 'Student Affairs',
                'description': 'A vibrant evening with performances, music, dance, and student-led showcases.'
            }
        ]
    if not memory_store['admins']:
        memory_store['admins'] = [{
            'name': 'Admin User',
            'email': 'admin@college.edu',
            'password': generate_password_hash('admin123')
        }]


def seed_database():
    if mongo_db is None:
        return
    if mongo_db.events.count_documents({}) == 0:
        mongo_db.events.insert_many([
            {
                'id': 1,
                'name': 'AI Innovation Hackathon',
                'category': 'Hackathon',
                'date': '15 July 2026',
                'time': '10:00 AM',
                'venue': 'Innovation Lab',
                'organizer': 'Computer Science Dept.',
                'description': 'A hands-on coding challenge for students to build smart solutions using AI and automation.'
            },
            {
                'id': 2,
                'name': 'Career Growth Seminar',
                'category': 'Seminar',
                'date': '22 July 2026',
                'time': '2:00 PM',
                'venue': 'Main Auditorium',
                'organizer': 'Placement Cell',
                'description': 'An interactive seminar on resume building, internships, and interview preparation.'
            },
            {
                'id': 3,
                'name': 'Cultural Fest Evening',
                'category': 'Cultural Event',
                'date': '30 July 2026',
                'time': '6:30 PM',
                'venue': 'Open Air Stage',
                'organizer': 'Student Affairs',
                'description': 'A vibrant evening with performances, music, dance, and student-led showcases.'
            }
        ])
    if mongo_db.admins.count_documents({}) == 0:
        mongo_db.admins.insert_one({
            'name': 'Admin User',
            'email': 'admin@college.edu',
            'password': generate_password_hash('admin123')
        })


def get_events():
    connect_database()
    if storage_mode == 'mongodb':
        events = list(mongo_db.events.find({}).sort('id', 1))
        return [{**event, 'id': event['id']} for event in events]
    return [dict(event) for event in memory_store['events']]


def get_event(event_id):
    connect_database()
    if storage_mode == 'mongodb':
        event = mongo_db.events.find_one({'id': event_id})
        return None if event is None else {**event, 'id': event['id']}
    return next((event for event in memory_store['events'] if event['id'] == event_id), None)


def find_student(email):
    connect_database()
    if storage_mode == 'mongodb':
        return mongo_db.students.find_one({'email': email})
    return next((student for student in memory_store['students'] if student['email'] == email), None)


def find_admin(email):
    connect_database()
    if storage_mode == 'mongodb':
        return mongo_db.admins.find_one({'email': email})
    return next((admin for admin in memory_store['admins'] if admin['email'] == email), None)


def create_student(name, email, password):
    connect_database()
    student = {
        'name': name,
        'email': email,
        'password': generate_password_hash(password)
    }
    if storage_mode == 'mongodb':
        mongo_db.students.insert_one(student)
    else:
        memory_store['students'].append(student)
    return student


def get_student_registrations(student_email):
    connect_database()
    if storage_mode == 'mongodb':
        registrations = list(mongo_db.registrations.find({'student_email': student_email}))
        return registrations
    return [reg for reg in memory_store['registrations'] if reg['student_email'] == student_email]


def register_event(student_email, event_id):
    connect_database()
    registration = {
        'student_email': student_email,
        'event_id': event_id,
        'status': 'Registered'
    }
    if storage_mode == 'mongodb':
        mongo_db.registrations.insert_one(registration)
    else:
        memory_store['registrations'].append(registration)
    return registration


@app.before_request
def load_user():
    session.setdefault('user', None)


@app.route('/')
def home():
    return render_template('index.html', events=get_events(), storage_mode=storage_mode)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        student = find_student(email)
        if student and check_password_hash(student['password'], password):
            session['user'] = {'name': student['name'], 'email': student['email'], 'role': 'student'}
            flash('Welcome back!')
            return redirect(url_for('student_dashboard'))

        admin = find_admin(email)
        if admin and check_password_hash(admin['password'], password):
            session['user'] = {'name': admin['name'], 'email': admin['email'], 'role': 'admin'}
            flash('Admin login successful.')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid email or password.')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash('Please fill in all fields.')
            return render_template('register.html')
        if find_student(email):
            flash('This email is already registered.')
            return render_template('register.html')
        create_student(name, email, password)
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/events')
def student_events():
    return render_template('student_events.html', events=get_events())


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = get_event(event_id)
    if event is None:
        return redirect(url_for('student_events'))
    return render_template('event_detail.html', event=event)


@app.route('/events/register/<int:event_id>', methods=['POST'])
def register_event_route(event_id):
    if not session.get('user') or session['user']['role'] != 'student':
        return redirect(url_for('login'))
    student_email = session['user']['email']
    register_event(student_email, event_id)
    flash('You have successfully registered for this event.')
    return redirect(url_for('student_dashboard'))


@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('user') or session['user']['role'] != 'student':
        return redirect(url_for('login'))
    registrations = get_student_registrations(session['user']['email'])
    student_events = [get_event(reg['event_id']) for reg in registrations if get_event(reg['event_id'])]
    return render_template('student_dashboard.html', events=student_events, user=session['user'])


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('user') or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', events=get_events(), user=session['user'])


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


if __name__ == '__main__':
    connect_database()
    app.run(debug=True)
