# routes/admin_routes.py
from controllers.admin_controller import admin_bp
from controllers.auth_controller import auth_bp

admin_routes = admin_bp
auth_routes = auth_bp
