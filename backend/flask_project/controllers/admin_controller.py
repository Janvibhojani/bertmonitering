# controllers/admin_controller.py
from db.mongo import users_collection
from middleware.auth_middleware import token_required, admin_required
from models import User
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/", methods=["GET"])
@token_required
@admin_required
def get_all_users():
    users = []
    for user_data in users_collection.find():
        user = User.from_dict(user_data)
        user_dict = user.to_dict()

        # ✅ Convert ObjectId to string
        if "_id" in user_data:
            user_dict["_id"] = str(user_data["_id"])

        # ✅ Convert datetime fields to ISO strings
        if isinstance(user_dict.get("created_at"), datetime):
            user_dict["created_at"] = user_dict["created_at"].isoformat()
        if isinstance(user_dict.get("updated_at"), datetime):
            user_dict["updated_at"] = user_dict["updated_at"].isoformat()


        users.append(user_dict)

    return jsonify(users), 200


@admin_bp.route("/<user_id>", methods=["GET"])
@token_required
@admin_required
def get_user(user_id):
    try:
       
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return jsonify({"message": "Invalid user ID"}), 400

    if not user_data:
        return jsonify({"message": "User not found"}), 404

    
    user_data["_id"] = str(user_data["_id"])

    
    for field in ["created_at", "updated_at"]:
        if field in user_data and hasattr(user_data[field], "isoformat"):
            user_data[field] = user_data[field].isoformat()

    return jsonify(user_data), 200

@admin_bp.route("/<user_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_user(user_id):
    try:
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
    except:
        return jsonify({"message": "Invalid user ID"}), 400

    if result.deleted_count == 0:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"message": "User deleted successfully"}), 200

@admin_bp.route("/", methods=["POST"])
@token_required
@admin_required
def create_user():
    data = request.get_json()

    if "password" in data:
        data["password"] = generate_password_hash(data["password"])

    user = User.from_dict(data)
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    
    user.urls = data.get("urls", [])
    user.start_date = data.get("start_date")
    user.end_date = data.get("end_date")

    user_dict = user.to_dict()
    user_dict.pop("_id", None)

    inserted = users_collection.insert_one(user_dict)

    user._id = inserted.inserted_id

    response_user = user.to_dict()
    response_user["_id"] = str(inserted.inserted_id)  # <-- FIX HERE


    return jsonify({
        "message": "User created successfully",
        "user": response_user
    }), 201


@admin_bp.route("/<user_id>", methods=["PUT"])
@token_required
@admin_required
def update_user(user_id):
    data = request.get_json()
    try:
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return jsonify({"message": "Invalid user ID"}), 400

    if not user_data:
        return jsonify({"message": "User not found"}), 404

    user = User.from_dict(user_data)
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    user.urls = data.get("urls", user.urls)
    user.start_date = data.get("start_date", user.start_date)
    user.end_date = data.get("end_date", user.end_date)

    # if "password" in data:
    #     user.password = generate_password_hash(data["password"])

    user.updated_at = datetime.utcnow()

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.to_dict()}
    )

    user_dict = user.to_dict()

    if "_id" in user_dict and isinstance(user_dict["_id"], ObjectId):
        user_dict["_id"] = str(user_dict["_id"])

    return jsonify({
        "message": "User updated successfully",
        "user": user_dict
    }), 200





# ====================enrypted version ========================

# from db.mongo import users_collection
# from middleware.auth_middleware import token_required
# from models import User
# from flask import Blueprint, jsonify, request
# from bson.objectid import ObjectId
# from datetime import datetime
# from werkzeug.security import generate_password_hash
# from base64 import b64decode
# from Crypto.Cipher import AES
# from Crypto.Protocol.KDF import PBKDF2
# from Crypto.Hash import SHA256  # ✅ same as in auth.py
# import os

# admin_bp = Blueprint("admin", __name__)

# AES_SECRET_KEY = os.getenv("AES_SECRET_KEY", "my-demo-key-123456").encode()


# # -------------------------------------------------------
# # 🔹 AES-GCM Decryption Helper
# # -------------------------------------------------------
# def decrypt_password(data):
#     """Decrypt AES-GCM encrypted password from frontend WebCrypto."""
#     try:
#         if not isinstance(data, dict):
#             return data  # already plaintext (for local testing)

#         cipher_b64 = data.get("cipher")
#         iv_b64 = data.get("iv")
#         salt_b64 = data.get("salt")

#         if not cipher_b64 or not iv_b64 or not salt_b64:
#             return None

#         cipher_bytes = b64decode(cipher_b64)
#         iv = b64decode(iv_b64)
#         salt = b64decode(salt_b64)

#         # ✅ Derive AES key same as frontend
#         key = PBKDF2(AES_SECRET_KEY, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)

#         # Split ciphertext + 16-byte GCM tag
#         ciphertext, tag = cipher_bytes[:-16], cipher_bytes[-16:]

#         cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
#         decrypted = cipher.decrypt_and_verify(ciphertext, tag)
#         return decrypted.decode("utf-8")

#     except Exception as e:
#         print("❌ Password decryption failed:", e)
#         return None


# # -------------------------------------------------------
# # 🔹 GET ALL USERS
# # -------------------------------------------------------
# @admin_bp.route("/", methods=["GET"])
# @token_required
# def get_all_users():
#     users = []
#     for user_data in users_collection.find():
#         user = User.from_dict(user_data)
#         user_dict = user.to_dict()

#         if "_id" in user_data:
#             user_dict["_id"] = str(user_data["_id"])

#         # Convert datetime fields
#         for field in ["created_at", "updated_at"]:
#             if field in user_dict and isinstance(user_dict[field], datetime):
#                 user_dict[field] = user_dict[field].isoformat()

#         users.append(user_dict)

#     return jsonify(users), 200


# # -------------------------------------------------------
# # 🔹 GET SINGLE USER
# # -------------------------------------------------------
# @admin_bp.route("/<user_id>", methods=["GET"])
# @token_required
# def get_user(user_id):
#     try:
#         user_data = users_collection.find_one({"_id": ObjectId(user_id)})
#     except:
#         return jsonify({"message": "Invalid user ID"}), 400

#     if not user_data:
#         return jsonify({"message": "User not found"}), 404

#     user_data["_id"] = str(user_data["_id"])
#     for field in ["created_at", "updated_at"]:
#         if field in user_data and hasattr(user_data[field], "isoformat"):
#             user_data[field] = user_data[field].isoformat()

#     return jsonify(user_data), 200


# # -------------------------------------------------------
# # 🔹 DELETE USER
# # -------------------------------------------------------
# @admin_bp.route("/<user_id>", methods=["DELETE"])
# @token_required
# def delete_user(user_id):
#     try:
#         result = users_collection.delete_one({"_id": ObjectId(user_id)})
#     except:
#         return jsonify({"message": "Invalid user ID"}), 400

#     if result.deleted_count == 0:
#         return jsonify({"message": "User not found"}), 404

#     return jsonify({"message": "User deleted successfully"}), 200
# @admin_bp.route("/", methods=["POST"])
# @token_required
# def create_user():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"message": "Missing JSON body"}), 400

#         # frontend sends password as { cipher, iv, salt }
#         password_data = data.get("password")
#         decrypted_pass = decrypt_password(password_data)
#         if decrypted_pass is None:
#             return jsonify({"message": "Password decryption failed"}), 400

#         # Build user object but DO NOT hash password. Store encrypted fields instead.
#         user = User.from_dict(data)
#         # remove `password` plaintext field if present in model
#         # store encrypted blob fields
#         user.cipher = password_data.get("cipher")
#         user.iv = password_data.get("iv")
#         user.salt = password_data.get("salt")

#         user.created_at = datetime.utcnow()
#         user.updated_at = datetime.utcnow()
#         user.urls = data.get("urls", [])
#         user.start_date = data.get("start_date")
#         user.end_date = data.get("end_date")

#         user_dict = user.to_dict()
#         # remove any plaintext password key if present
#         user_dict.pop("password", None)
#         # ensure encrypted fields present in dict
#         user_dict["cipher"] = user.cipher
#         user_dict["iv"] = user.iv
#         user_dict["salt"] = user.salt

#         user_dict.pop("_id", None)
#         inserted = users_collection.insert_one(user_dict)
#         user._id = inserted.inserted_id

#         response_user = user.to_dict()
#         response_user["_id"] = str(inserted.inserted_id)

#         return jsonify({
#             "message": "User created successfully",
#             "user": response_user
#         }), 201

#     except Exception as e:
#         print("❌ Error in create_user:", e)
#         return jsonify({"message": "Internal server error"}), 500


# # -------------------------------------------------------
# # 🔹 UPDATE USER - update encrypted fields if provided
# # -------------------------------------------------------
# @admin_bp.route("/<user_id>", methods=["PUT"])
# @token_required
# def update_user(user_id):
#     try:
#         data = request.get_json()
#         user_data = users_collection.find_one({"_id": ObjectId(user_id)})
#     except Exception:
#         return jsonify({"message": "Invalid user ID"}), 400

#     if not user_data:
#         return jsonify({"message": "User not found"}), 404

#     user = User.from_dict(user_data)
#     user.username = data.get("username", user.username)
#     user.email = data.get("email", user.email)
#     user.urls = data.get("urls", user.urls)
#     user.start_date = data.get("start_date", user.start_date)
#     user.end_date = data.get("end_date", user.end_date)
#     user.is_active = data.get("is_active", user.is_active)

#     password_data = data.get("password")
#     if password_data:
#         # decrypt to verify payload is valid (optional)
#         decrypted_pass = decrypt_password(password_data)
#         if decrypted_pass is None:
#             return jsonify({"message": "Password decryption failed"}), 400
#         # store encrypted fields (do not hash)
#         user.cipher = password_data.get("cipher")
#         user.iv = password_data.get("iv")
#         user.salt = password_data.get("salt")

#     user.updated_at = datetime.utcnow()

#     # prepare dict for update
#     updated_dict = user.to_dict()
#     # remove plaintext password key if present
#     updated_dict.pop("password", None)
#     # set encrypted fields explicitly
#     if password_data:
#         updated_dict["cipher"] = user.cipher
#         updated_dict["iv"] = user.iv
#         updated_dict["salt"] = user.salt

#     users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": updated_dict})

#     # convert _id for response
#     if "_id" in updated_dict and isinstance(updated_dict["_id"], ObjectId):
#         updated_dict["_id"] = str(updated_dict["_id"])

#     return jsonify({
#         "message": "User updated successfully",
#         "user": updated_dict
#     }), 200