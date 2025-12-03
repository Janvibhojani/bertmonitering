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
    
    
# ============================Encrypted version===================================


# from flask import Blueprint, request, jsonify
# from werkzeug.security import check_password_hash, generate_password_hash
# from bson.objectid import ObjectId
# from db.mongo import users_collection
# import jwt
# import os
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# from base64 import b64decode
# from Crypto.Cipher import AES
# from Crypto.Protocol.KDF import PBKDF2
# from Crypto.Hash import SHA256  # ✅ from Code 1

# load_dotenv()

# auth_bp = Blueprint("auth", __name__)

# # 🔹 Environment setup
# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
# HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")
# JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 60))
# AES_SECRET_KEY = os.getenv("AES_SECRET_KEY", "my-demo-key-123456").encode()

# # ------------------------------------------------------------------
# # 🔹 AES-GCM Decryption (frontend → backend)
# # ------------------------------------------------------------------
# def decrypt_password(data):
#     """Decrypt AES-GCM encrypted password from WebCrypto frontend."""
#     try:
#         if not isinstance(data, dict):
#             return data  # already plaintext (for testing)

#         cipher_b64 = data.get("cipher")
#         iv_b64 = data.get("iv")
#         salt_b64 = data.get("salt")

#         if not cipher_b64 or not iv_b64 or not salt_b64:
#             return None

#         cipher_bytes = b64decode(cipher_b64)
#         iv = b64decode(iv_b64)
#         salt = b64decode(salt_b64)

#         # ✅ Derive AES key exactly as in frontend
#         key = PBKDF2(AES_SECRET_KEY, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)

#         # Split ciphertext + tag (last 16 bytes is GCM tag)
#         ciphertext, tag = cipher_bytes[:-16], cipher_bytes[-16:]

#         # ✅ AES-GCM decryption
#         cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
#         decrypted = cipher.decrypt_and_verify(ciphertext, tag)
#         return decrypted.decode("utf-8")

#     except Exception as e:
#         print("❌ Password decryption failed:", e)
#         return None
    
# # ------------------------------------------------------------------
# # 🔹 REGISTER - store encrypted fields instead of hashing
# # ------------------------------------------------------------------
# @auth_bp.route("/register", methods=["POST"])
# def register():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"message": "Missing JSON body"}), 400

#         username = data.get("username")
#         email = data.get("email")
#         password_data = data.get("password")

#         if not username or not email or not password_data:
#             return jsonify({"message": "All fields are required"}), 400

#         # decrypt to validate the payload (optional)
#         decrypted_password = decrypt_password(password_data)
#         if decrypted_password is None:
#             return jsonify({"message": "Password decryption failed"}), 400

#         # Prevent duplicates
#         if users_collection.find_one({"username": username}):
#             return jsonify({"message": "Username already exists"}), 400
#         if users_collection.find_one({"email": email}):
#             return jsonify({"message": "Email already exists"}), 400

#         # Store encrypted fields as-is (do NOT hash)
#         user = {
#             "username": username,
#             "email": email,
#             "role": "user",
#             "is_active": True,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow(),
#             "urls": [],
#             # store encrypted blob parts
#             "cipher": password_data.get("cipher"),
#             "iv": password_data.get("iv"),
#             "salt": password_data.get("salt"),
#         }

#         result = users_collection.insert_one(user)

#         return jsonify({
#             "message": "User registered successfully",
#             "user_id": str(result.inserted_id)
#         }), 201

#     except Exception as e:
#         print("Error in register:", e)
#         return jsonify({"message": "Internal server error"}), 500


# # ------------------------------------------------------------------
# # 🔹 LOGIN - decrypt incoming & stored encrypted password and compare plaintexts
# # ------------------------------------------------------------------
# @auth_bp.route("/login", methods=["POST"])
# def login():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"message": "Missing JSON body"}), 400

#         username = data.get("username")
#         password_data = data.get("password")
        

#         if not username or not password_data:
#             return jsonify({"message": "Username and password are required"}), 400

#         user_find = users_collection.find_one({"username": username})
#         if not user_find:
#             return jsonify({"message": "Invalid credentials"}), 401

#         # Decrypt incoming encrypted password from client
#         decrypted_password = decrypt_password(password_data)
       
#         if decrypted_password is None:
#             return jsonify({"message": "Password decryption failed"}), 400


#         # ✅ Generate JWT
#         payload = {
#             "user_id": str(user_find["_id"]),
#             "username": user_find["username"],
#             "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES),
#             "role": user_find["role"]
#         }

#         token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=HASH_ALGORITHM)
#         if isinstance(token, bytes):
#             token = token.decode("utf-8")

        
#         return jsonify({
#             "message": "Login successful",
#             "token": token,
#             "username": user_find["username"],
#             "role": user_find["role"],
#             "expires_in": JWT_EXPIRY_MINUTES * 60
#         }), 200
        

#     except Exception as e:
#         print("Error in login:", e)
#         return jsonify({"message": "Internal server error"}), 500

