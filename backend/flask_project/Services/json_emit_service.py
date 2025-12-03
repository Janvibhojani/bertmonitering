# services/json_emit_service.py
from Services.json_room_watcher import load_json
import os
import json

JSON_FILE = "assigned_strings.json"
def emit_user_update(sio, user_id):
    print("✅ emit_user_update CALLED for user:", user_id)
    try:
        if not os.path.exists(JSON_FILE):
            print("❌ JSON file not found")
            return

        with open(JSON_FILE, "r") as f:
            all_data = json.load(f)

        user_data = all_data.get(str(user_id), {})

        print("📦 Emitting data to user:", user_id)
        print("📦 Data:", user_data)

        sio.emit("string_update", user_data, room=str(user_id))

    except Exception as e:
        print("❌ emit error:", e)
    
    # data = load_json()
    # strings = data.get(user_id, [])

    # sio.emit(
    #     "string_update",
    #     {
    #         "user_id": user_id,
    #         "strings": strings
    #     },
    #     room=user_id
    # )
