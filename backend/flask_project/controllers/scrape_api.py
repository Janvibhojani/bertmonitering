# controllers/scrape_api.py
from flask import Blueprint, jsonify, request
from datetime import datetime
import asyncio
import logging
import httpx
from playwright.async_api import async_playwright
import numpy as np
from middleware.auth_middleware import token_required
from utils.helpers import parse_gold_table, parse_table, clean_dataframe
import requests
# Create blueprint
scrape_api_bp = Blueprint("scrape_api", __name__)
logging.basicConfig(level=logging.WARNING)


# ------------------- RAW SCRAPE API --------------------------
@scrape_api_bp.route("/raw", methods=["POST"])
@token_required
def api_raw():
    """
    Scrape data using requests once and return result.
    Requires authentication via token.
    """
    payload = request.get_json()
    targets = payload.get("targets")

    if not targets or not isinstance(targets, list):
        return jsonify({"detail": "Missing or invalid 'targets' list"}), 400

    results = []

    for target in targets:
        url = target.get("url")
        if not url:
            continue
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                table_data = parse_table(resp.text)
                results.append({
                    "status": "success",
                    "url": url,
                    "text": table_data
                })
            else:
                results.append({
                    "status": "error",
                    "url": url,
                    "message": f"HTTP {resp.status_code}"
                })
        except Exception as e:
            results.append({
                "status": "error",
                "url": url,
                "message": str(e)
            })

    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    })


# ------------------- PLAYWRIGHT SCRAPE API --------------------------
@scrape_api_bp.route("/scrape", methods=["POST"])
@token_required
def api_scrape():
    """
    Scrape data using Playwright once and return result.
    Requires authentication via token.
    """
    payload = request.get_json()
    targets = payload.get("targets")

    if not targets or not isinstance(targets, list):
        return jsonify({"detail": "Invalid targets list"}), 400

    async def scrape_pages():
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-extensions",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--blink-settings=imagesEnabled=false",
                    "--disable-sync",
                    "--disable-translate",
                    "--disable-features=AudioServiceOutOfProcess",
                    "--mute-audio",
                    "--no-sandbox",
                    "--no-zygote",
                    "--single-process"
                ]
            )
            try:
                for target_cfg in targets:
                    url = target_cfg.get("url")
                    if not url:
                        continue
                    try:
                        page = await browser.new_page()
                        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(3000)

                        selector = target_cfg.get("target")
                        mode = target_cfg.get("mode", "css")

                        if selector:
                            query = (
                                f"#{selector.strip()}" if mode == "id"
                                else f".{selector.strip()}" if mode == "class"
                                else selector.strip()
                            )
                            result = await page.eval_on_selector(query, "el => el.innerText")
                        else:
                            result = await page.content()

                        if result:
                            table_data = parse_gold_table(result)
                            maindata = clean_dataframe(table_data)
                            data = maindata.replace({np.nan: None})
                            records = data.to_dict(orient="records")
                            results.append({
                                "status": "success",
                                "name": target_cfg.get("name", "Unnamed"),
                                "text": records
                            })
                    except Exception as err:
                        results.append({
                            "status": "error",
                            "url": url,
                            "message": str(err)
                        })
            finally:
                await browser.close()
        return results

    results = asyncio.run(scrape_pages())

    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    })

@scrape_api_bp.route("/status", methods=["GET"])
def api_status():
    """
    Check scraper status.
    Requires authentication via token.
    """
    # For simplicity, we just return a static status here.
    # You can enhance this to return real-time status if needed.
    return jsonify({
        "status": "idle",  # or "running"
        "message": "Scraper is currently idle."
    })
    
