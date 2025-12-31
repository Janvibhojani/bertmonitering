# services/broadcast_service.py
import logging
from copy import deepcopy


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

        # 👤 USERS → URL-WISE PAYLOAD
        for url_id in url_ids:
            filtered_payload = filter_payload_by_url(payload, url_id)

            if not filtered_payload["html_scrape"] and not filtered_payload["api_scrape"]:
                continue

            sio.emit(
                "data",
                {
                    **filtered_payload,
                    "meta": {
                        "filtered": True,
                        "url_id": url_id,
                        "role": "user"
                        
                    }
                },
                room=f"url:{url_id}"
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
