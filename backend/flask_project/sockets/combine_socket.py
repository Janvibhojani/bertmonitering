

# ====================newly started====================
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
from Services.scraper_service import run_scraper

authenticated_clients = {}
scraper_lock = threading.Lock()
watcher_started = False
user_subscriptions = {}

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
    
@sio.on("subscribe_selected")
def subscribe_selected(sid, data):
    """
    data = [{"marketName": "A", "rowIndex": 0}, ...]
    """
    # Find user's room
    user_room = None
    for room in sio.rooms(sid):
        if room != sid:
            user_room = room
            break

    if not user_room:
        sio.emit("status", {"error": "User room not found"}, to=sid)
        return

    user_subscriptions[user_room] = data
    print(f"✅ User {user_room} subscribed to {len(data)} rows")
    sio.emit("status", {"subscribed": len(data)}, to=sid)

        
# -------------------------
# Start Scraper
# -------------------------

@sio.on("start_combined")
def start_combined(sid, data):

    if sid not in authenticated_clients:
        sio.emit("status", {"error": "User not authenticated"}, to=sid)
        return


# async def send_to_clients(payload):
#     for sid in connected_clients:
#         try:
#             sio.emit("combined_scrape", payload, to=sid)
#         except Exception as e:
#             logging.error(f"Emit failed for {sid}: {e}")

async def send_to_clients(payload):
    """
    payload = {
        "type": "combined_scrape",
        "html_scrape": [...],
        "api_scrape": [...]
    }
    """

    for user_room, subscriptions in user_subscriptions.items():

        filtered_html = []
        filtered_api = []

        # -------------------------
        # HTML FILTERING
        # -------------------------
        for entry in payload.get("html_scrape", []):
            market_name = list(entry.keys())[0]
            market_data = entry[market_name]

            records = market_data.get("records", [])

            selected = [
                s["symbol"]
                for s in subscriptions
                if s["marketName"] == market_name
            ]

            filtered_records = [
                r for r in records
                if r.get("Name") in selected
            ]

            if filtered_records:
                filtered_html.append({
                    market_name: {
                        **market_data,
                        "records": filtered_records
                    }
                })


        # -------------------------
        # API FILTERING
        # -------------------------
        for entry in payload.get("api_scrape", []):

            market_name = entry.get("name")
            rows = entry.get("text", [])

            selected_rows = [
                s for s in subscriptions if s["marketName"] == market_name
            ]

            filtered_rows = [
                rows[s["rowIndex"]]
                for s in selected_rows
                if s["rowIndex"] < len(rows)
            ]

            if not filtered_rows:
                continue

            filtered_api.append({
                **entry,
                "text": filtered_rows
            })

        # -------------------------
        # EMIT TO USER ROOM
        # -------------------------
        filtered_payload = {
            "type": payload["type"],
            "html_scrape": filtered_html,
            "api_scrape": filtered_api
        }

        try:
            sio.emit("combined_scrape", filtered_payload, to=user_room)
        except Exception as e:
            logging.error(f"Emit failed for room {user_room}: {e}")

 # import at top
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
    
    
    
    