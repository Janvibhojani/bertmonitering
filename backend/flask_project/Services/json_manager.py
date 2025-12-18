

# Services/json_manager.py
import os
import json
import datetime
import threading

JSON_FILE = "scrape_domain.json"
_json_lock = threading.Lock()

def ensure_json_file():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f:
            json.dump({}, f, indent=4)
        print("✅ Created new scrape_domain.json")
        
def load_json():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                print("📁 JSON file is empty, returning empty dict")
                return {}

            return json.loads(content)

    except json.JSONDecodeError as e:
        print(f"❌ JSON corrupted at line {e.lineno}, column {e.colno}: {e.msg}")
        print("🔄 Resetting JSON file...")
        save_json({})
        return {}   # ✅ VERY IMPORTANT

    except FileNotFoundError:
        print("📁 JSON file missing. Creating new file...")
        save_json({})
        return {}

    except Exception as e:
        print(f"❌ Unexpected error loading JSON: {e}")
        save_json({})
        return {}

def normalize_name(name):
    if not name:
        return ""
    
    # Remove extra whitespace and special characters
    normalized = name.strip()
    
    # Convert to uppercase for case-insensitive comparison
    normalized = normalized.upper()
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized
def save_json(data):
    with _json_lock:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

def normalize_name(name):
    if not name:
        return ""
    return name.strip().upper()

def add_domain(url_cfg):
    data = load_json() or {}
    normalized_data = {normalize_name(n): n for n in data}
    name = url_cfg.get("name", "Unnamed")
    normalized_name = normalize_name(name)

    # Check if already exists with different casing
    existing_key = None
    for norm_key, actual_key in normalized_data.items():
        if norm_key == normalized_name:
            existing_key = actual_key
            break

    if existing_key:
        # Update existing instead of adding new
        print(f"⚠ Domain '{name}' already exists in JSON (as '{existing_key}'), updating...")
        update_domain(url_cfg)
        return

    data[name] = {
        "url_id": str(url_cfg.get("_id", "")),
        "domain": url_cfg.get("domain"),
        "scrap_from": url_cfg.get("scrap_from", "HTML"),
        "target": url_cfg.get("target", None),
        "mode": url_cfg.get("mode", "css"),
        "created_at": url_cfg.get("created_at"),
        "updated_at": url_cfg.get("updated_at"),
        "only_on_change": url_cfg.get("only_on_change", False),
        "interval_ms": url_cfg.get("interval_ms", 0),
        "inner_text": "",
        "records": []
    }
    save_json(data)
    print(f"🟢 Added new domain to JSON: {name}")
    
# Services/json_manager.py - update_records function ને fix કરો

def update_records(name, records, inner_text, cfg=None):
    try:
        data = load_json()
        url_id = str(cfg.get("_id") or cfg.get("url_id") or "").strip()

        if not url_id:
            print("❌ update_records: url_id missing")
            return

        found_key = None

        # 🔎 FIND ENTRY BY url_id (NOT NAME)
        for key, obj in data.items():
            if str(obj.get("url_id")) == url_id:
                found_key = key
                break

        if not found_key:
            print(f"⚠ No JSON entry found for url_id {url_id}, skipping record update")
            return
        if found_key != name:
            obj = data[found_key]
            del data[found_key]
            data[name] = obj
            print(f"🔁 JSON key renamed: {found_key} → {name}")
        else:
            obj = data[found_key]
            

        # ✅ UPDATE SAME OBJECT ONLY
        obj["inner_text"] = inner_text
        obj["records"] = records
        obj["updated_at"] = datetime.datetime.utcnow().isoformat()

        save_json(data)
        # print(f"📝 Records updated for url_id {url_id}")

    except Exception as e:
        print(f"❌ update_records failed: {e}")
        import traceback
        traceback.print_exc()


def update_domain(url_cfg):
    data = load_json()
    url_id = str(url_cfg.get("url_id") or url_cfg.get("_id") or "").strip()

    if not url_id:
        print("⚠ No url_id found")
        return

    found_key = None
    found_obj = None

    # 🔎 FIND EXISTING ENTRY BY url_id
    for key, obj in data.items():
        if str(obj.get("url_id")) == url_id:
            found_key = key
            found_obj = obj
            break

    name = url_cfg.get("name", found_key or "Unnamed")

    # 🗑 DELETE OLD KEY (MANDATORY)
    if found_key:
        del data[found_key]

    # 🆕 RECREATE OBJECT (OVERWRITE GUARANTEED)
    data[name] = {
        "url_id": url_id,
        "domain": url_cfg.get("domain", found_obj.get("domain") if found_obj else None),
        "type": url_cfg.get("type", found_obj.get("type") if found_obj else "HTML"),
        "records": found_obj.get("records", []) if found_obj else [],
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

    save_json(data)
    print(f"🔁 JSON reloaded by url_id: {url_id}")



def delete_domain(url_id):
    data = load_json()
    url_id = str(url_id).strip()
    delete_key = None
    
    for key, item in list(data.items()):
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
    
    
def update_api_records(name, data_text, target_cfg):
    """
    Special function for updating API target records
    """
    data = load_json()
    normalized_name = normalize_name(name)
    
    # Find existing entry
    entry_key = None
    for key, item in data.items():
        if normalize_name(key) == normalized_name:
            entry_key = key
            break
    
    if not entry_key:
        # Create new entry
        data[name] = {
            "url_id": str(target_cfg.get("_id", "")) if target_cfg else "",
            "domain": target_cfg.get("domain", "") if target_cfg else "",
            "scrap_from": "API",
            "target": None,
            "mode": None,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "only_on_change": False,
            "interval_ms": 0,
            "inner_text": "",
            "records": [{"data": data_text}]
        }
    else:
        # Update existing entry
        entry = data[entry_key]
        entry["records"] = [{"data": data_text}]
        entry["updated_at"] = datetime.datetime.utcnow().isoformat()
        data[entry_key] = entry
    
    save_json(data)
    # print(f"📡 Updated API records for {name}")