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
    user.is_active = data.get("is_active", user.is_active)

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




