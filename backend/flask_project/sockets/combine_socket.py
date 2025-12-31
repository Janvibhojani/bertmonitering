
# combine_socket.py
import asyncio
import threading
import logging
from socket_instance import sio
from Services.connection_service import handle_connect, connected_clients
from Services.auth_service import authenticate_user,authenticated_clients
from Services.scraper_service import run_scraper
from Services.scraper_service import get_is_running
watcher_started = False
user_subscriptions = {}

@sio.event
def connect(sid, environ):
    handle_connect(sio, sid)
    logging.info(f"🔌 Connected: {sid}")


@sio.event
def disconnect(sid):
    authenticated_clients.pop(sid, None)
    connected_clients.discard(sid)
    logging.info(f"❌ Disconnected: {sid}")


@sio.on("authenticate")
def authenticate(sid, data):
    authenticate_user(sio, sid, data, authenticated_clients)

@sio.on("subscribe_selected")
def subscribe_selected(sid, data):
    user_id = authenticated_clients[sid]["user_id"]
    user_room = f"user:{user_id}"
    user_subscriptions[user_room] = data


@sio.on("start_combined")
def start_combined(sid, data):
    if sid not in authenticated_clients:
        sio.emit("status", {"error": "Not authenticated"}, to=sid)
        return

    if get_is_running():
        sio.emit("status", {"error": "Scraper already running"}, to=sid)
        return
    else:
        sio.emit("status", {"status": "Starting scraper..."}, to=sid)


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
