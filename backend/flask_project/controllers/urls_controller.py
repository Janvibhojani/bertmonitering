
# controllers/urls_controller.py - FIXED VERSION
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime


from db.mongo import urls_collection
from middleware.auth_middleware import token_required
from Services.json_manager import add_domain, update_domain, delete_domain


# Import scraper service functions
from Services.scraper_service import (
    schedule_on_scraper_loop,
    get_stop_event,
    get_send_func 
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

def check_scraper_status():
    """Helper to check scraper status with detailed logging"""
    from Services.scraper_service import get_is_running,get_send_func
    running = get_is_running()
    context = get_scraper_context()
    context_available = context is not None
    send_func = get_send_func()
    context_closed = False
    
    
    
    print(f"🔍 Scraper Status Check:")
    print(f"   - Service is_running: {running}")
    print(f"   - Context available: {context_available}")
    print(f"   - Send func available: {send_func is not None}")
    print(f"   - Context closed: {context_closed}")
    print(f"   - Global is_scraper_running(): {is_scraper_running()}")
    

    return running and context_available and send_func is not None

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
    except Exception:
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

    if scraper_active:
        print("🎯 Attempting to add target to running scraper...")

        async def add_target_live():
            try:
                context = get_scraper_context()
                print("--ctx-->", context)

                if not context:
                    print("❌ No scraper context")
                    return

                # ✅ SAFE CONTEXT CHECK
                try:
                    test_page = await context.new_page()
                    await test_page.close()
                except Exception as e:
                    print("❌ Context unusable:", e)
                    return

                print(f"🎯 Adding target: {data.get('domain')}")
                send_func = get_send_func()
                if not send_func:
                    print("❌ send_func not available")
                    return

                await add_new_target(
                    context,
                    data,
                    get_stop_event(),
                    send_func
                    
                )

                print(f"✅ Successfully added new target: {data.get('domain')}")

                # Verify
                from utils.sraping_playwright import html_pages
                print(f"📊 Total pages after addition: {len(html_pages)}")

            except Exception as e:
                print(f"❌ Failed to add target live: {e}")
                import traceback
                traceback.print_exc()

        scheduled = schedule_on_scraper_loop(add_target_live())
        if scheduled:
            print("✅ Task scheduled successfully")
        else:
            print("⚠ Failed to schedule task")

    else:
        print("⚠ Scraper not running. Will load on restart.")

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
    incoming = request.get_json(force=True) or {}
    incoming["updated_at"] = datetime.utcnow().isoformat()

    try:
        old_data = urls_collection.find_one({"_id": ObjectId(url_id)})
    except Exception:
        return jsonify({"message": "Invalid URL ID"}), 400

    if not old_data:
        return jsonify({"message": "URL not found"}), 404

    # Update DB
    urls_collection.update_one(
        {"_id": ObjectId(url_id)},
        {"$set": incoming}
    )

    # Fetch updated record
    updated = urls_collection.find_one({"_id": ObjectId(url_id)})
    updated["_id"] = str(updated["_id"])

    # Update JSON
    update_domain(updated)
    print("✅ Domain updated in JSON")

    # Check scraper status
    scraper_active = check_scraper_status()

    if scraper_active:
        print("🎯 Attempting to update target in running scraper...")

        async def update_target_live():
            try:
                context = get_scraper_context()
                print("CTX =", context)

                if not context:
                    print("❌ No scraper context")
                    return

                # ✅ SAFE CONTEXT CHECK
                try:
                    test_page = await context.new_page()
                    await test_page.close()
                except Exception as e:
                    print("❌ Context unusable:", e)
                    return
                send_func = get_send_func()

                if not send_func:
                    print("❌ send_func not available")
                    return
                await update_existing_target(
                    context,
                    updated,
                    get_stop_event(),
                    send_func
                   
                )

                print(f"✅ Successfully updated target: {updated.get('domain')}")

            except Exception as e:
                print(f"❌ Failed to update target live: {e}")
                import traceback
                traceback.print_exc()

        scheduled = schedule_on_scraper_loop(update_target_live())
        if scheduled:
            print("✅ Update task scheduled successfully")
        else:
            print("⚠ Failed to schedule update task")

    else:
        print("⚠ Scraper not running. Update will apply on restart.")

    return jsonify({
        "status": "success",
        "message": "URL updated successfully",
        "scraper_active": scraper_active
    }), 200

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

