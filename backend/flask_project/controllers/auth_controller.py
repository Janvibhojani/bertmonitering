# controllers/auth_controller.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
from db.mongo import users_collection
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint("auth", __name__)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 60))


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Missing JSON body"}), 400

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")  # Default role is 'user'

        if not username or not email or not password:
            return jsonify({"message": "All fields are required"}), 400

        # Check if username or email already exists
        if users_collection.find_one({"username": username}):
            return jsonify({"message": "Username already exists"}), 400
        if users_collection.find_one({"email": email}):
            return jsonify({"message": "Email already exists"}), 400

        hashed_password = generate_password_hash(password)

        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "urls": []  # Initialize with empty URL list
        }

        result = users_collection.insert_one(user)

        return jsonify({
            "message": "User registered successfully",
            "user_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print("Error in register:", e)
        return jsonify({"message": "Internal server error"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        print("Login route hit")
        data = request.get_json()
        print("Data received:", data)
        if not data:
            return jsonify({"message": "Missing JSON body"}), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        user_find = users_collection.find_one({"username": username})
        if not user_find or not check_password_hash(user_find["password"], password):
            return jsonify({"message": "Invalid credentials"}), 401

        payload = {
            "user_id": str(user_find["_id"]),
            "username": user_find["username"],
            "role": user_find["role"],
            "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=HASH_ALGORITHM)
        if isinstance(token, bytes):  # For older PyJWT versions
            token = token.decode("utf-8")

        return jsonify({
            "message": "Login successful",
            "user_id": str(user_find["_id"]),
            "username": user_find["username"],
            "role": user_find["role"],
            "token": token,
            "expires_in": JWT_EXPIRY_MINUTES * 60
        }), 200

    except Exception as e:
        print("Error in login:", e)
        return jsonify({"message": "Internal server error"}), 500
    
   