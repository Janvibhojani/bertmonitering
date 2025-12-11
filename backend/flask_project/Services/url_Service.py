# Services/url_Service.py
from db.mongo import urls_collection
from bson.objectid import ObjectId
from datetime import datetime
import time

def fetch_all_urls_from_db():
    urls = []
    for url_data in urls_collection.find():
        url_data["_id"] = str(url_data["_id"])

        # Convert datetime fields
        for k, v in url_data.items():
            if isinstance(v, datetime):
                url_data[k] = v.isoformat()

        urls.append(url_data)
    return urls


def detect_changes(old_list, new_list):
    """Find added, deleted, updated URLs"""

    # Convert to dict by ID
    old_map = {item["_id"]: item for item in old_list}
    new_map = {item["_id"]: item for item in new_list}

    added = [new_map[id] for id in new_map if id not in old_map]
    deleted = [old_map[id] for id in old_map if id not in new_map]

    updated = []
    for id in new_map:
        if id in old_map and new_map[id] != old_map[id]:
            updated.append(new_map[id])

    return added, deleted, updated


def start_dynamic_url_watcher(callback_add, callback_delete, callback_update, interval=3):
    """Continuously checks DB for changes & fires callbacks"""

    print("🚀 URL Watcher started...")

    old_targets = fetch_all_urls_from_db()

    while True:
        time.sleep(interval)

        new_targets = fetch_all_urls_from_db()

        added, deleted, updated = detect_changes(old_targets, new_targets)

        # ---- 🔥 Fire Callbacks ----
        for url in added:
            print("➕ Added:", url)
            callback_add(url)

        for url in deleted:
            print("❌ Deleted:", url)
            callback_delete(url)

        for url in updated:
            print("♻️ Updated:", url)
            callback_update(url)

        # update baseline
        old_targets = new_targets



# # url_Service.py
# from db.mongo import urls_collection, users_collection
# from bson.objectid import ObjectId
# from datetime import datetime

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
