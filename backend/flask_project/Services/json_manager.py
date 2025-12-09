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
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)



def add_domain_if_missing(url_cfg):
    data = load_json()

    url_id = str(url_cfg.get("_id", "")).strip()
    if not url_id:
        return
    name = url_cfg.get("name", "Unnamed")
    domain = url_cfg.get("url")
    scrap_type = url_cfg.get("scrap_from", "HTML")
    
     # prevent duplicates by domain
    for item_name, item in data.items():
        if item["domain"] == domain:
            print(f"⚠ JSON already contains domain: {domain}")
            return
    if name not in data:
        data[name] = {
            "domain": domain,
            "url_id": url_id,
            "type": scrap_type,
            "inner_text": "",
            "records": []
            
        }
        save_json(data)
        print(f"🟢 Added new domain into JSON: {name}")


# ----------------------------
# Update records via scraper
# ----------------------------


def update_records(name, records, inner_text=""):
    data = load_json()

    # if name not in data:
    #     print(f"⚠ Cannot update records. Name not found in JSON: {name}")
    #     return  # domain not found → ignore

    data[name]["records"] = records
    data[name]["inner_text"] = inner_text
    save_json(data)


def update_domain(url_cfg):
    data = load_json()

    url_id = url_cfg.get("_id")
    new_name = url_cfg.get("name", "Unnamed")

    # find existing entry by url_id
    old_key = None
    for key, item in data.items():
        if item["url_id"] == url_id:
            old_key = key
            break

    if not old_key:
        print(f"⚠ JSON entry not found for ID: {url_id}")
        return

    # if name is changed → rename JSON key
    if new_name != old_key:
        data[new_name] = data.pop(old_key)

    # update fields
    data[new_name]["domain"] = url_cfg.get("url", data[new_name]["domain"])
    data[new_name]["type"] = url_cfg.get("scrap_from", data[new_name]["type"])

    save_json(data)
    print(f"🟡 JSON domain updated: {new_name}")

# def get_domain_by_id(url_id):
#     """
#     Return (key_name, entry) if found else (None, None)
#     """
#     data = load_json()
#     for name, entry in data.items():
#         if str(entry.get("url_id")).strip() == str(url_id).strip():
#             return name, entry
#     return None, None
# def update_records_by_id(url_id, records, inner_text=""):
#     data = load_json()

#     found_key = None

#     # Find correct JSON key (name)
#     for key, item in data.items():
#         # if str(item.get("url_id")) == url_id:
#         if str(item.get("url_id")).strip() == str(url_id).strip():

#             found_key = key
#             break

#     if not found_key:
#         print("Available IDs in JSON:")
#         for k, v in data.items():
#             print(f" - {k} → {v.get('url_id')}")
#         print(f"⚠ Cannot update records. URL ID not found: {url_id}")
#         return

#     data[found_key]["records"] = records
#     data[found_key]["inner_text"] = inner_text

#     save_json(data)
#     print(f"🟢 Updated JSON records for: {found_key}")


# --------------------------------------------
# DELETE DOMAIN BY url_id
# --------------------------------------------
def delete_domain(url_id):
    data = load_json()

    delete_key = None
    for key, item in list(data.items()):
        if str(item.get("url_id")).strip() == str(url_id).strip():
            delete_key = key
            break

    if delete_key:
        del data[delete_key]
        save_json(data)
        print(f"🔴 Deleted JSON entry: {delete_key}")
    else:
        print(f"⚠ JSON delete failed, ID not found: {url_id}")
# def delete_domain(url_id):
#     data = load_json()

#     if url_id in data:
#         del data[url_id]
#         save_json(data)
#         print(f"🔴 Deleted JSON domain object: {url_id}")
#     else:
#         print(f"⚠ Tried deleting missing JSON id: {url_id}")
# ------------------------------------------
# 2️⃣ Update JSON when a URL is updated
# ------------------------------------------
# def update_domain(url_cfg):
#     data = load_json()

#     url_id = url_cfg.get("_id")
#     if not url_id:
#         return
    
#     if url_id in data:
#         # Update only changed fields
#         data[url_id]["name"] = url_cfg.get("name", data[url_id]["name"])
#         data[url_id]["domain"] = url_cfg.get("url", data[url_id]["domain"])
#         data[url_id]["type"] = url_cfg.get("scrap_from", data[url_id]["type"])

#         save_json(data)
#         print(f"🟡 Updated JSON domain object:{url_id}")
#     else:
#         print(f"⚠JSON object not found for:  {url_id}")

