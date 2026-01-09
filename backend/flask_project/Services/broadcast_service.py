# services/broadcast_service.py
import logging
from copy import deepcopy
from sockets.combine_socket import user_subscriptions
def broadcast_to_clients(sio, connected_clients, authenticated_clients, payload):
    """
    RULES:
    - ADMIN → FULL payload
    - USER  → ONLY allocated url_id data
    """

    try:
        url_ids = extract_url_ids(payload)
        logging.info(f"📦 url_ids found in payload: {url_ids}")

        # 👑 ADMIN → FULL PAYLOAD
        sio.emit(
            "data",
            {
                **payload,
                "meta": {
                    "filtered": False,
                    "role": "admin"
                }
            },
            room="admin"
        )
        for url_id in url_ids:
            filtered_payload = filter_payload_by_url(payload, url_id)

            if not filtered_payload["html_scrape"] and not filtered_payload["api_scrape"]:
                continue

            room_name = f"url:{url_id}"
            sids = list(
                sio.manager.rooms.get("/", {}).get(room_name, set())
            )

            for sid in sids:
                auth = authenticated_clients.get(sid)
                if not auth:
                    continue

                user_room = f"user:{auth['user_id']}"
                subscriptions = user_subscriptions.get(user_room)

                final_payload = filtered_payload

                
                if subscriptions:
                    final_payload = apply_subscription_filter(
                        filtered_payload,
                        subscriptions
                    )

                if not final_payload["html_scrape"] and not final_payload["api_scrape"]:
                    continue

                # ✅ AHI EMIT KARVU CHE
                sio.emit(
                    "data",
                    {
                        **final_payload,
                        "meta": {
                            "filtered": True,
                            "url_id": url_id,
                            "role": "user"
                        }
                    },
                    to=sid
                )
                
    except Exception:
        logging.error("❌ Broadcast failed", exc_info=True)

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def extract_url_ids(payload):
    ids = set()

    for block in payload.get("html_scrape", []):
        for _, data in block.items():
            if isinstance(data, dict) and data.get("url_id"):
                ids.add(str(data["url_id"]))

    for item in payload.get("api_scrape", []):
        if item.get("url_id"):
            ids.add(str(item["url_id"]))

    return ids


def filter_payload_by_url(payload, url_id):
    filtered = {
        "type": payload.get("type"),
        "html_scrape": [],
        "api_scrape": []
    }

    for block in payload.get("html_scrape", []):
        for name, data in block.items():
            if isinstance(data, dict) and str(data.get("url_id")) == str(url_id):
                filtered["html_scrape"].append({name: deepcopy(data)})

    for item in payload.get("api_scrape", []):
        if str(item.get("url_id")) == str(url_id):
            filtered["api_scrape"].append(deepcopy(item))

    return filtered

def apply_subscription_filter(payload, subscriptions):
    filtered_html = []
    filtered_api = []

    # -------- HTML --------
    for entry in payload.get("html_scrape", []):
        market_name = list(entry.keys())[0]
        market_data = entry[market_name]
        records = market_data.get("records", [])

        # ✅ NEW LOGIC (symbols array support)
        selected_symbols = []
        for s in subscriptions:
            if s.get("marketname") == market_name:
                selected_symbols.extend(s.get("symbols", []))

        filtered_records = [
            r for r in records
            if r.get("Name") in selected_symbols
        ]

        if filtered_records:
            filtered_html.append({
                market_name: {
                    **market_data,
                    "records": filtered_records
                }
            })

    return {
        "type": payload.get("type"),
        "html_scrape": filtered_html,
        "api_scrape": filtered_api
    }


# # services/broadcast_service.py
# import logging
# from copy import deepcopy
# from sockets.combine_socket import user_subscriptions
# def broadcast_to_clients(sio, connected_clients, authenticated_clients, payload):
#     """
#     Broadcast rules:
#     - ADMIN → full payload
#     - USERS → only their subscribed url_ids
#     """
#     try:
        
#         # Admin room
#         sio.emit("data", {**payload, "meta": {"filtered": False, "role": "admin"}}, room="admin")

#         for sid, sub in user_subscriptions.items():
#             url_ids = set(str(u) for u in sub.get("url_ids", set()))
#             if not url_ids:
#                 continue

#             filtered_payload = {
#                 "type": payload.get("type"),
#                 "html_scrape": [],
#                 "api_scrape": []
#             }

#             # Filter html_scrape
#             for block in payload.get("html_scrape", []):
#                 for name, data in block.items():
#                     if isinstance(data, dict) and str(data.get("url_id")) in url_ids:
#                         filtered_payload["html_scrape"].append({name: deepcopy(data)})

#             # Filter api_scrape
#             for item in payload.get("api_scrape", []):
#                 if str(item.get("url_id")) in url_ids:
#                     filtered_payload["api_scrape"].append(deepcopy(item))

#             if filtered_payload["html_scrape"] or filtered_payload["api_scrape"]:
#                 # Emit to rooms user joined
#                 for url_id in url_ids:
#                     sio.emit(
#                         "data",
#                         {**filtered_payload, "meta": {"filtered": True, "role": "user"}},
#                         room=f"url:{url_id}"
#                     )


#     except Exception:
#         import logging
#         logging.error("❌ Broadcast failed", exc_info=True)



# # -------------------------------------------------
# # Helpers
# # -------------------------------------------------

# def extract_url_ids(payload):
#     ids = set()

#     for block in payload.get("html_scrape", []):
#         for _, data in block.items():
#             if isinstance(data, dict) and data.get("url_id"):
#                 ids.add(str(data["url_id"]))

#     for item in payload.get("api_scrape", []):
#         if item.get("url_id"):
#             ids.add(str(item["url_id"]))

#     return ids
# def filter_payload_by_url(payload, url_id):
#     filtered = {
#         "type": payload.get("type"),
#         "html_scrape": [],
#         "api_scrape": []
#     }

#     for block in payload.get("html_scrape", []):
#         for name, data in block.items():
#             if isinstance(data, dict) and str(data.get("url_id")) == str(url_id):
#                 filtered["html_scrape"].append({name: deepcopy(data)})

#     for item in payload.get("api_scrape", []):
#         if str(item.get("url_id")) == str(url_id):
#             filtered["api_scrape"].append(deepcopy(item))

#     return filtered

