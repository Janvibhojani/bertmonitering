from flask import Flask
from app.db.mongo import init_db
from app.routes.user_routes import user_bp
from app.middleware.auth_middleware import register_middleware
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecretkey")
    
    # Initialize DB
    init_db(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register routes
    app.register_blueprint(user_bp, url_prefix="/api/users")
    
    return app
