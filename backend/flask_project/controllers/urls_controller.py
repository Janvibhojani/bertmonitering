# controllers/urls_controller.py
from db.mongo import urls_collection
from middleware.auth_middleware import token_required
from models import User

from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime
from bson import ObjectId
from Services.json_manager import add_domain,update_domain,delete_domain,update_records

urls_bp = Blueprint("urls", __name__)  

@urls_bp.route("/", methods=["GET"])
@token_required
def get_all_urls():
    urls = []
    for url_data in urls_collection.find():
        url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
        urls.append(url_data)
    return jsonify(urls), 200
@urls_bp.route("/<url_id>", methods=["GET"])
@token_required
def get_url(url_id):
    try:
        url_data = urls_collection.find_one({"_id": ObjectId(url_id)})
    except:
        return jsonify({"message": "Invalid URL ID"}), 400

    if not url_data:
        return jsonify({"message": "URL not found"}), 404

    url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
    return jsonify(url_data), 200

@urls_bp.route("/<url_id>", methods=["DELETE"])
@token_required
def delete_url(url_id):
    from bson import ObjectId

    # Validate ObjectId
    try:
        object_id = ObjectId(url_id)
    except:
        return jsonify({"message": "Invalid URL ID"}), 400

    # Delete from MongoDB
    result = urls_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        return jsonify({"message": "URL not found"}), 404

    # Delete from JSON
    json_deleted = delete_domain(url_id)

    # Refresh JSON cached records if needed
    update_records()
    

    return jsonify({
        "message": "URL deleted successfully",
        "json_deleted": json_deleted
    }), 200


@urls_bp.route("/", methods=["POST"])
@token_required
def create_url():
    data = request.get_json() or {}

    new_domain = data.get("url")
    if not new_domain:
        return jsonify({"error": "URL is required"}), 400

    # ----------------------------------------
    # 1️⃣ Extract base domain
    # ----------------------------------------
    from urllib.parse import urlparse

    parsed = urlparse(new_domain)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    data["url"] = base_domain   
    # ----------------------------------------
    # 2️⃣ CHECK IF DOMAIN ALREADY EXISTS
    # ----------------------------------------
    existing = urls_collection.find_one({"url": base_domain})

    if existing:
        return jsonify({
            "status": "error",
            "message": "Url is  already exists",
            "existing_id": str(existing["_id"]),
            "existing_domain": existing["url"]
        }), 409

    # ----------------------------------------
    # 3️⃣ Insert new URL
    # ----------------------------------------
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()

    if data.get("target"):
        data["scrap_from"] = "HTML"
        data["only_on_change"] = False
        data["interval_ms"] = 0
    else:
        data["scrap_from"] = "API"
        data.pop("target", None)
        data.pop("mode", None)

    result = urls_collection.insert_one(data)
    data["_id"] = str(result.inserted_id)

    # ----------------------------------------
    # 4️⃣ Add to JSON
    # ----------------------------------------
    add_domain(data)
    return jsonify({
        "status": "success",
        "message": "New URL created successfully",
        "data": data
    }), 201

@urls_bp.route("/<url_id>", methods=["PUT"])
@token_required
def update_url(url_id):
    incoming = request.get_json() or {}
    incoming["updated_at"] = datetime.utcnow()

    # Fetch existing record
    try:
        old_data = urls_collection.find_one({"_id": ObjectId(url_id)})
    except:
        return jsonify({"message": "Invalid URL ID"}), 400

    if not old_data:
        return jsonify({"message": "URL not found"}), 404

    # Update DB
    urls_collection.update_one({"_id": ObjectId(url_id)}, {"$set": incoming})

    # Fetch updated record
    updated = urls_collection.find_one({"_id": ObjectId(url_id)})
    updated["_id"] = str(updated["_id"])

    # Update JSON (single unified function)
    
    update_domain(updated)
        
    print("✅ Domain updated in JSON")

    return jsonify(updated), 200

# @urls_bp.route("/<url_id>", methods=["PUT"])
# @token_required
# def update_url(url_id):
#     incoming = request.get_json() or {}
#     incoming["updated_at"] = datetime.utcnow()

#     # Fetch existing record first
#     try:
#         old_data = urls_collection.find_one({"_id": ObjectId(url_id)})
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if not old_data:
#         return jsonify({"message": "URL not found"}), 404

#     # Merge old + new fields
#     final_data = {**old_data, **incoming}
#     final_data["_id"] = old_data["_id"]  # Keep ObjectId

#     # Update DB
#     urls_collection.update_one({"_id": ObjectId(url_id)}, {"$set": incoming})

#     # Fetch updated
#     updated_url = urls_collection.find_one({"_id": ObjectId(url_id)})
#     updated_url["_id"] = str(updated_url["_id"])  # convert to str for JSON

#     # Update JSON properly via name-keyed structure
#     update_domain(updated_url)

#     return jsonify(updated_url), 200



# def fetch_all_urls_from_db():
#     urls = []
#     for url_data in urls_collection.find():
#         url_data["_id"] = str(url_data["_id"])
#         # ✅ Convert datetime fields to ISO strings
#         for key, value in url_data.items():
#             if isinstance(value, datetime):
#                 url_data[key] = value.isoformat()
#         urls.append(url_data)
#     return urls

# def fetch_user_allocated_urls(user_id):
#     try:
#         user = users_collection.find_one({"_id": ObjectId(user_id)})

#         if not user:
#             return []

#         urls = user.get("urls", [])

#         formatted = []
#         for u in urls:
#             if isinstance(u, str):
#                 formatted.append({"url": u})  # wrap strings as dicts
#             elif isinstance(u, dict) and "url" in u:
#                 formatted.append(u)
#         return formatted

#     except Exception as e:
#         return []



# @urls_bp.route("/<url_id>", methods=["PUT"])
# @token_required
# def update_url(url_id):
#     data = request.get_json()
#     data["updated_at"] = datetime.utcnow()

#     try:
#         result = urls_collection.update_one(
#             {"_id": ObjectId(url_id)},
#             {"$set": data}
#         )
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if result.matched_count == 0:
#         return jsonify({"message": "URL not found"}), 404

#     updated_url = urls_collection.find_one({"_id": ObjectId(url_id)})
#     updated_url["_id"] = str(updated_url["_id"])  # Convert ObjectId to string

#     return jsonify(updated_url), 200



# def fetch_user_allocated_urls(user_id):
#     try:
#         user = users_collection.find_one({"_id": ObjectId(user_id)})

#         if not user:
#             return {
#                 "success": False,
#                 "message": "User not found",
#                 "allocated_urls": []
#             }

#         return {
#             "success": True,
#             "user_id": str(user_id),
#             "allocated_urls": user.get("urls", [])
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "allocated_urls": []
#         }
# def fetch_user_allocated_urls(user_id):
#     try:
#         user = users_collection.find_one({"_id": ObjectId(user_id)})

#         if not user:
#             return []

#         # ✅ ONLY return list (not object)
#         return user.get("urls", [])

#     except Exception as e:
#         return []

