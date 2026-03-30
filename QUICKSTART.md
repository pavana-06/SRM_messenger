# 🚀 Quick Start Guide

## Running the Chat Application

### Step 1: Start the Server
```bash
python3 app.py
```
or
```bash
./run.sh
```

### Step 2: Open Your Browser
Navigate to: **http://localhost:5000**

### Step 3: Join a Chat Room
1. Enter your username (e.g., "Alice")
2. Enter a room name (e.g., "CS101")
3. Click "Join Chat Room"

### Step 4: Test with Multiple Users
1. Open another browser window (or use incognito mode)
2. Go to http://localhost:5000
3. Use a different username (e.g., "Bob")
4. Join the **same room** (e.g., "CS101")
5. Start chatting!

## Example Scenarios

### Scenario 1: Class Discussion
- Room: "CS101"
- Users: Alice, Bob, Charlie
- Use case: Discussing homework assignments

### Scenario 2: Study Group
- Room: "MidtermStudy"
- Users: Sarah, Mike, Emma
- Use case: Collaborative exam preparation

### Scenario 3: Project Team
- Room: "FinalProject"
- Users: Team members
- Use case: Real-time project coordination

## Features to Try

✅ **Send Messages** - Type and press Enter or click Send
✅ **Join Notifications** - Watch as users join the room
✅ **Leave Notifications** - Close a tab to see leave notification
✅ **Multiple Rooms** - Create different rooms for different purposes
✅ **Timestamps** - Every message shows the time it was sent
✅ **Chat Bubbles** - Your messages appear on the right, others on the left

## Troubleshooting

### Port Already in Use
If port 5000 is busy, change the port in `app.py`:
```python
socketio.run(app, debug=True, port=5001)  # Change to 5001
```

### Username Taken
If you see "Username already taken", either:
- Choose a different username
- Wait for the previous user with that name to disconnect
- Refresh the page if it's a stale session

### Can't See Messages
Make sure:
- Both users are in the **same room**
- Your browser allows WebSocket connections
- No firewall is blocking port 5000

## Tips for Demo

1. **Prepare Multiple Browser Windows** - Have 2-3 windows ready
2. **Use Descriptive Usernames** - Makes it clearer who is who
3. **Show Different Rooms** - Demonstrate room isolation
4. **Test Disconnect** - Close a window to show leave notification
5. **Highlight Real-time Nature** - Type in one window, see it instantly in another

Enjoy your chat application! 🎓💬
