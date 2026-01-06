# combine_socket.py
import asyncio
import logging
from socket_instance import sio
from Services.connection_service import handle_connect, connected_clients
from Services.auth_service import authenticate_user, authenticated_clients
from Services.scraper_service import run_scraper, get_is_running
from controllers.user_controller import get_user_subscriptions

watcher_started = False
user_subscriptions = {}

# ================= CONNECT =================

@sio.event
def connect(sid, environ):
    handle_connect(sio, sid)
    logging.info(f"🔌 Connected: {sid}")

@sio.event
def disconnect(sid):
    authenticated_clients.pop(sid, None)
    connected_clients.discard(sid)
    logging.info(f"❌ Disconnected: {sid}")

# ================= AUTH =================

@sio.on("authenticate")
def authenticate(sid, data):
    authenticate_user(sio, sid, data, authenticated_clients)

# ================= SUBSCRIBE =================

@sio.on("subscribe_selected")
def subscribe_selected(sid, data):
    user = authenticated_clients.get(sid)
    if not user:
        return

    user_id = user["user_id"]
    user_room = f"user:{user_id}"
    user_subscriptions[user_room] = data

# ================= SUBSCRIBER LIST =================

@sio.on("Subscriber_list")
def get_subscriber_list(sid):
    user = authenticated_clients.get(sid)
    if not user:
        return

    user_id = user["user_id"]
    subscriptions = get_user_subscriptions(user_id)

    sio.emit(
        "subscriptionList_data",
        {"subscriptions": subscriptions},
        to=sid
    )

    logging.info(f"✅ Sent subscription list to user {user_id}: {subscriptions}")

# ================= SCRAPER =================

@sio.on("start_combined")
def start_combined(sid, data):
    if sid not in authenticated_clients:
        sio.emit("status", {"error": "Not authenticated"}, to=sid)
        return

    if get_is_running():
        sio.emit("status", {"error": "Scraper already running"}, to=sid)
        return

    sio.emit("status", {"status": "Starting scraper..."}, to=sid)

    global watcher_started
    if not watcher_started:
        import threading
        threading.Thread(target=thread_runner, daemon=True).start()
        watcher_started = True

def thread_runner():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            run_scraper(
                sio,
                connected_clients,
                authenticated_clients
            )
        )
    finally:
        loop.close()

# # combine_socket.py
# import asyncio
# import threading
# import logging
# from socket_instance import sio
# from Services.connection_service import handle_connect, connected_clients
# from Services.auth_service import authenticate_user,authenticated_clients
# from Services.scraper_service import run_scraper
# from Services.scraper_service import get_is_running
# watcher_started = False
# user_subscriptions = {}

# @sio.event
# def connect(sid, environ):
#     handle_connect(sio, sid)
#     logging.info(f"🔌 Connected: {sid}")


# @sio.event
# def disconnect(sid):
#     authenticated_clients.pop(sid, None)
#     connected_clients.discard(sid)

#     user_subscriptions.pop(sid, None)

#     logging.info(f"❌ Disconnected: {sid}")

# @sio.on("authenticate")
# def authenticate(sid, data):
#     authenticate_user(sio, sid, data, authenticated_clients)

# @sio.on("subscribe_selected")
# def subscribe_selected(sid, data):
#     user = authenticated_clients.get(sid)
#     if not user:
#         logging.warning("⚠ subscribe_selected without auth")
#         return

#     user_id = user["user_id"]

#     if not isinstance(data, list):
#         logging.error(f"❌ Invalid subscription data: {data}")
#         return

#     url_ids = set()

#     for item in data:
#         # ✅ CASE 1: frontend sent string
#         if isinstance(item, str):
#             url_id = item

#         # ✅ CASE 2: frontend sent dict
#         elif isinstance(item, dict):
#             url_id = item.get("url_id")

#         else:
#             continue

#         if not url_id:
#             continue

#         url_id = str(url_id)
#         sio.enter_room(sid, f"url:{url_id}")
#         url_ids.add(url_id)

#     user_subscriptions[sid] = {
#         "user_id": user_id,
#         "url_ids": url_ids
#     }

#     logging.info(f"✅ User {user_id} subscribed to URLs: {url_ids}")

# @sio.on("start_combined")
# def start_combined(sid, data):
#     if sid not in authenticated_clients:
#         sio.emit("status", {"error": "Not authenticated"}, to=sid)
#         return

#     if get_is_running():
#         sio.emit("status", {"error": "Scraper already running"}, to=sid)
#         return
    
#     sio.emit("status", {"status": "Starting scraper..."}, to=sid)
#     global watcher_started
#     if not watcher_started:
#         import threading
#         threading.Thread(target=thread_runner, daemon=True).start()
#         watcher_started = True

# def thread_runner():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     try:
#         loop.run_until_complete(
#             run_scraper(
#                 sio,
#                 connected_clients,
#                 authenticated_clients
#             )
#         )
#     finally:
#         loop.close()
