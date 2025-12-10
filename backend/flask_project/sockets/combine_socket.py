
# import asyncio
# import logging
# import threading
# import jwt
# import os
# from utils.sraping_playwright import scrape_combined
# from controllers.urls_controller import fetch_all_urls_from_db
# from utils.globel import init_browser, close_browser
# from socket_instance import sio
# from dotenv import load_dotenv

# load_dotenv()
# logging.basicConfig(level=logging.INFO)

# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
# HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")

# connected_clients = set()
# authenticated_clients = {}
# browser = None
# stop_event = None
# scraper_task = None
# scraper_lock = threading.Lock()  # ✅ Prevent multiple parallel scrapers


# # ----------------------------------------------------
# # ✅ Client connects
# # ----------------------------------------------------
# @sio.event
# def connect(sid, environ):
#     connected_clients.add(sid)
#     logging.info(f"Client connected: {sid}")
#     sio.emit("status", {
#         "status": "connected",
#         "message": "Connected. Please authenticate."
#     }, to=sid)


# # ----------------------------------------------------
# # ✅ Token authentication
# # ----------------------------------------------------
# @sio.on("authenticate")
# def authenticate(sid, data):
#     token = data.get("token")
#     if not token:
#         sio.emit("status", {"error": "Token missing!"}, to=sid)
#         return

#     try:
#         payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASH_ALGORITHM])
#         user_id = payload.get("user_id") or payload.get("id")
#         if not user_id:
#             raise jwt.InvalidTokenError("user_id missing")

#         authenticated_clients[sid] = user_id
#         # logging.info(f"✅ {sid} authenticated as {user_id}")
#         sio.emit("status", {
#             "status": "authenticated",
#             "message": f"Authenticated as user {user_id}"
#         }, to=sid)

#     except jwt.ExpiredSignatureError:
#         sio.emit("status", {"error": "Token expired!"}, to=sid)
#     except jwt.InvalidTokenError as e:
#         sio.emit("status", {"error": f"Invalid token: {str(e)}"}, to=sid)
# from utils.globel import close_browser  # ✅ add this import at top
# # disconnect event
# @sio.event
# def disconnect(sid):
#     global browser, scraper_task, stop_event

#     logging.info(f"Client disconnected: {sid}")
#     connected_clients.discard(sid)
#     authenticated_clients.pop(sid, None)

#     # 🧠 If no clients left, stop everything cleanly
#     if not connected_clients:
#         logging.info("No clients left — stopping scraper and closing browser...")

#         # ✅ Stop ongoing scraper
#         if stop_event and not stop_event.is_set():
#             stop_event.set()

#         if scraper_task:
#             try:
#                 scraper_task.cancel()
#             except Exception as e:
#                 logging.warning(f"Error cancelling scraper: {e}")
#             scraper_task = None

#         # ✅ Safely close Playwright (both browser + playwright instance)
#         try:
#             asyncio.run(close_browser())
#         except Exception as e:
#             logging.warning(f"Error closing browser: {e}")
#         finally:
#             browser = None
#             stop_event = None
#             logging.info("✅ All resources released & browser fully reset.")


# # ----------------------------------------------------
# # ✅ Start Scraper (only once)
# # ----------------------------------------------------
# @sio.on("start_combined")
# def start_combined(sid, data):
#     global scraper_task, stop_event, browser

#     # 🔒 Ensure only one scraper starts at a time
#     with scraper_lock:
#         if scraper_task and not scraper_task.done():
#             sio.emit("status", {
#                 "status": "running",
#                 "message": "Scraper already running"
#             }, to=sid)
#             return

#         def thread_runner():
#             asyncio.run(run_scraper(sid))

#         threading.Thread(target=thread_runner, daemon=True).start()

# from utils.globel import init_browser, close_browser  # ✅ make sure this import is at top

# async def run_scraper(sid):
#     """Async scraper runner in a separate thread"""
#     global scraper_task, stop_event, browser

#     try:
#         targets = fetch_all_urls_from_db()
#         if not targets:
#             sio.emit("data", {"error": "No targets found"}, to=sid)
#             return

#         # ✅ Always start fresh browser session
#         browser = await init_browser()
#         stop_event = asyncio.Event()

#         sio.emit("status", {
#             "status": "scraping_started",
#             "message": "Scraper loop started",
#             "total_targets": len(targets)
#         })

#         async def send_func(payload):
#             dead = []
#             for client_sid in connected_clients:
#                 try:
#                     sio.emit("data", payload, to=client_sid)
#                 except Exception as e:
#                     logging.warning(f"Emit failed for {client_sid}: {e}")
#                     dead.append(client_sid)
#             for d in dead:
#                 connected_clients.discard(d)
#                 authenticated_clients.pop(d, None)

#         async def scraper_loop():
#             global browser
#             try:
#                 await scrape_combined(browser, targets, stop_event, send_func)
#             except asyncio.CancelledError:
#                 logging.info("Scraper cancelled")
#             except Exception as e:
#                 logging.exception(f"Scraper crashed: {e}")
#                 sio.emit("data", {"error": str(e)})
#             finally:
#                 stop_event.set()

#                 # ✅ Proper close: close browser + stop Playwright + reset loop
#                 try:
#                     await close_browser()
#                 except Exception as e:
#                     logging.warning(f"Error closing browser: {e}")

#                 browser = None
#                 sio.emit("status", {"status": "scraping_stopped"})

#         scraper_task = asyncio.create_task(scraper_loop())
#         await scraper_task

#     except Exception as e:
#         logging.exception("Error in run_scraper")
#         sio.emit("data", {"error": str(e)}, to=sid)


# ===================with userside socket==========================
# import asyncio
# import logging
# import threading
# import jwt
# import os
# from utils.sraping_playwright import scrape_combined
# from controllers.urls_controller import fetch_all_urls_from_db
# from utils.globel import init_browser, close_browser
# from socket_instance import sio
# from dotenv import load_dotenv
# from controllers.user_controller import fetch_allocated_urls_by_user_id

# load_dotenv()
# logging.basicConfig(level=logging.INFO)

# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
# HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")

# connected_clients = set()
# authenticated_clients = {}
# browser = None
# stop_event = None
# scraper_task = None
# scraper_lock = threading.Lock()  # ✅ Prevent multiple parallel scrapers


# # ----------------------------------------------------
# # ✅ Client connects
# # ----------------------------------------------------
# @sio.event
# def connect(sid, environ):
#     connected_clients.add(sid)
#     logging.info(f"Client connected: {sid}")
#     sio.emit("status", {
#         "status": "connected",
#         "message": "Connected. Please authenticate."
#     }, to=sid)


# # ----------------------------------------------------
# # ✅ Token authentication
# # ----------------------------------------------------
# @sio.on("authenticate")
# def authenticate(sid, data):
#     token = data.get("token")
#     if not token:
#         sio.emit("status", {"error": "Token missing!"}, to=sid)
#         return

#     try:
#         payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASH_ALGORITHM])
#         user_id = payload.get("user_id") or payload.get("id")
#         role = payload.get("role", "user")
#         if not user_id:
#             raise jwt.InvalidTokenError("user_id missing")

#         authenticated_clients[sid] = {
#             "user_id": user_id,
#             "role": role
#         }
#         sio.emit("status", {
#             "status": "authenticated",
#             "message": f"Authenticated as user {user_id}"
#         }, to=sid)

#     except jwt.ExpiredSignatureError:
#         sio.emit("status", {"error": "Token expired!"}, to=sid)
#     except jwt.InvalidTokenError as e:
#         sio.emit("status", {"error": f"Invalid token: {str(e)}"}, to=sid)


# # ----------------------------------------------------
# # disconnect event (loop-safe close_browser)
# # ----------------------------------------------------
# @sio.event
# def disconnect(sid):
#     global browser, scraper_task, stop_event

#     logging.info(f"Client disconnected: {sid}")
#     connected_clients.discard(sid)
#     authenticated_clients.pop(sid, None)

#     # If no clients left, stop everything cleanly
#     if not connected_clients:
#         logging.info("No clients left — stopping scraper and closing browser...")

#         # Stop ongoing scraper
#         if stop_event and not stop_event.is_set():
#             stop_event.set()

#         if scraper_task:
#             try:
#                 scraper_task.cancel()
#             except Exception as e:
#                 logging.warning(f"Error cancelling scraper: {e}")
#             scraper_task = None

#         # Safely close Playwright (both browser + playwright instance)
#         try:
#             loop = None
#             try:
#                 loop = asyncio.get_event_loop()
#             except RuntimeError:
#                 loop = None

#             if loop and loop.is_running():
#                 # schedule async close in current loop
#                 loop.create_task(close_browser())
#             else:
#                 # safe synchronous run if no event loop running
#                 asyncio.run(close_browser())
#         except Exception as e:
#             logging.warning(f"Error closing browser: {e}")
#         finally:
#             browser = None
#             stop_event = None
#             logging.info("✅ All resources released & browser fully reset.")


# # ----------------------------------------------------
# # ✅ Start Scraper (only once) - requires authentication
# # ----------------------------------------------------
# @sio.on("start_combined")
# def start_combined(sid, data):
#     global scraper_task, stop_event, browser
    
#     # Require authenticated user
#     client = authenticated_clients.get(sid)
#     if not client:
#         sio.emit("status", {"error": "Unauthorized. Please authenticate first."}, to=sid)
#         return

#     # Ensure only one scraper starts at a time
#     with scraper_lock:
#         if scraper_task and not scraper_task.done():
#             sio.emit("status", {
#                 "status": "running",
#                 "message": "Scraper already running"
#             }, to=sid)
#             return

#         # If any previous stop_event exists, mark it so we start fresh
#         if stop_event and not getattr(stop_event, "is_set", lambda: False)():
#             try:
#                 stop_event.set()
#             except Exception:
#                 # If stop_event is not an asyncio.Event, ignore
#                 pass

#         def thread_runner():
#             asyncio.run(run_scraper(sid))

#         threading.Thread(target=thread_runner, daemon=True).start()

# async def run_scraper(sid):
#     """Async scraper runner in a separate thread"""
#     global scraper_task, stop_event, browser

#     try:
#         client = authenticated_clients.get(sid)
#         if not client:
#             sio.emit("status", {"error": "Unauthorized"}, to=sid)
#             return

#         user_id = client["user_id"]
#         role = client["role"]

#         # ✅ Fetch targets based on role
#         if role == "admin":
#             targets = fetch_all_urls_from_db()
#         else:
#             targets = fetch_allocated_urls_by_user_id(user_id)

#         if not targets:
#             sio.emit("data", {"error": "No targets found"}, to=sid)
#             return

#         # ✅ Normalize targets (fix string-index crash)
#         normalized_targets = []
#         for t in targets:
#             if isinstance(t, dict):
#                 normalized_targets.append(t)
#             elif isinstance(t, str):
#                 normalized_targets.append({
#                     "url": t,
#                     "_id": t
#                 })
#             else:
#                 logging.warning(f"[SCRAPER] Invalid target format: {t}")

#         targets = normalized_targets

#         # ✅ Start browser
#         browser = await init_browser()
#         stop_event = asyncio.Event()

#         sio.emit("status", {
#             "status": "scraping_started",
#             "message": "Scraper loop started",
#             "total_targets": len(targets)
#         }, to=sid)

#         # ✅ Cache for per-user allocated URLs
#         user_url_cache = {}

#         async def send_func(payload):
#             dead = []
#             for client_sid in list(connected_clients):
#                 try:
#                     client = authenticated_clients.get(client_sid)
#                     if not client:
#                         continue

#                     c_user_id = client.get("user_id")
#                     c_role = client.get("role")

#                     # ✅ Admins get all data
#                     if c_role == "admin":
#                         sio.emit("data", payload, to=client_sid)
#                         continue

#                     # ✅ Cached allocated URLs
#                     if c_user_id not in user_url_cache:
#                         allocated_urls = fetch_allocated_urls_by_user_id(c_user_id) or []

#                         # ✅ Safe ID extraction
#                         allocated_ids = {
#                             str(x.get("_id"))
#                             for x in allocated_urls
#                             if isinstance(x, dict)
#                         }

#                         user_url_cache[c_user_id] = allocated_ids
#                     else:
#                         allocated_ids = user_url_cache[c_user_id]

#                     # ✅ payload URL id safe handling
#                     payload_url_id = str(
#                         payload.get("url_id") or payload.get("_id") or ""
#                     )

#                     if payload_url_id in allocated_ids:
#                         sio.emit("data", payload, to=client_sid)

#                 except Exception as e:
#                     logging.warning(f"Emit failed for {client_sid}: {e}")
#                     dead.append(client_sid)

#             # ✅ Cleanup dead sockets
#             for d in dead:
#                 connected_clients.discard(d)
#                 authenticated_clients.pop(d, None)

#         # ✅ Main scraper loop
#         async def scraper_loop():
#             global browser
#             try:
#                 await scrape_combined(browser, targets, stop_event, send_func)
#             except asyncio.CancelledError:
#                 logging.info("Scraper cancelled")
#             except Exception as e:
#                 logging.exception(f"Scraper crashed: {e}")
#                 sio.emit("data", {"error": str(e)})
#             finally:
#                 try:
#                     stop_event.set()
#                 except:
#                     pass

#                 # ✅ Close browser safely
#                 try:
#                     await close_browser()
#                 except Exception as e:
#                     logging.warning(f"Error closing browser: {e}")

#                 browser = None
#                 sio.emit("status", {"status": "scraping_stopped"})

#         # ✅ Start the task
#         scraper_task = asyncio.create_task(scraper_loop())
#         await scraper_task

#     except Exception as e:
#         logging.exception("Error in run_scraper")
#         sio.emit("data", {"error": str(e)}, to=sid)

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
from Services.scraper_service import run_scraper, stop_scraper
from utils.globel import close_browser

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
    # no_clients_left = handle_disconnect(sid, authenticated_clients)
    

    # if no_clients_left:
    #     logging.info("No clients left — stopping scraper & closing browser")

    #     stop_scraper()

    #     try:
    #         asyncio.run(close_browser())
    #     except Exception as e:
    #         logging.warning(f"Browser close failed: {e}")

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

    threading.Thread(target=thread_runner, daemon=True).start()

    sio.emit("status", {
        "status": "started",
        "message": "Global scraper started (ONE browser)"
    }, to=sid)
# -------------------------
# Send payload to connected clients
# -------------------------
async def send_to_clients(payload):
    from Services.connection_service import connected_clients  # import global dict

    for sid in connected_clients:
        await sio.emit("combined_scrape", payload, to=sid)

# @sio.on("start_combined")
# def start_combined(sid, data):
#     user = authenticated_clients.get(sid)
    
#     if not user:
#         sio.emit("status", {"error": "User not authenticated"}, to=sid)
#         return

#     def thread_runner():
#             asyncio.run(
#                 run_scraper(
#                     sio,
#                     sid,
#                     connected_clients,
#                     authenticated_clients
#                 )
#             )

#     threading.Thread(target=thread_runner, daemon=True).start()

#     sio.emit("status", {
#         "status": "started",
#         "message": f"Scraper started "
#     }, to=sid)







# temp
    # with scraper_lock:
    #     def thread_runner():
    #         asyncio.run(
    #             run_scraper(
    #                 sio,
    #                 sid,
    #                 connected_clients,
    #                 authenticated_clients
    #             )
    #         )

    #     threading.Thread(target=thread_runner, daemon=True).start()
