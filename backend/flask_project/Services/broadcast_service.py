# services/broadcast_service.py
import logging


async def broadcast_to_clients(sio, connected_clients, authenticated_clients, payload):
    """
    RULES:
    - ADMIN → FULL payload
    - USER  → ONLY allocated url_id payload
    """

    try:
        url_ids = extract_url_ids(payload)
        logging.info(f"📦 url_ids found: {url_ids}")

        # 👑 ADMIN
        sio.emit("data", {
            **payload,
            "meta": {"filtered": False}
        }, room="admin")

        # 👤 USERS
        for url_id in url_ids:
            sio.emit("data", {
                **payload,
                "meta": {
                    "is_Show": True,
                    "url_id": url_id
                }
            }, room=f"url:{url_id}")

    except Exception as e:
        logging.error(f"Broadcast failed: {e}", exc_info=True)


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


# # services/broadcast_service.py
# import logging
# from Services.url_Service import fetch_user_allocated_urls

# async def broadcast_to_clients(sio, connected_clients, authenticated_clients, payload):
#     dead_clients = []

#     urls_in_payload = extract_urls_from_payload(payload)
#     logging.info(f"Extracted URLs => {urls_in_payload}")
#     for sid in list(connected_clients):
#         try:
#             user_info = authenticated_clients.get(sid)
#             if not user_info:
#                 continue

#             role = user_info.get("role")
#             user_id = user_info.get("user_id")

#             # ✅ admin gets all
#             if role == "admin":
#                 sio.emit("data", payload, room="admin")
#                 continue

#             # ✅ fetch allowed user urls
#             allocated = fetch_user_allocated_urls(user_id)
#             allowed_urls = [u["url"] for u in allocated if "url" in u]

#             # ✅ check intersection
#             if urls_in_payload.intersection(set(allowed_urls)):
#                 sio.emit("data", payload, to=sid)

#         except Exception:
#             dead_clients.append(sid)

#     for sid in dead_clients:
#         connected_clients.discard(sid)
#         authenticated_clients.pop(sid, None)


# def extract_urls_from_payload(payload):
#     urls = set()

#     # ✅ direct url
#     if "url" in payload:
#         urls.add(payload["url"])

#     # ✅ api_scrape array
#     for item in payload.get("api_scrape", []):
#         if isinstance(item, dict) and "url" in item:
#             urls.add(item["url"])

#     # ✅ html_scrape nested object
#     for block in payload.get("html_scrape", []):
#         if isinstance(block, dict):
#             for _, value in block.items():
#                 if isinstance(value, dict):
#                     domain = value.get("domain")
#                     if domain:
#                         urls.add(domain)

#     return urls
