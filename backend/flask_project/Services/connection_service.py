# services/connection_service.py
import logging

connected_clients = set()


def handle_connect(sio, sid):
    connected_clients.add(sid)
    logging.info(f"Client connected: {sid}")

    sio.emit("status", {
        "status": "connected",
        "message": "Connected. Please authenticate."
    }, to=sid)

def handle_disconnect(sid, authenticated_clients):
    logging.info(f"Client disconnected: {sid}")
    connected_clients.discard(sid)
    authenticated_clients.pop(sid, None)
    print(connected_clients)
    print(authenticated_clients)
    return len(connected_clients) == 0
    # return True if no clients left

def get_connected_clients():
    return list(connected_clients)

def get_authenticated_clients(authenticated_clients):
    return authenticated_clients.copy()