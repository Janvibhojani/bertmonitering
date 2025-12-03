# sockets/socket_instance.py
import socketio

# Create Socket.IO server instance (async_mode='threading' avoids eventlet)
sio = socketio.Server(cors_allowed_origins="*", async_mode="threading")
