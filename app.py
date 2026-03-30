from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'university-chat-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage
users = {}  # {username: {'sid': sid, 'room': room}}
rooms = {}  # {room_name: [usernames]}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')

    if not username or not room:
        return redirect(url_for('index'))

    # Check if username already exists
    if username in users:
        return redirect(url_for('index'))

    return render_template('chat.html', username=username, room=room)


@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']

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
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
