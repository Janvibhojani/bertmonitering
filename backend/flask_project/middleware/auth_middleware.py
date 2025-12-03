# middleware/auth_middleware.py
from flask import request, jsonify, g
from functools import wraps
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASH_ALGORITHM])
            g.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, "user", None)

        if not user or user.get("role") != "admin":
            return jsonify({"message": "Admin access only"}), 403

        return f(*args, **kwargs)
    return decorated

