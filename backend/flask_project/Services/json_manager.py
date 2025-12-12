# # Services/json_manager.py
# import os
# import json
# import datetime

# JSON_FILE = "scrape_domain.json"   # <- unified filename

# # ----------------------------
# # Ensure file exists on startup
# # ----------------------------
# def ensure_json_file():
#     if not os.path.exists(JSON_FILE):
#         with open(JSON_FILE, "w") as f:
#             json.dump({}, f, indent=4)
#         print("✅ Created new scrape_domain.json")

# # ----------------------------
# # Load JSON
# # ----------------------------
# def load_json():
#     try:
#         with open(JSON_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)

#     except json.JSONDecodeError:
#         print("❌ JSON corrupted. Resetting file...")
#         save_json({})
#         return {}

#     except FileNotFoundError:
#         print("📁 JSON file missing. Creating new file...")
#         save_json({})
#         return {}

# # ----------------------------
# # Save JSON
# # ----------------------------
# def save_json(data):
#     # use JSON_FILE constant rather than a different filename
#     with open(JSON_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, default=str)
#     # print("✅ JSON saved")

# # ----------------------------
# # Domain helpers (keeps same logical behaviour)
# # ----------------------------
# def add_domain(url_cfg):
#     data = load_json()
#     normalized_data = {normalize_name(n): n for n in data}
#     name = url_cfg.get("name", "Unnamed")
#     normalized_name = normalize_name(name)

#     if normalized_name not in normalized_data:
#         data[name] = {
#             "url_id": str(url_cfg.get("_id", "")),
#             "domain": url_cfg.get("domain"),
#             "scrap_from": url_cfg.get("scrap_from", "HTML"),
#             "target": url_cfg.get("target", None),
#             "mode": url_cfg.get("mode", "css"),
#             "created_at": url_cfg.get("created_at"),
#             "updated_at": url_cfg.get("updated_at"),
#             "only_on_change": url_cfg.get("only_on_change", False),
#             "interval_ms": url_cfg.get("interval_ms", 0),
#             "inner_text": "",
#             "records": []
#         }
#         save_json(data)
#         print(f"🟢 Added new domain to JSON: {name}")


# def update_records(name, records, inner_text, cfg=None):
#     data = load_json()
#     normalized_data = {normalize_name(n): n for n in data}  # normalize all keys
#     normalized_name = normalize_name(name)

#     if normalized_name not in normalized_data:
#         if not cfg:
#             print(f"⚠ {name} not found & no cfg provided, skipping")
#             return

#         data[name] = {
#             "url_id": str(cfg.get("_id", "")),
#             "domain": cfg.get("domain", ""),
#             "scrap_from": cfg.get("scrap_from", "HTML"),
#             "target": cfg.get("target", ""),
#             "mode": cfg.get("mode", "css"),
#             "created_at": cfg.get("created_at"),
#             "updated_at": cfg.get("updated_at"),
#             "only_on_change": cfg.get("only_on_change", False),
#             "interval_ms": cfg.get("interval_ms", 0),
#             "inner_text": "",
#             "records": []
#         }

#     # update using actual key from normalized_data if exists
#     key_to_use = normalized_data.get(normalized_name, name)
#     entry = data[key_to_use]
#     entry["inner_text"] = inner_text
#     entry["records"] = records
#     entry["updated_at"] = datetime.datetime.utcnow().isoformat()
#     data[key_to_use] = entry
#     save_json(data)


# def update_domain(url_cfg):
#     data = load_json()

#     name = url_cfg.get("name", "").strip()
#     if not name:
#         print("⚠ No name found in url_cfg")
#         return

#     def sanitize(obj):
#         if isinstance(obj, dict):
#             return {k: sanitize(v) for k, v in obj.items()}
#         if isinstance(obj, list):
#             return [sanitize(i) for i in obj]
#         if isinstance(obj, datetime.datetime):
#             return obj.isoformat()
#         return obj

#     url_id = str(url_cfg.get("_id", "")).strip()

#     old = data.get(name, {})
#     data[name] = {
#         "url_id": url_id,
#         "domain": url_cfg.get("domain"),
#         "scrap_from": url_cfg.get("scrap_from", old.get("scrap_from", "HTML")),

#         "target": url_cfg.get("target", old.get("target", "")),
#         "mode": url_cfg.get("mode", old.get("mode", "css")),

#         "created_at": url_cfg.get("created_at", old.get("created_at")),
#         "updated_at": url_cfg.get("updated_at", datetime.datetime.utcnow().isoformat()),

#         "only_on_change": url_cfg.get("only_on_change", old.get("only_on_change", False)),
#         "interval_ms": url_cfg.get("interval_ms", old.get("interval_ms", 0)),

#         "inner_text": old.get("inner_text", ""),
#         "records": old.get("records", [])
#     }

#     sanitized = sanitize(data)
#     save_json(sanitized)

#     print(f"🟡 Updated domain in JSON: {name}")


# def delete_domain(url_id):
#     data = load_json()
#     url_id = str(url_id).strip()
#     delete_key = None
#     for key, item in list(data.items()):
#         if str(item.get("url_id")).strip() == url_id:
#             delete_key = key
#             break

#     if delete_key:
#         del data[delete_key]
#         save_json(data)
#         print(f"🔴 Deleted JSON entry: {delete_key}")
#         return "delete successful"
#     else:
#         print(f"⚠ JSON delete failed, ID not found: {url_id}")
#         return "delete failed"


# def normalize_name(name):
#     if not name:
#         return ""
#     return name.strip().upper()

# Services/json_manager.py
import os
import json
import datetime

JSON_FILE = "scrape_domain.json"

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
                
            data = json.loads(content)
            # print(f"📖 Loaded JSON with {len(data)} entries")
            return data

    except json.JSONDecodeError as e:
        print(f"❌ JSON corrupted at line {e.lineno}, column {e.colno}: {e.msg}")
        print("🔄 Resetting JSON file...")
        
        
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

# def load_json():
#     try:
#         with open(JSON_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except json.JSONDecodeError:
#         print("❌ JSON corrupted. Resetting file...")
#         save_json({})
#         return {}
#     except FileNotFoundError:
#         print("📁 JSON file missing. Creating new file...")
#         save_json({})
#         return {}

def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)

def normalize_name(name):
    if not name:
        return ""
    return name.strip().upper()

def add_domain(url_cfg):
    data = load_json()
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
        
        # Debug: Print what we're looking for
        
        # First try exact match
        if name in data:
            actual_key = name
            # print(f"   ✅ Exact match found: '{actual_key}'")
        else:
            # Try case-insensitive match
            normalized_name = normalize_name(name)
            actual_key = None
            
            for key in data.keys():
                if normalize_name(key) == normalized_name:
                    actual_key = key
                    print(f"   ✅ Case-insensitive match found: '{key}' -> '{actual_key}'")
                    break
            
            if not actual_key:
                print(f"   ⚠ No match found for '{name}' in JSON")
                
                if cfg:
                    # Create new entry
                    actual_key = name
                    data[actual_key] = {
                        "url_id": str(cfg.get("_id", "")) if cfg else "",
                        "domain": cfg.get("domain", "") if cfg else "",
                        "scrap_from": cfg.get("scrap_from", "HTML") if cfg else "HTML",
                        "target": cfg.get("target", "") if cfg else "",
                        "mode": cfg.get("mode", "css") if cfg else "css",
                        "created_at": cfg.get("created_at", datetime.datetime.utcnow().isoformat()) if cfg else datetime.datetime.utcnow().isoformat(),
                        "updated_at": cfg.get("updated_at", datetime.datetime.utcnow().isoformat()) if cfg else datetime.datetime.utcnow().isoformat(),
                        "only_on_change": cfg.get("only_on_change", False) if cfg else False,
                        "interval_ms": cfg.get("interval_ms", 0) if cfg else 0,
                        "inner_text": "",
                        "records": []
                    }
                    print(f"   🆕 Created new entry: '{actual_key}'")
                else:
                    print(f"   ❌ No cfg provided, cannot create entry")
                    return

        # Now update the entry
        if actual_key and actual_key in data:
            entry = data[actual_key]
            entry["inner_text"] = inner_text
            entry["records"] = records
            entry["updated_at"] = datetime.datetime.utcnow().isoformat()
            data[actual_key] = entry
            save_json(data)
            # print(f"   📝 Updated records for '{actual_key}'")
        else:
            print(f"   ❌ Error: actual_key '{actual_key}' not in data")
            
    except Exception as e:
        print(f"❌ Error in update_records for '{name}': {e}")
        import traceback
        traceback.print_exc()


def update_domain(url_cfg):
    data = load_json()
    name = url_cfg.get("name", "").strip()
    if not name:
        print("⚠ No name found in url_cfg")
        return

    url_id = str(url_cfg.get("_id", "")).strip()
    
    # Find existing entry (case-insensitive)
    existing_key = None
    for key, item in data.items():
        if normalize_name(key) == normalize_name(name):
            existing_key = key
            break

    if existing_key:
        # Update existing entry
        old = data[existing_key]
        data[existing_key] = {
            "url_id": url_id,
            "domain": url_cfg.get("domain", old.get("domain", "")),
            "scrap_from": url_cfg.get("scrap_from", old.get("scrap_from", "HTML")),
            "target": url_cfg.get("target", old.get("target", "")),
            "mode": url_cfg.get("mode", old.get("mode", "css")),
            "created_at": url_cfg.get("created_at", old.get("created_at")),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "only_on_change": url_cfg.get("only_on_change", old.get("only_on_change", False)),
            "interval_ms": url_cfg.get("interval_ms", old.get("interval_ms", 0)),
            "inner_text": old.get("inner_text", ""),
            "records": old.get("records", [])
        }
        print(f"🟡 Updated domain in JSON: {existing_key}")
    else:
        # Create new entry
        data[name] = {
            "url_id": url_id,
            "domain": url_cfg.get("domain"),
            "scrap_from": url_cfg.get("scrap_from", "HTML"),
            "target": url_cfg.get("target", ""),
            "mode": url_cfg.get("mode", "css"),
            "created_at": url_cfg.get("created_at"),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "only_on_change": url_cfg.get("only_on_change", False),
            "interval_ms": url_cfg.get("interval_ms", 0),
            "inner_text": "",
            "records": []
        }
        print(f"🟢 Added new domain in JSON (update_domain): {name}")
    
    save_json(data)

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
    print(f"📡 Updated API records for {name}")