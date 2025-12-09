# run.py
import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import socketio
from socket_instance import sio  # Import the shared Socket.IO instance
from sockets.combine_socket import *  # Import socket event 
from Services.scraper_service import run_scraper, stop_scraper
from Services.json_manager import ensure_json_file, add_domain_if_missing
from Services.url_Service import fetch_all_urls_from_db

# Controller blueprints
from controllers.admin_controller import admin_bp
from controllers.auth_controller import auth_bp
from controllers.urls_controller import urls_bp
from controllers.scrape_api import scrape_api_bp
from controllers.user_controller import user_bp


load_dotenv()

# Create Flask app
flask_app = Flask(__name__)
CORS(flask_app, resources={r"/*": {"origins": "*"}},supports_credentials=True)
flask_app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")

# Register Flask blueprints (REST APIs)
flask_app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
flask_app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
flask_app.register_blueprint(urls_bp, url_prefix="/api/v1/urls")
flask_app.register_blueprint(scrape_api_bp, url_prefix="/api/v1/scrape")
flask_app.register_blueprint(user_bp, url_prefix="/api/v1/user")


app = socketio.WSGIApp(sio, flask_app)


def start_scraper_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_scraper(sio, connected_clients, authenticated_clients))
    
# Start Eventlet server
if __name__ == "__main__":
    ensure_json_file()
    
    urls = fetch_all_urls_from_db()
    for u in urls:
        add_domain_if_missing(u)
      # Start scraper thread
    t = threading.Thread(target=start_scraper_background)
    t.daemon = True
    t.start()

    
    import werkzeug.serving
    werkzeug.serving.run_simple("0.0.0.0", 5000, app, threaded=True)
    
   
# ====================newly socket start====================
       
# import os
# import asyncio
# import threading
# from flask import Flask
# from flask_cors import CORS
# from dotenv import load_dotenv
# import socketio
# from socket_instance import sio
# from sockets.combine_socket import *
# from utils.globel import init_browser, close_browser
# import signal

# # Controller blueprints
# from controllers.admin_controller import admin_bp
# from controllers.auth_controller import auth_bp
# from controllers.urls_controller import urls_bp
# from controllers.scrape_api import scrape_api_bp
# from controllers.user_controller import user_bp

# load_dotenv()

# flask_app = Flask(__name__)
# CORS(flask_app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
# flask_app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")

# flask_app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
# flask_app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
# flask_app.register_blueprint(urls_bp, url_prefix="/api/v1/urls")
# flask_app.register_blueprint(scrape_api_bp, url_prefix="/api/v1/scrape")
# flask_app.register_blueprint(user_bp, url_prefix="/api/v1/user")

# app = socketio.WSGIApp(sio, flask_app)

# shutdown_flag = False


# # -----------------------------
# # Start Playwright Browser Once
# # -----------------------------
# async def startup_browser():
#     print("✅ Starting global browser...")
#     await init_browser()
#     print("🟢 Browser started successfully")


# # -----------------------------
# # Shutdown browser cleanly
# # -----------------------------
# def handle_exit(signum, frame):
#     global shutdown_flag
#     if shutdown_flag:
#         return
#     shutdown_flag = True

#     print("\n⚠ CTRL+C received — shutting down cleanly...")

#     def closer():
#         asyncio.run(close_browser())
#         print("🟢 Browser closed. Exiting...")

#     threading.Thread(target=closer).start()

#     raise KeyboardInterrupt

# async def test_page():
#     browser = await init_browser()
#     context = await browser.new_context()
#     page = await context.new_page()
#     await page.goto("https://google.com")
    
# signal.signal(signal.SIGINT, handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)


# # -----------------------------
# # MAIN
# # -----------------------------
# if __name__ == "__main__":
#     print("🚀 Flask + Socket.IO server running on http://0.0.0.0:5000")

#     # Start browser before Flask
#     # asyncio.run(startup_browser())
#     threading.Thread(target=lambda: asyncio.run(startup_browser()), daemon=True).start()

#     import werkzeug.serving
#     werkzeug.serving.run_simple("0.0.0.0", 5000, app, threaded=True)