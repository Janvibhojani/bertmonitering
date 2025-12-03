# # sockets/combine_socket.py
# import logging
# from sockets.socket_instance import sio

# logging.basicConfig(level=logging.INFO)

# connected_clients = set()

# @sio.event
# def connect(sid, environ):
#     logging.info(f"Client connected: {sid}")
#     connected_clients.add(sid)
#     sio.emit("server_message", {"msg": "✅ Connected to server!"}, to=sid)

# @sio.event
# def disconnect(sid):
#     logging.info(f"Client disconnected: {sid}")
#     connected_clients.discard(sid)

# # Example custom event: client -> server
# @sio.event
# def client_message(sid, data):
#     logging.info(f"Received from {sid}: {data}")
#     # Send back data to that same client
#     sio.emit("server_message", {"msg": f"Got your message: {data}"}, to=sid)

# # Example function to broadcast live data to all clients
# def broadcast_data(data):
#     logging.info(f"Broadcasting data: {data}")
#     sio.emit("live_data", data)

import logging
from sockets.socket_instance import sio

logging.basicConfig(level=logging.INFO)

connected_clients = set()

@sio.event
def connect(sid, environ):
    logging.info(f"Client connected: {sid}")
    connected_clients.add(sid)
    sio.emit("server_message", {"msg": f"✅ Client {sid[:5]} connected!"}, to=sid)

@sio.event
def disconnect(sid):
    logging.info(f"Client disconnected: {sid}")
    connected_clients.discard(sid)


# ---------------------------
# 🔹 When a client sends data
# ---------------------------
@sio.event
def client_message(sid, data):
    logging.info(f"Received from {sid}: {data}")

    # 1️⃣ Confirm receipt to sender
    sio.emit("server_message", {
        "msg": f"📨 Message received: {data}"
    }, to=sid)

    # 2️⃣ Broadcast message to ALL OTHER clients
    for client_sid in list(connected_clients):
        if client_sid != sid:  # Don't send back to the sender
            try:
                sio.emit("server_message", {
                    "msg": f"💬 From {sid[:5]}: {data}"
                }, to=client_sid)
            except Exception as e:
                logging.warning(f"Failed to send to {client_sid}: {e}")
                connected_clients.discard(client_sid)


# ---------------------------
# 🔹 Function to broadcast data
# ---------------------------
def broadcast_data(data):
    """Broadcast live data updates to all clients."""
    logging.info(f"Broadcasting data: {data}")
    sio.emit("live_data", data)
