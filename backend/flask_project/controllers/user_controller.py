
from db.mongo import users_collection,subscribe_data_collection
from bson.objectid import ObjectId
from flask import Blueprint, jsonify, g, request
from middleware.auth_middleware import token_required
from datetime import datetime



user_bp = Blueprint("user", __name__)

def fetch_allocated_urls_by_user_id(user_id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(user_id)}},
        {
            "$addFields": {
                "urls": {
                    "$map": {
                        "input": "$urls",
                        "as": "url_id",
                        "in": {"$toObjectId": "$$url_id"}
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "urls",
                "localField": "urls",
                "foreignField": "_id",
                "as": "allocated_urls_details"
            }
        },
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "username": 1,
                "email": 1,
                "allocated_urls_details": {
                    "$map": {
                        "input": "$allocated_urls_details",
                        "as": "url",
                        "in": {
                            "_id": {"$toString": "$$url._id"},
                            "name": "$$url.name",
                            "url": "$$url.url",
                            "target": "$$url.target",
                            "mode": "$$url.mode",
                            "scrap_from": "$$url.scrap_from",
                            "only_on_change": "$$url.only_on_change",
                            "interval_ms": "$$url.interval_ms",
                            "created_at": "$$url.created_at",
                            "updated_at": "$$url.updated_at"
                        }
                    }
                }
            }
        }
    ]

    result = list(users_collection.aggregate(pipeline))
    return result[0] if result else None

@user_bp.route("/subscribe", methods=["PUT"])
@token_required
def subscribe_symbols():

    data = request.get_json(force=True)

    # ✅ HARD SAFETY CHECK
    if not isinstance(data, dict):
        return jsonify({
            "message": "Invalid JSON body, expected object"
        }), 400

    user_id = data.get("user_id")
    subscriptions = data.get("subscriptions")

    if not user_id or not isinstance(subscriptions, list):
        return jsonify({
            "message": "user_id and subscriptions array required"
        }), 400
    try:
        user_object_id = ObjectId(user_id)
    except:
        return jsonify({"message": "Invalid user_id"}), 400

    now = datetime.utcnow()

    doc = subscribe_data_collection.find_one({"user_id": user_object_id})

    if not doc:
        subscribe_data_collection.insert_one({
            "user_id": user_object_id,
            "subscriptions": [
                {
                    "marketname": s["marketname"],
                    "subscribed_symbols": s["symbols"]
                } for s in subscriptions
            ],
            "last_updated": now
        })

        return jsonify({"message": "Subscriptions created"}), 201

    # 🔁 Update existing
    for s in subscriptions:
        marketname = s["marketname"]
        symbols = s["symbols"]

        result = subscribe_data_collection.update_one(
            {
                "_id": doc["_id"],
                "subscriptions.marketname": marketname
            },
            {
                "$set": {
                    "subscriptions.$.subscribed_symbols": symbols,
                    "last_updated": now
                }
            }
        )

        if result.matched_count == 0:
            subscribe_data_collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$push": {
                        "subscriptions": {
                            "marketname": marketname,
                            "subscribed_symbols": symbols
                        }
                    },
                    "$set": {"last_updated": now}
                }
            )

    return jsonify({"message": "Subscriptions updated"}), 200


def get_user_subscriptions(user_id):
    try:
        user_object_id = ObjectId(user_id)
    except:
        return []

    doc = subscribe_data_collection.find_one(
        {"user_id": user_object_id},
        {"_id": 0, "subscriptions": 1}
    )

    if not doc:
        return []

    return doc.get("subscriptions", [])

@user_bp.route("/get_subscribelist", methods=["GET"])
@token_required
def get_subscriptions():
    user_id = g.user_id   # ✅ token mathi aavse
    if not user_id:
        return jsonify({"message": "Invalid token user"}), 401
    subscriptions = get_user_subscriptions(user_id)

    return jsonify({
        "user_id": user_id,
        "subscriptions": subscriptions
    }), 200
