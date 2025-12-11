# Services/json_manager.py
import os
import json
import datetime

JSON_FILE = "scrape_domain.json"   # <- unified filename

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
    # use JSON_FILE constant rather than a different filename
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    # print("✅ JSON saved")

# ----------------------------
# Domain helpers (keeps same logical behaviour)
# ----------------------------
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
            "url_id": url_id,
            "domain": domain,
            "scrap_from": scrap_type,
            "target": target,
            "mode": mode or "css",
            "created_at": created_at,
            "updated_at": updated_at,
            "only_on_change": only_on_change,
            "interval_ms": interval_ms,
            "inner_text": "",
            "records": []
        }
        save_json(data)
        print(f"🟢 Added new domain to JSON: {name}")

def update_records(name, records, inner_text):
    data = load_json()
    name = name.strip()
    if name not in data:
        print(f"⚠ {name} not found in JSON, creating fresh entry.")
        data[name] = {
            "url_id": "",
            "domain": "",
            "scrap_from": "HTML",
            "target": "",
            "mode": "css",
            "created_at": None,
            "updated_at": None,
            "only_on_change": False,
            "interval_ms": 0,
            "inner_text": "",
            "records": []
        }

    # update only relevant fields (keep metadata intact)
    entry = data[name]
    entry["inner_text"] = inner_text
    entry["records"] = records
    entry["updated_at"] = datetime.datetime.utcnow().isoformat()
    data[name] = entry
    save_json(data)

def update_domain(url_cfg):
    data = load_json()

    name = url_cfg.get("name", "").strip()
    if not name:
        print("⚠ No name found in url_cfg")
        return

    url_id = str(url_cfg.get("_id", "")).strip()

    # Build/overwrite the entry for this name (keep last scraped data if present)
    old = data.get(name, {})
    data[name] = {
        "url_id": url_id,
        "domain": url_cfg.get("domain"),
        "scrap_from": url_cfg.get("scrap_from", old.get("scrap_from", "HTML")),
        "target": url_cfg.get("target", old.get("target", "")),
        "mode": url_cfg.get("mode", old.get("mode", "css")),
        "created_at": url_cfg.get("created_at", old.get("created_at")),
        "updated_at": url_cfg.get("updated_at", datetime.datetime.utcnow().isoformat()),
        "only_on_change": url_cfg.get("only_on_change", old.get("only_on_change", False)),
        "interval_ms": url_cfg.get("interval_ms", old.get("interval_ms", 0)),
        "inner_text": old.get("inner_text", ""),
        "records": old.get("records", [])
    }

    save_json(data)
    print(f"🟡 Updated domain in JSON: {name}")

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
