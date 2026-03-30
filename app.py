from dotenv import load_dotenv
import os

load_dotenv()

print("SMTP_HOST =", os.getenv("SMTP_HOST"))
print("SMTP_USER =", os.getenv("SMTP_USER"))
print("SMTP_PASSWORD =", os.getenv("SMTP_PASSWORD"))

from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import re
import secrets
import os   
import smtplib
from email.message import EmailMessage
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'university-chat-secret-key-2024')
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=os.getenv('SOCKETIO_ASYNC_MODE', 'threading')
)

# In-memory storage
accounts = {}  # {email: password_hash}
pending_verifications = {}  # {email: {"password_hash": str, "code": str}}
users = {}  # {username: {'sid': sid, 'room': room}}
rooms = {}  # {room_name: [usernames]}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
COLLEGE_DOMAIN = "@srmap.edu.in"


def is_valid_email(value: str) -> bool:
    if not value:
        return False
    value = value.strip()
    return bool(EMAIL_RE.match(value))


def is_college_email(value: str) -> bool:
    if not is_valid_email(value):
        return False
    return value.lower().endswith(COLLEGE_DOMAIN)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def send_verification_email(recipient_email: str, code: str) -> bool:
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_from = os.getenv('SMTP_FROM', smtp_user or '')
    use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    if not smtp_host or not smtp_user or not smtp_password or not smtp_from:
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Your University Chat OTP'
    msg['From'] = smtp_from
    msg['To'] = recipient_email
    msg.set_content(
        f"Your University Chat verification code is: {code}\n"
        "This code is valid for your current signup flow."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True


def require_login():
    email = session.get('email')
    if not email:
        return None
    if not is_college_email(email) or email not in accounts:
        return None
    return email


@app.route('/')
def index():
    return render_template('index.html')

@app.post('/signup')
def signup():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''

    if not is_college_email(email) or len(password) < 6:
        return redirect(url_for('index'))

    if email in accounts:
        return redirect(url_for('index'))

    code = generate_verification_code()
    pending_verifications[email] = {
        'password_hash': generate_password_hash(password),
        'code': code
    }
    session['pending_email'] = email
    try:
        sent = send_verification_email(email, code)
    except Exception:
        sent = False

    if not sent:
        pending_verifications.pop(email, None)
        session.pop('pending_email', None)
        return redirect(url_for('index', error='otp_send_failed'))

    return redirect(url_for('verify_email'))


@app.post('/login')
def login():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''

    if not is_college_email(email) or not password:
        return redirect(url_for('index'))

    password_hash = accounts.get(email)
    if not password_hash or not check_password_hash(password_hash, password):
        return redirect(url_for('index'))

    session['email'] = email
    return redirect(url_for('join'))


@app.route('/verify', methods=['GET', 'POST'])
def verify_email():
    email = session.get('pending_email')
    if not email or email not in pending_verifications:
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('verify.html', email=email)

    code = (request.form.get('code') or '').strip()
    pending = pending_verifications.get(email)
    if not pending or code != pending['code']:
        return redirect(url_for('verify_email'))

    accounts[email] = pending['password_hash']
    del pending_verifications[email]
    session.pop('pending_email', None)
    session['email'] = email
    return redirect(url_for('join'))

@app.post('/resend-otp')
def resend_otp():
    email = session.get('pending_email')
    if not email:
        return redirect(url_for('index'))

    pending = pending_verifications.get(email)
    if not pending:
        return redirect(url_for('index'))

    code = generate_verification_code()
    pending['code'] = code
    pending_verifications[email] = pending

    try:
        sent = send_verification_email(email, code)
    except Exception:
        sent = False

    if not sent:
        return redirect(url_for('verify_email', error='otp_send_failed'))

    return redirect(url_for('verify_email', message='otp_resent'))


@app.get('/logout')
def logout():
    session.pop('email', None)
    session.pop('pending_email', None)
    session.pop('chat_username', None)
    session.pop('room', None)
    return redirect(url_for('index'))


@app.route('/join', methods=['GET', 'POST'])
def join():
    email = require_login()
    if not email:
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('join.html', email=email)

    username = (request.form.get('username') or '').strip()
    room = (request.form.get('room') or '').strip()

    if not username or not room:
        return redirect(url_for('join'))

    # Store desired chat identity in session
    session['chat_username'] = username
    session['room'] = room
    return redirect(url_for('chat'))


@app.route('/chat')
def chat():
    email = require_login()
    if not email:
        return redirect(url_for('index'))

    username = session.get('chat_username')
    room = session.get('room')
    if not username or not room:
        return redirect(url_for('join'))

    # Check if username already exists
    if username in users:
        return redirect(url_for('join'))

    return render_template('chat.html', username=username, room=room)


@socketio.on('join')
def handle_join(data):
    email = session.get('email')
    if not email or email not in accounts or not is_college_email(email):
        emit('error', {'message': 'Please login first'})
        return

    username = (data.get('username') or '').strip()
    room = (data.get('room') or '').strip()

    if not username or not room:
        emit('error', {'message': 'Missing username or room'})
        return

    # Check if username is already taken
    if username in users:
        emit('error', {'message': 'Username already taken'})
        return

    # Store user info
    users[username] = {'sid': request.sid, 'room': room}

    # Add user to room
    if room not in rooms:
        rooms[room] = []
    rooms[room].append(username)

    # Join the Socket.IO room
    join_room(room)

    # Notify room that user joined
    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)


@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    message = data['message']
    room = data['room']

    # Broadcast message to room
    emit('new_message', {
        'username': username,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)


@socketio.on('disconnect')
def handle_disconnect():
    # Find and remove disconnected user
    disconnected_user = None
    disconnected_room = None

    for username, info in users.items():
        if info['sid'] == request.sid:
            disconnected_user = username
            disconnected_room = info['room']
            break

    if disconnected_user:
        # Remove from rooms
        if disconnected_room in rooms:
            rooms[disconnected_room].remove(disconnected_user)
            if not rooms[disconnected_room]:
                del rooms[disconnected_room]

        # Remove from users
        del users[disconnected_user]

        # Notify room
        emit('user_left', {
            'username': disconnected_user,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=disconnected_room)


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.getenv('PORT', '5000'))
    socketio.run(app, debug=debug_mode, port=port, allow_unsafe_werkzeug=True)
print("SMTP_HOST:", os.getenv("SMTP_HOST"))