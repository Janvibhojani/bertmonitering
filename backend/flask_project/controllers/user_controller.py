
from db.mongo import users_collection
from bson.objectid import ObjectId
from flask import Blueprint, jsonify, g, request
from middleware.auth_middleware import token_required

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


@user_bp.route("/allocated-urls", methods=["GET"])
@token_required
def get_allocated_urls():
    try:
        user_id = g.user.get("user_id")

        if not user_id:
            return jsonify({"message": "Invalid token"}), 401

        result = fetch_allocated_urls_by_user_id(user_id)

        if not result:
            return jsonify({"message": "User not found"}), 404

        return jsonify(result), 200

    except Exception as e:
        print("❌ Error in allocated-urls route:", e)
        return jsonify({"message": "Internal server error"}), 500