# controllers/urls_controller.py
from db.mongo import urls_collection
from middleware.auth_middleware import token_required

from utils.sraping_playwright import add_new_target, delete_existing_target, update_existing_target,current_context
import asyncio
from sockets.combine_socket import send_to_clients

  # must expose current browser context
from Services.scraper_service import stop_event
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime
from bson import ObjectId
from Services.json_manager import add_domain,update_domain,delete_domain

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

import asyncio
from utils.sraping_playwright import delete_existing_target

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
    if current_context:
        run_async_task(delete_existing_target(url_id))
    print("✅ Domain deleted from JSON")
     # schedule async deletion

    return jsonify({
        "message": "URL deleted successfully",
        "json_deleted": json_deleted
    }), 200

import json
@urls_bp.route("/", methods=["POST"])
@token_required
def create_url():
    # -----------------------------
    # 🔹 Force JSON parse & catch errors
    # -----------------------------
    try:
        data = request.get_json(force=True) or {}
        print("✅ Incoming JSON parsed successfully", json.dumps(data, indent=4))
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return jsonify({"error": "Invalid JSON format"}), 400

    # 👇 aa thi baki code jema URL create karvanu che
    new_domain = data.get("domain")
    if not new_domain:
        return jsonify({"error": "URL is required"}), 400
    existing = urls_collection.find_one({"domain": new_domain})
    if existing:
        return jsonify({
            "status": "error",
            "message": "Url is  already exists",
            "existing_id": str(existing["_id"]),
            "existing_domain": existing["domain"]
        }), 409

    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()


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

    # Add to JSON
    add_domain(data)
    if current_context:  # only if browser is running
    
        run_async_task(add_new_target(current_context, data, stop_event, lambda payload: asyncio.create_task(send_to_clients(payload))))
    print("✅ url added to JSON")
 

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
    if current_context:
        run_async_task(update_existing_target(current_context, updated, stop_event, lambda payload: asyncio.create_task(send_to_clients(payload))))
    print("✅ Domain updated in JSON")

    return jsonify(updated), 200

  # the global stop_event used by the scraper

def run_async_task(coro):
    """Schedule async function in running event loop safely."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        # If no event loop, create new
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(coro)
        new_loop.close()


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

