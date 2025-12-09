# services/json_room_watcher.py
import json
import time
import threading
import logging
import os

JSON_FILE =  "scrape_domain.json"

if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w") as f:
        json.dump({}, f)
# Cache
_last_state = {}

def load_json():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def watch_json_changes(sio):
    global _last_state

    logging.info("✅ JSON watcher thread started")

    while True:
        try:
            current_data = load_json()

            # Detect changes per user
            for user_id, new_strings in current_data.items():
                old_strings = _last_state.get(user_id)

                if old_strings != new_strings:
                    logging.info(f"🔔 Change detected for user: {user_id}")

                    # Emit to user's room
                    sio.emit(
                        "string_update",
                        {
                            "user_id": user_id,
                            "strings": new_strings
                        },
                        room=user_id
                    )

            _last_state = current_data.copy()

            time.sleep(1)  # check every 1s

        except Exception as e:
            logging.error(f"JSON watcher error: {e}")
            time.sleep(2)


def start_json_watcher(sio):
    t = threading.Thread(target=watch_json_changes, args=(sio,), daemon=True)
    t.start()
