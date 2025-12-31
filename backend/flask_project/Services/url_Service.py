

# Services/url_Service.py
from db.mongo import urls_collection, users_collection
from bson.objectid import ObjectId
from datetime import datetime


def fetch_all_urls_from_db():
    urls = []
    for u in urls_collection.find():
        u["_id"] = str(u["_id"])
        for k, v in u.items():
            if isinstance(v, datetime):
                u[k] = v.isoformat()
        urls.append(u)
    return urls


def fetch_user_allocated_urls(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user.get("urls", []) if user else []
    except Exception:
        return []
