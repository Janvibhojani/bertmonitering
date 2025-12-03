import os
import json

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
    ensure_json_file()
    with open(JSON_FILE, "r") as f:
        return json.load(f)


# ----------------------------
# Save JSON
# ----------------------------
def save_json(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ----------------------------
# Add domain from DB format
# ----------------------------
def add_domain_if_missing(url_cfg):
    data = load_json()
    name = url_cfg.get("name", "Unnamed")
    domain = url_cfg.get("url")
    scrap_type = url_cfg.get("scrap_from", "HTML")

    if name not in data:
        data[name] = {
            "domain": domain,
            "type": scrap_type,
            "records": [],
            "inner_text": ""
        }
        save_json(data)
        print(f"🟢 Added new domain into JSON: {name}")


# ----------------------------
# Update records via scraper
# ----------------------------
def update_records(name, records, inner_text=""):
    data = load_json()

    if name not in data:
        return  # domain not found → ignore

    data[name]["records"] = records
    data[name]["inner_text"] = inner_text

    save_json(data)
