import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat-secret'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# In-memory storage
users = {}   # {username: {'sid': sid, 'room': room}}
rooms = {}   # {room: [usernames]}


@app.route('/')
def index():
    return render_template('index.html')


# ✅ Only username + room
@app.route('/join', methods=['POST'])
def join_page():
    username = (request.form.get('username') or '').strip()
    room = (request.form.get('room') or '').strip()

    if not username or not room:
        return redirect(url_for('index'))

    session['username'] = username
    session['room'] = room

    return redirect(url_for('chat'))


@app.route('/chat')
def chat():
    username = session.get('username')
    room = session.get('room')

    if not username or not room:
        return redirect(url_for('index'))

    return render_template('chat.html', username=username, room=room)


# 🔌 SOCKET EVENTS

@socketio.on('join')
def handle_join(data):
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