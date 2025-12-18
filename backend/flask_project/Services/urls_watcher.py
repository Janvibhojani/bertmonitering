# combine_socket.py
import asyncio
import threading
import logging
from socket_instance import sio
from Services.json_room_watcher import start_json_watcher
from Services.connection_service import (
    handle_connect,
    handle_disconnect,
    connected_clients
)
from Services.auth_service import authenticate_user
# from Services.scraper_service import run_scraper, stop_scraper


authenticated_clients = {}
scraper_lock = threading.Lock()
watcher_started = False

# -------------------------
# Connect
# -------------------------
@sio.event
def connect(sid, environ):
    global watcher_started
    handle_connect(sio, sid)

    if not watcher_started:
        start_json_watcher(sio)
        watcher_started = True
# -------------------------
# Authenticate
# -------------------------
@sio.on("authenticate")
def authenticate(sid, data):
    authenticate_user(sio, sid, data, authenticated_clients)


# -------------------------
# Disconnect
# -------------------------
@sio.event
def disconnect(sid):
    global authenticated_clients
    print(f"Client disconnected: {sid}")
    

@sio.on("join_user_room")
def join_user_room(sid, data):
    user_id = data.get("user_id")
    if not user_id:
        sio.emit("status", {
            "error": "user_id missing to join room"
        }, to=sid)
        return
    sio.enter_room(sid, user_id)
    print(f"✅ SID {sid} joined room for user {user_id}")
    sio.emit("status", {
        "status": "joined_room",
        "message": f"Joined room for user {user_id}"
    }, to=sid)
        

# -------------------------
# Start Scraper
# -------------------------

@sio.on("start_combined")
def start_combined(sid, data):

    if sid not in authenticated_clients:
        sio.emit("status", {"error": "User not authenticated"}, to=sid)
        return


async def send_to_clients(payload):
    for sid in connected_clients:
        try:
            sio.emit("combined_scrape", payload, to=sid)
        except Exception as e:
            logging.error(f"Emit failed for {sid}: {e}")
        
from Services.scraper_service import run_scraper  # import at top
def thread_runner():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # expose this loop so other threads (Flask handlers) can schedule coros onto it
   
    try:
        loop.run_until_complete(
            run_scraper(
                sio,
                connected_clients,
                authenticated_clients
            )
        )
    finally:
        # cleanup: unset scraper_loop after loop ends
        loop.close()