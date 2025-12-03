# sockets/run.py
from flask import Flask
from flask_cors import CORS
from sockets.socket_instance import sio
from sockets import combine_socket  # to register socket events
import socketio
# Create Flask app
app = Flask(__name__)
CORS(app)

# Wrap Flask app with Socket.IO middleware
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

if __name__ == "__main__":
    print("🚀 Flask + Socket.IO server running on http://0.0.0.0:5001")
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5001, app, use_reloader=True)
