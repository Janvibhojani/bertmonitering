# # controllers/urls_controller.py

# from db.mongo import urls_collection
# from middleware.auth_middleware import token_required
#   # must expose current browser context
# from Services.scraper_service import schedule_on_scraper_loop, stop_event, is_running
# from Services.scraper_service import stop_event, schedule_on_scraper_loop
# from utils.globel import current_context,is_scraper_running
# from utils.sraping_playwright import add_new_target, update_existing_target, delete_existing_target
# from flask import Blueprint, jsonify, request
# from bson.objectid import ObjectId
# from datetime import datetime
# import json
# from Services.json_manager import add_domain,update_domain,delete_domain
# from sockets.combine_socket import send_to_clients
# urls_bp = Blueprint("urls", __name__)  

# @urls_bp.route("/", methods=["GET"])
# @token_required
# def get_all_urls():
#     urls = []
#     for url_data in urls_collection.find():
#         url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
#         urls.append(url_data)
#     return jsonify(urls), 200
# @urls_bp.route("/<url_id>", methods=["GET"])
# @token_required
# def get_url(url_id):
#     try:
#         url_data = urls_collection.find_one({"_id": ObjectId(url_id)})
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if not url_data:
#         return jsonify({"message": "URL not found"}), 404

#     url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
#     return jsonify(url_data), 200

# import asyncio
# from utils.sraping_playwright import delete_existing_target

# @urls_bp.route("/<url_id>", methods=["DELETE"])
# @token_required
# def delete_url(url_id):
#     from bson import ObjectId

#     # Validate ObjectId
#     try:
#         object_id = ObjectId(url_id)
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     # Delete from MongoDB
#     result = urls_collection.delete_one({"_id": object_id})
#     if result.deleted_count == 0:
#         return jsonify({"message": "URL not found"}), 404

#     # Delete from JSON
#     json_deleted = delete_domain(url_id)
#     print("✅ Domain deleted from JSON")
#      # schedule async deletion

#     return jsonify({
#         "message": "URL deleted successfully",
#         "json_deleted": json_deleted
#     }), 200

# import json
# @urls_bp.route("/", methods=["POST"])
# @token_required
# def create_url():
#     # -----------------------------
#     # 🔹 Force JSON parse & catch errors
#     # -----------------------------
#     try:
#         data = request.get_json(force=True) or {}
#         print("✅ Incoming JSON parsed successfully", json.dumps(data, indent=4))
#     except Exception as e:
#         print("JSON PARSE ERROR:", e)
#         return jsonify({"error": "Invalid JSON format"}), 400

#     # 👇 aa thi baki code jema URL create karvanu che
#     new_domain = data.get("domain")
#     if not new_domain:
#         return jsonify({"error": "URL is required"}), 400
#     existing = urls_collection.find_one({"domain": new_domain})
#     if existing:
#         return jsonify({
#             "status": "error",
#             "message": "Url is  already exists",
#             "existing_id": str(existing["_id"]),
#             "existing_domain": existing["domain"]
#         }), 409

#     data["created_at"] = datetime.utcnow().isoformat()
#     data["updated_at"] = datetime.utcnow().isoformat()


#     if data.get("target"):
#         data["scrap_from"] = "HTML"
#         data["only_on_change"] = False
#         data["interval_ms"] = 0
#     else:
#         data["scrap_from"] = "API"
#         data.pop("target", None)
#         data.pop("mode", None)

#     result = urls_collection.insert_one(data)
#     data["_id"] = str(result.inserted_id)

#     # Add to JSON
#     add_domain(data)
#     if current_context:
#         schedule_on_scraper_loop(
#             add_new_target(current_context, data, stop_event, lambda payload: asyncio.create_task(send_to_clients(payload)))
#     )
#     print("✅ url added to JSON")
 

#     return jsonify({
#         "status": "success",
#         "message": "New URL created successfully",
#         "data": data
#     }), 201

# @urls_bp.route("/<url_id>", methods=["PUT"])
# @token_required
# def update_url(url_id):
#     incoming = request.get_json() or {}
#     incoming["updated_at"] = datetime.utcnow()

#     # Fetch existing record
#     try:
#         old_data = urls_collection.find_one({"_id": ObjectId(url_id)})
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if not old_data:
#         return jsonify({"message": "URL not found"}), 404

#     # Update DB
#     urls_collection.update_one({"_id": ObjectId(url_id)}, {"$set": incoming})

#     # Fetch updated record
#     updated = urls_collection.find_one({"_id": ObjectId(url_id)})
#     updated["_id"] = str(updated["_id"])

#     # Update JSON (single unified function)
    
#     update_domain(updated)
    
#     print("✅ Domain updated in JSON")

#     return jsonify(updated), 200

# from db.mongo import urls_collection
# from middleware.auth_middleware import token_required
#   # must expose current browser context
# from Services.scraper_service import schedule_on_scraper_loop, stop_event, is_running
# from Services.scraper_service import stop_event, schedule_on_scraper_loop
# from utils.globel import *
# from utils.sraping_playwright import add_new_target, update_existing_target, delete_existing_target
# from flask import Blueprint, jsonify, request
# from bson.objectid import ObjectId
# from datetime import datetime
# import json
# from Services.json_manager import add_domain,update_domain,delete_domain
# from sockets.combine_socket import send_to_clients
# urls_bp = Blueprint("urls", __name__)  

# @urls_bp.route("/", methods=["GET"])
# @token_required
# def get_all_urls():
#     urls = []
#     for url_data in urls_collection.find():
#         url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
#         urls.append(url_data)
#     return jsonify(urls), 200
# @urls_bp.route("/<url_id>", methods=["GET"])
# @token_required
# def get_url(url_id):
#     try:
#         url_data = urls_collection.find_one({"_id": ObjectId(url_id)})
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if not url_data:
#         return jsonify({"message": "URL not found"}), 404

#     url_data["_id"] = str(url_data["_id"])  # Convert ObjectId to string
#     return jsonify(url_data), 200

# async def notify_clients(payload):
#     await send_to_clients(payload)

# @urls_bp.route("/", methods=["POST"])
# @token_required
# def create_url():
#     try:
#         data = request.get_json(force=True) or {}
#         print("✅ Incoming JSON parsed successfully", json.dumps(data, indent=4))
#     except Exception as e:
#         print("JSON PARSE ERROR:", e)
#         return jsonify({"error": "Invalid JSON format"}), 400

#     new_domain = data.get("domain")
#     if not new_domain:
#         return jsonify({"error": "URL is required"}), 400
    
#     existing = urls_collection.find_one({"domain": new_domain})
#     if existing:
#         return jsonify({
#             "status": "error",
#             "message": "Url already exists",
#             "existing_id": str(existing["_id"]),
#             "existing_domain": existing["domain"]
#         }), 409

#     data["created_at"] = datetime.utcnow().isoformat()
#     data["updated_at"] = datetime.utcnow().isoformat()

#     if data.get("target"):
#         data["scrap_from"] = "HTML"
#         data["only_on_change"] = False
#         data["interval_ms"] = 0
#     else:
#         data["scrap_from"] = "API"
#         data.pop("target", None)
#         data.pop("mode", None)

#     result = urls_collection.insert_one(data)
#     data["_id"] = str(result.inserted_id)

#     # Add to JSON
#     add_domain(data)
#     print("✅ url added to JSON")

#     # Dynamically add to running scraper
#     if is_running and is_scraper_running():
#         async def add_target():
#             try:
#                 context = get_scraper_context()
#                 if context and not context.is_closed():
#                     await add_new_target(
#                         context, 
#                         data, 
#                         stop_event, 
#                         notify_clients  # Use notify_clients directly
#                     )
#                     print(f"✅ Successfully added new target to running scraper: {data.get('domain')}")
#                 else:
#                     print("⚠ Scraper context not available or closed")
#             except Exception as e:
#                 print(f"❌ Failed to add target to running scraper: {e}")

#         # Schedule the add_target coroutine - ONLY ONCE, outside the function
#         schedule_on_scraper_loop(add_target())
#     else:
#         print("⚠ Scraper not running or context not available. New URL will be picked up on next restart.")

#     return jsonify({
#         "status": "success",
#         "message": "New URL created successfully",
#         "data": data
#     }), 201
# @urls_bp.route("/<url_id>", methods=["PUT"])
# @token_required
# def update_url(url_id):
#     incoming = request.get_json() or {}
#     incoming["updated_at"] = datetime.utcnow()

#     try:
#         old_data = urls_collection.find_one({"_id": ObjectId(url_id)})
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     if not old_data:
#         return jsonify({"message": "URL not found"}), 404

#     # Update DB
#     urls_collection.update_one({"_id": ObjectId(url_id)}, {"$set": incoming})

#     # Fetch updated record
#     updated = urls_collection.find_one({"_id": ObjectId(url_id)})
#     updated["_id"] = str(updated["_id"])

#     # Update JSON
#     update_domain(updated)
#     print("✅ Domain updated in JSON")

#     # Dynamically update in running scraper
#     if is_running and is_scraper_running():
#         async def update_target():
#             try:
#                 context = get_scraper_context()
#                 if context and not context.is_closed():
#                     await update_existing_target(
#                         context,
#                         updated,
#                         stop_event,
#                         notify_clients
#                     )
#                     print(f"✅ Successfully updated target in running scraper: {updated.get('domain')}")
#                 else:
#                     print("⚠ Scraper context not available or closed")
#             except Exception as e:
#                 print(f"❌ Failed to update target in running scraper: {e}")

#         schedule_on_scraper_loop(update_target())
#     else:
#         print("⚠ Scraper not running or context not available. Update will be picked up on next restart.")

#     return jsonify(updated), 200
# @urls_bp.route("/<url_id>", methods=["DELETE"])
# @token_required
# def delete_url(url_id):
#     try:
#         object_id = ObjectId(url_id)
#     except:
#         return jsonify({"message": "Invalid URL ID"}), 400

#     # Fetch URL before deletion for notification
#     url_to_delete = urls_collection.find_one({"_id": object_id})
    
#     # Delete from MongoDB
#     result = urls_collection.delete_one({"_id": object_id})
#     if result.deleted_count == 0:
#         return jsonify({"message": "URL not found"}), 404

#     # Delete from JSON
#     json_deleted = delete_domain(url_id)
#     print("✅ Domain deleted from JSON")

#     # Dynamically delete from running scraper
#     if is_running and is_scraper_running() and url_to_delete:
#         async def delete_target():
#             try:
#                 await delete_existing_target(
#                     url_id,
#                     notify_clients
#                 )
#                 print(f"✅ Successfully deleted target from running scraper: {url_id}")
#             except Exception as e:
#                 print(f"❌ Failed to delete target from running scraper: {e}")

#         schedule_on_scraper_loop(delete_target())

#     return jsonify({
#         "message": "URL deleted successfully",
#         "json_deleted": json_deleted
#     }), 200
    
    
# @urls_bp.route("/debug/pages", methods=["GET"])
# @token_required
# def debug_pages():
#     from utils.sraping_playwright import html_pages
    
#     pages_info = []
#     for cfg, page, task in html_pages:
#         try:
#             page_closed = page.is_closed() if hasattr(page, 'is_closed') else 'Unknown'
#         except:
#             page_closed = 'Error checking'
            
#         pages_info.append({
#             "name": cfg.get("name", "Unnamed"),
#             "domain": cfg.get("domain"),
#             "url_id": str(cfg.get("_id", "")),
#             "page_closed": page_closed,
#             "task_done": task.done() if task else 'No task'
#         })
    
#     return jsonify({
#         "total_pages": len(html_pages),
#         "pages": pages_info
#     }), 200
# controllers/urls_controller.py
# controllers/urls_controller.py - FIXED VERSION
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime
import json
import asyncio
import logging

from db.mongo import urls_collection
from middleware.auth_middleware import token_required
from Services.json_manager import add_domain, update_domain, delete_domain
from sockets.combine_socket import send_to_clients

# Import scraper service functions
from Services.scraper_service import (
    schedule_on_scraper_loop,
    get_is_running,
    execute_on_scraper,
    get_stop_event
)

# Import scraping_playwright functions
from utils.sraping_playwright import (
    add_new_target, 
    update_existing_target, 
    delete_existing_target
)

# Import globel functions
from utils.globel import get_scraper_context, is_scraper_running

urls_bp = Blueprint("urls", __name__)

async def notify_clients(payload):
    await send_to_clients(payload)

def check_scraper_status():
    """Helper to check scraper status with detailed logging"""
    from Services.scraper_service import get_is_running
    running = get_is_running()
    context = get_scraper_context()
    context_available = context is not None
    context_closed = False
    
    if context and hasattr(context, 'is_closed'):
        context_closed = context.is_closed()
    
    print(f"🔍 Scraper Status Check:")
    print(f"   - Service is_running: {running}")
    print(f"   - Context available: {context_available}")
    print(f"   - Context closed: {context_closed}")
    print(f"   - Global is_scraper_running(): {is_scraper_running()}")
    
    return running and context_available and not context_closed

@urls_bp.route("/", methods=["GET"])
@token_required
def get_all_urls():
    urls = []
    for url_data in urls_collection.find():
        url_data["_id"] = str(url_data["_id"])
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

    url_data["_id"] = str(url_data["_id"])
    return jsonify(url_data), 200

@urls_bp.route("/", methods=["POST"])
@token_required
def create_url():
    try:
        data = request.get_json(force=True) or {}
    except Exception as e:
        return jsonify({"error": "Invalid JSON format"}), 400

    new_domain = data.get("domain")
    if not new_domain:
        return jsonify({"error": "URL is required"}), 400
    
    existing = urls_collection.find_one({"domain": new_domain})
    if existing:
        return jsonify({
            "status": "error",
            "message": "Url already exists",
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
    print("✅ url added to JSON")

    # Check scraper status
    scraper_active = check_scraper_status()
    
    # Dynamically add to running scraper
    if scraper_active:
        print("🎯 Attempting to add target to running scraper...")
        
        async def add_target_live():
            try:
                context = get_scraper_context()
                if context and hasattr(context, 'is_closed') and not context.is_closed():
                    print(f"🎯 Adding target: {data.get('domain')}")
                    await add_new_target(
                        context, 
                        data, 
                        get_stop_event(), 
                        notify_clients
                    )
                    print(f"✅ Successfully added new target to running scraper: {data.get('domain')}")
                    
                    # Verify addition
                    from utils.sraping_playwright import html_pages
                    print(f"📊 Total pages after addition: {len(html_pages)}")
                    for cfg, page, task in html_pages:
                        print(f"   - {cfg.get('name')}: page_closed={page.is_closed() if hasattr(page, 'is_closed') else 'N/A'}")
                    
                else:
                    print("⚠ Scraper context not available or closed")
            except Exception as e:
                print(f"❌ Failed to add target to running scraper: {e}")
                import traceback
                traceback.print_exc()

        # Schedule the task
        scheduled = schedule_on_scraper_loop(add_target_live())
        if scheduled:
            print("✅ Task scheduled successfully")
        else:
            print("⚠ Failed to schedule task")
    else:
        print("⚠ Scraper not running or context not available. New URL will be picked up on next restart.")

    return jsonify({
        "status": "success",
        "message": "New URL created successfully",
        "data": data,
        "scraper_active": scraper_active,
        "added_live": scraper_active
    }), 201

@urls_bp.route("/<url_id>", methods=["PUT"])
@token_required
def update_url(url_id):
    incoming = request.get_json() or {}
    incoming["updated_at"] = datetime.utcnow()

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

    # Update JSON
    update_domain(updated)
    print("✅ Domain updated in JSON")

    # Check scraper status
    scraper_active = check_scraper_status()
    
    # Dynamically update in running scraper
    if scraper_active:
        async def update_target_live():
            try:
                context = get_scraper_context()
                if context and hasattr(context, 'is_closed') and not context.is_closed():
                    await update_existing_target(
                        context,
                        updated,
                        get_stop_event(),
                        notify_clients
                    )
                    print(f"✅ Successfully updated target in running scraper: {updated.get('domain')}")
                else:
                    print("⚠ Scraper context not available or closed")
            except Exception as e:
                print(f"❌ Failed to update target in running scraper: {e}")

        schedule_on_scraper_loop(update_target_live())
    else:
        print("⚠ Scraper not running or context not available. Update will be picked up on next restart.")

    return jsonify(updated), 200

@urls_bp.route("/<url_id>", methods=["DELETE"])
@token_required
def delete_url(url_id):
    try:
        object_id = ObjectId(url_id)
    except:
        return jsonify({"message": "Invalid URL ID"}), 400

    # Fetch URL before deletion for notification
    url_to_delete = urls_collection.find_one({"_id": object_id})
    
    # Delete from MongoDB
    result = urls_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        return jsonify({"message": "URL not found"}), 404

    # Delete from JSON
    json_deleted = delete_domain(url_id)
    print("✅ Domain deleted from JSON")

    # Check scraper status
    scraper_active = check_scraper_status()
    
    # Dynamically delete from running scraper
    if scraper_active and url_to_delete:
        async def delete_target_live():
            try:
                await delete_existing_target(
                    url_id,
                    notify_clients
                )
                print(f"✅ Successfully deleted target from running scraper: {url_id}")
            except Exception as e:
                print(f"❌ Failed to delete target from running scraper: {e}")

        schedule_on_scraper_loop(delete_target_live())

    return jsonify({
        "message": "URL deleted successfully",
        "json_deleted": json_deleted,
        "scraper_active": scraper_active,
        "deleted_live": scraper_active
    }), 200

@urls_bp.route("/debug/pages", methods=["GET"])
@token_required
def debug_pages():
    from utils.sraping_playwright import html_pages
    
    pages_info = []
    for cfg, page, task in html_pages:
        try:
            page_closed = page.is_closed() if hasattr(page, 'is_closed') else 'Unknown'
        except:
            page_closed = 'Error checking'
            
        pages_info.append({
            "name": cfg.get("name", "Unnamed"),
            "domain": cfg.get("domain"),
            "url_id": str(cfg.get("_id", "")),
            "page_closed": page_closed,
            "task_done": task.done() if task else 'No task'
        })
    
    return jsonify({
        "total_pages": len(html_pages),
        "pages": pages_info
    }), 200

@urls_bp.route("/debug/scraper-status", methods=["GET"])
@token_required
def debug_scraper_status():
    """Debug endpoint to check scraper status"""
    status = check_scraper_status()
    
    # Get more details
    from Services.scraper_service import get_is_running, get_scraper_loop
    from utils.sraping_playwright import html_pages
    
    loop = get_scraper_loop()
    loop_running = loop is not None and loop.is_running() if loop else False
    
    return jsonify({
        "scraper_active": status,
        "service_is_running": get_is_running(),
        "event_loop_running": loop_running,
        "active_pages": len(html_pages),
        "context_available": get_scraper_context() is not None
    }), 200