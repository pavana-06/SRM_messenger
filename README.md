# 🎓 University Chat Application

A real-time messaging web application built with Flask and Socket.IO for university environments.

## Features

✨ **Real-time Communication** - Messages appear instantly without page refresh
🏠 **Room-Based Chat** - Join specific chat rooms for different classes or groups
👥 **Multiple Users** - Support for simultaneous connections
💬 **Modern UI** - WhatsApp-style chat bubbles with timestamps
🔔 **Notifications** - See when users join or leave rooms
📱 **Responsive Design** - Works on desktop and mobile devices

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using the run script (recommended)
```bash
./run.sh
```

### Option 2: Direct Python execution
```bash
python3 app.py
```

The application will be available at: `http://localhost:5000`

**Note**: If you encounter PATH issues with Flask, use the run.sh script which properly sets up the environment.

## Production Deployment (WebSocket-safe)

Use a platform that supports long-lived WebSocket connections (Render, Railway, Fly.io, VM).  
This project includes:

- `Procfile` for `gunicorn + eventlet`
- `render.yaml` for one-click Render setup

### Required Environment Variables

- `SECRET_KEY`
- `SMTP_HOST`
- `SMTP_PORT` (usually `587`)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_USE_TLS` (`true` or `false`)

### Start Command (production)

```bash
gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT app:app
```

### Why not Vercel for this backend?

Vercel serverless functions are not a good fit for persistent Flask-SocketIO WebSocket sessions.  
For reliable real-time chat, deploy this backend on a WebSocket-friendly host.

## How to Use

1. Open `http://localhost:5000` in your browser
2. Enter a unique username
3. Enter a room name (e.g., "CS101", "Study Group", "Library")
4. Click "Join Chat Room"
5. Start chatting in real-time!

## Technical Details

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML, CSS, JavaScript with Socket.IO client
- **Storage**: In-memory (no database required)
- **Port**: 5000

## Project Structure

```
├── app.py                 # Flask backend with Socket.IO
├── templates/
│   ├── index.html        # Login page
│   └── chat.html         # Chat interface
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

## Features Explained

### User Management
- Username uniqueness validation
- Automatic disconnect handling
- Session management via Socket.IO

### Room System
- Users can create/join any room
- Messages are only visible within the same room
- Each room maintains its own user list

### Real-time Events
- `join` - User joins a room
- `send_message` - User sends a message
- `disconnect` - User leaves or disconnects
- `user_joined` - Notification broadcast
- `new_message` - Message broadcast
- `user_left` - Notification broadcast

## Development Notes

- No database required (perfect for demos)
- No external API dependencies
- Beginner-friendly code structure
- Well-commented and organized
- Production-ready with minimal setup

## Browser Compatibility

Works on all modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

## License

Free to use for educational purposes.
