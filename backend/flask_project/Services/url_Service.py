

# url_Service.py
from db.mongo import urls_collection, users_collection
from bson.objectid import ObjectId
from datetime import datetime

def fetch_all_urls_from_db():
    urls = []
    for url_data in urls_collection.find():
        url_data["_id"] = str(url_data["_id"])
        # ✅ Convert datetime fields to ISO strings
        for key, value in url_data.items():
            if isinstance(value, datetime):
                url_data[key] = value.isoformat()
        urls.append(url_data)
    return urls

def fetch_user_allocated_urls(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            return []

        urls = user.get("urls", [])

        formatted = []
        for u in urls:
            if isinstance(u, str):
                formatted.append({"url": u})  # wrap strings as dicts
            elif isinstance(u, dict) and "url" in u:
                formatted.append(u)
        return formatted

    except Exception as e:
        return []
