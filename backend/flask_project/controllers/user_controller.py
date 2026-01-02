
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

    data = request.get_json()

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
        # 🆕 create new user subscription doc
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

    # 🔁 update existing
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


# @user_bp.route("/allocated-urls", methods=["GET"])
# @token_required
# def get_allocated_urls():
#     try:
#         user_id = g.user.get("user_id")

#         if not user_id:
#             return jsonify({"message": "Invalid token"}), 401

#         result = fetch_allocated_urls_by_user_id(user_id)

#         if not result:
#             return jsonify({"message": "User not found"}), 404

#         return jsonify(result), 200

#     except Exception as e:
#         print("❌ Error in allocated-urls route:", e)
#         return jsonify({"message": "Internal server error"}), 500
    
# from flask import Blueprint, request, jsonify, g
# from bson import ObjectId
# from db.mongo import subscribe_data_collection
# from middleware.auth_middleware import token_required
# from datetime import datetime

# user_bp = Blueprint("user", __name__)

# @user_bp.route("/subscribe", methods=["PUT"])
# @token_required
# def subscribe_symbols():
#     data = request.get_json()
#     user_id = data.get("user_id")
#     marketname = data.get("marketname")
#     symbols = data.get("symbols")  # list of strings

#     if not user_id or not marketname or not isinstance(symbols, list):
#         return jsonify({"message": "user_id, marketname, and symbols array are required"}), 400

#     try:
#         user_object_id = ObjectId(user_id)
#     except:
#         return jsonify({"message": "Invalid user_id"}), 400

#     now = datetime.utcnow()

#     # 🔹 Check if user document exists
#     existing_user = subscribe_data_collection.find_one({"user_id": user_object_id})

#     if existing_user:
#         # 🔹 Check if this market already exists
#         market_index = None
#         for idx, sub in enumerate(existing_user.get("subscriptions", [])):
#             if sub.get("marketname") == marketname:
#                 market_index = idx
#                 break

#         if market_index is not None:
#             # Update symbols for this market
#             subscribe_data_collection.update_one(
#                 {"user_id": user_object_id, f"subscriptions.{market_index}.marketname": marketname},
#                 {
#                     "$set": {
#                         f"subscriptions.{market_index}.subscribed_symbols": symbols,
#                         "last_updated": now
#                     }
#                 }
#             )
#         else:
#             # Add new market to subscriptions
#             subscribe_data_collection.update_one(
#                 {"user_id": user_object_id},
#                 {
#                     "$push": {
#                         "subscriptions": {
#                             "marketname": marketname,
#                             "subscribed_symbols": symbols
#                         }
#                     },
#                     "$set": {"last_updated": now}
#                 }
#             )
#     else:
#         # New user subscription document
#         subscribe_data_collection.insert_one({
#             "user_id": user_object_id,
#             "subscriptions": [
#                 {
#                     "marketname": marketname,
#                     "subscribed_symbols": symbols
#                 }
#             ],
#             "last_updated": now
#         })

#     return jsonify({"message": "Subscription saved successfully"}), 200

    
# @user_bp.route("/subscribe", methods=["PUT"])
# @token_required
# def subscribe_symbols():
#     data = request.get_json()

#     # 🔹 Validation
#     user_id = data.get("user_id")
#     marketname = data.get("marketname")
#     symbols = data.get("symbols")

#     if not user_id or not marketname or not isinstance(symbols, list):
#         return jsonify({
#             "message": "user_id, marketname and symbols (array) are required"
#         }), 400

#     try:
#         user_object_id = ObjectId(user_id)
#     except:
#         return jsonify({"message": "Invalid user_id"}), 400

#     now = datetime.utcnow()

#     # 🔁 If already exists → update
#     existing = subscribe_data_collection.find_one({
#         "user_id": user_object_id,
#         "marketname": marketname
#     })

#     if existing:
#         subscribe_data_collection.update_one(
#             {"_id": existing["_id"]},
#             {
#                 "$set": {
#                     "symbols": symbols,
#                     "updated_at": now
#                 }
#             }
#         )
#         return jsonify({
#             "message": "Subscription updated successfully"
#         }), 200

#     # 🆕 Else insert new
#     subscribe_data_collection.insert_one({
#         "user_id": user_object_id,
#         "marketname": marketname,
#         "symbols": symbols,
#         "created_at": now,
#         "updated_at": now
#     })

#     return jsonify({
#         "message": "Subscription created successfully"
#     }), 201



@user_bp.route("/subscribe/test", methods=["GET"])
def subscribe_test():
    return "Subscribe route is alive", 200
