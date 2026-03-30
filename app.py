import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime
import re
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'university-chat-secret-key-2024')

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# In-memory storage
accounts = {}  # {email: password_hash}
users = {}     # {username: {'sid': sid, 'room': room}}
rooms = {}     # {room_name: [usernames]}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
COLLEGE_DOMAIN = "@srmap.edu.in"


def is_valid_email(value: str) -> bool:
    return bool(value and EMAIL_RE.match(value.strip()))


def is_college_email(value: str) -> bool:
    return is_valid_email(value) and value.lower().endswith(COLLEGE_DOMAIN)


def require_login():
    email = session.get('email')
    if not email or email not in accounts:
        return None
    return email


@app.route('/')
def index():
    return render_template('index.html')


# ✅ UPDATED SIGNUP (NO OTP)
@app.post('/signup')
def signup():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''

    if not is_college_email(email) or len(password) < 6:
        return redirect(url_for('index'))

    if email in accounts:
        return redirect(url_for('index'))

    # Direct account creation
    accounts[email] = generate_password_hash(password)

    # Auto login
    session['email'] = email

    return redirect(url_for('join'))


@app.post('/login')
def login():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''

    if not is_college_email(email):
        return redirect(url_for('index'))

    password_hash = accounts.get(email)
    if not password_hash or not check_password_hash(password_hash, password):
        return redirect(url_for('index'))

    session['email'] = email
    return redirect(url_for('join'))


@app.get('/logout')
def logout():
    session.clear()
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

    if username in users:
        return redirect(url_for('join'))

    return render_template('chat.html', username=username, room=room)


# 🔌 SOCKET EVENTS

@socketio.on('join')
def handle_join(data):
    email = session.get('email')
    if not email or email not in accounts:
        emit('error', {'message': 'Please login first'})
        return

    username = data.get('username')
    room = data.get('room')

    if not username or not room:
        emit('error', {'message': 'Missing username or room'})
        return

    if username in users:
        emit('error', {'message': 'Username already taken'})
        return

    users[username] = {'sid': request.sid, 'room': room}

    if room not in rooms:
        rooms[room] = []
    rooms[room].append(username)

    join_room(room)

    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)


@socketio.on('send_message')
def handle_message(data):
    emit('new_message', {
        'username': data['username'],
        'message': data['message'],
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=data['room'])


@socketio.on('disconnect')
def handle_disconnect():
    disconnected_user = None
    disconnected_room = None

    for username, info in users.items():
        if info['sid'] == request.sid:
            disconnected_user = username
            disconnected_room = info['room']
            break

    if disconnected_user:
        if disconnected_room in rooms:
            rooms[disconnected_room].remove(disconnected_user)
            if not rooms[disconnected_room]:
                del rooms[disconnected_room]

        del users[disconnected_user]

        emit('user_left', {
            'username': disconnected_user,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=disconnected_room)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, debug=True, port=port, allow_unsafe_werkzeug=True)