
# main.py - updated version
import os
import threading
import asyncio
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import socketio
from socket_instance import sio
from sockets.combine_socket import *
from Services.scraper_service import run_scraper
from Services.json_manager import ensure_json_file, add_domain
from Services.url_Service import fetch_all_urls_from_db

# Controller blueprints
from controllers.admin_controller import admin_bp
from controllers.auth_controller import auth_bp
from controllers.urls_controller import urls_bp
from controllers.scrape_api import scrape_api_bp
from controllers.user_controller import user_bp

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Flask app
flask_app = Flask(__name__)
CORS(flask_app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
flask_app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")

# Register Flask blueprints (REST APIs)
flask_app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
flask_app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
flask_app.register_blueprint(urls_bp, url_prefix="/api/v1/urls")
flask_app.register_blueprint(scrape_api_bp, url_prefix="/api/v1/scrape")
flask_app.register_blueprint(user_bp, url_prefix="/api/v1/user")

app = socketio.WSGIApp(sio, flask_app)

def start_scraper_background():
    try:
        # Create new event loop for the scraper thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logging.info("🔄 Starting scraper in background thread...")
        
        # Run the scraper
        loop.run_until_complete(run_scraper(sio, connected_clients, authenticated_clients))
        
        logging.info("🔄 Scraper background thread finished")
    except Exception as e:
        logging.error(f"❌ Error in scraper thread: {e}")
        import traceback
        traceback.print_exc()

# Start Eventlet server
if __name__ == "__main__":
    ensure_json_file()
    print("\n🔍 CHECKING JSON INTEGRITY...")
    
    # Load initial URLs into scraper
    urls = fetch_all_urls_from_db()
    
    for u in urls:
        add_domain(u)
        

    # Start scraper thread
    print("🚀 Launching scraper thread...")
    t = threading.Thread(target=start_scraper_background, name="ScraperThread")
    t.daemon = True
    t.start()
    print("⏳ Waiting 2 seconds for scraper to initialize...")
    import time
    time.sleep(2)
    
    # Verify scraper started
    from Services.scraper_service import get_is_running
    if get_is_running():
        print("✅ Scraper started successfully!")
    else:
        print("⚠ Scraper may not have started correctly")
    
    print("🌐 Starting Flask-SocketIO server on http://0.0.0.0:5000")
    import werkzeug.serving
    werkzeug.serving.run_simple("0.0.0.0", 5000, app, threaded=True)