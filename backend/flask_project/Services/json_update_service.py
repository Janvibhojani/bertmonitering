# services/json_update_service.py

import json
from socket_instance import sio
from Services.json_emit_service import emit_user_update

JSON_FILE = "assigned_strings.json"

def update_user_strings(user_id, new_strings):
    print("✅ update_user_strings CALLED for user:", user_id)
    print("✅ New data:", new_strings)
    # read old json
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}

    # update json
    data[str(user_id)] = new_strings
    

    # write back
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        

    # 🔥 NOW TRIGGER YOUR FUNCTION
    emit_user_update(sio, user_id)
