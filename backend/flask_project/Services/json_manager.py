# Services/json_manager.py
import os
import json
import datetime

JSON_FILE = "scrape_domain.json"

# ----------------------------
# Ensure file exists on startup
# ----------------------------
def ensure_json_file():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f:
            json.dump({}, f, indent=4)
        print("✅ Created new scrape_domain.json")

# ----------------------------
# Load JSON
# ----------------------------
def load_json():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError:
        print("❌ JSON corrupted. Resetting file...")
        save_json({})
        return {}

    except FileNotFoundError:
        print("📁 JSON file missing. Creating new file...")
        save_json({})
        return {}



# ----------------------------
# Save JSON
# ----------------------------
def save_json(data):
    with open("scrape_Domain.json", "w") as f:
        import json
        json.dump(data, f, indent=4)
    print("✅ JSON saved")





def add_domain(url_cfg):
    data = load_json()

    url_id = str(url_cfg.get("_id", "")).strip()
    if not url_id:
        return
    name = url_cfg.get("name", "Unnamed")
    domain = url_cfg.get("domain")
    scrap_type = url_cfg.get("scrap_from", "HTML")
    target = url_cfg.get("target", None)
    mode = url_cfg.get("mode", None)
    created_at = url_cfg.get("created_at", None)
    updated_at = url_cfg.get("updated_at", None)
    only_on_change = url_cfg.get("only_on_change", False)
    interval_ms = url_cfg.get("interval_ms", 0)

    if name not in data:
        data[name] = {
            "domain": domain,
            "url_id": url_id,
            "type": scrap_type,
            "target": target,
            "mode": mode,
            "created_at": created_at,
            "updated_at": updated_at,
            "only_on_change": only_on_change,
            "interval_ms": interval_ms,
            "inner_text": "",
            "records": []
        }
        save_json(data)
        print(f"🟢 Added new domain to JSON: {name}")


# ----------------------------
# Update records via scraper
# ----------------------------


def update_records(name, records, inner_text):
    data = load_json()
    name = name.strip()

    if name not in data:
        print(f"⚠ {name} not found in JSON, creating fresh entry.")
        data[name] = {}

    # update only relevant fields
    old = data[name]
    data[name] = {
        "domain": old.get("domain", ""),
        "url_id": old.get("url_id", ""),
        "type": old.get("type", "HTML"),
        "target": old.get("target", ""),
        "mode": old.get("mode", "css"),
        "only_on_change": old.get("only_on_change", False),
        "interval_ms": old.get("interval_ms", 0),
        "inner_text": inner_text,
        "records": records
    }

    save_json(data)

def update_domain(url_cfg):
    data = load_json()

    url_id = str(url_cfg.get("_id", "")).strip()
    new_name = url_cfg.get("name", "").strip()

    if not url_id:
        print("❌ Missing URL ID")
        return

    # -----------------------------------
    # 1️⃣ Find existing entry by url_id
    # -----------------------------------
    old_key = None
    for key, item in data.items():
        if str(item.get("url_id", "")).strip() == url_id:
            old_key = key
            break

    if not old_key:
        print(f"⚠ JSON entry not found for ID: {url_id}")
        return

    # -----------------------------------
    # 2️⃣ Prevent duplicate name
    # -----------------------------------
    if new_name != old_key and new_name in data:
        print(f"❌ Name '{new_name}' already exists. Choose another name.")
        return

    old_entry = data[old_key]

    # -----------------------------------
    # 3️⃣ New updated entry (override new fields, keep old if missing)
    # -----------------------------------
    new_entry = {
        "url_id": url_id,
        "domain": url_cfg.get("url", old_entry.get("domain")),
        "type": url_cfg.get("scrap_from", old_entry.get("type")),
        "target": url_cfg.get("target", old_entry.get("target")),
        "mode": url_cfg.get("mode", old_entry.get("mode")),
        "created_at": url_cfg.get("created_at", old_entry.get("created_at")),
        "updated_at": url_cfg.get("updated_at", old_entry.get("updated_at")),
        "only_on_change": url_cfg.get("only_on_change", old_entry.get("only_on_change")),
        "interval_ms": url_cfg.get("interval_ms", old_entry.get("interval_ms")),
        "inner_text": old_entry.get("inner_text", ""),
        "records": old_entry.get("records", [])
    }

    # -----------------------------------
    # 4️⃣ Remove old key and add new one
    # -----------------------------------
    del data[old_key]
    data[new_name] = new_entry

    save_json(data)

    print(f"🟢 Old key '{old_key}' removed.")
    print(f"🟡 New key '{new_name}' created and updated.")
    print("🟢 Updated Entry:", new_entry)

    return "update successful"

# --------------------------------------------
# DELETE DOMAIN BY url_id
# --------------------------------------------
def delete_domain(url_id):
    data = load_json()
    url_id = str(url_id).strip()
    delete_key = None
    for key, item in list(data.items()):
        print(f"Checking: key={key}, url_id_in_json={item.get('url_id')}, url_id_to_delete={url_id}")
        
        if str(item.get("url_id")).strip() == url_id:
            delete_key = key
            break

    if delete_key:
        del data[delete_key]
        save_json(data)
        print(f"🔴 Deleted JSON entry: {delete_key}")
        return "delete successful"
    else:
        print(f"⚠ JSON delete failed, ID not found: {url_id}")
        return "delete failed"
