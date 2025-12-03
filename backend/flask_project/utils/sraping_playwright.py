
# ==================main code =============================


# import asyncio
# import httpx
# import json
# import logging
# import hashlib
# import numpy as np
# from utils.helpers import clean_html, parse_gold_table, parse_table, clean_dataframe
# from utils.globel import init_browser

# # Globals
# html_pages = []
# prev_values = {}
# saved_once = {}

# async def scrape_combined(browser, targets, stop_event, send_func, reload_interval=60):
#     """
#     ⚡ NO-SKIP Updated Unified Scraping Loop
#     - Captures every DOM update (even when innerText same)
#     - 0.1s precision
#     - No delays, no missed updates
#     """

#     global html_pages, prev_values, saved_once
#     html_pages = []
#     prev_values = {}
#     saved_once = {t["url"]: False for t in targets}

#     api_targets = [t for t in targets if t.get("scrap_from") == "API"]
#     html_targets = [t for t in targets if t.get("scrap_from") != "API"]

#     combined_buffer = {"html_scrape": [], "api_scrape": []}

#     # Create new browser context
#     try:
#         context = await browser.new_context()
#         logging.info("✅ New browser context created.")
#     except Exception as e:
#         await send_func({"status": "error", "message": f"Browser init failed: {str(e)}"})
#         return

#     async with httpx.AsyncClient(timeout=10) as client:

#         # ------------------------------
#         # Open HTML pages
#         # ------------------------------
#         for target_cfg in html_targets:
#             url = target_cfg["url"]
#             try:
#                 page = await context.new_page()
#                 await page.goto(url, timeout=60000, wait_until="domcontentloaded")
#                 html_pages.append((target_cfg, page))
#                 prev_values[url] = None
#                 logging.info(f"✅ Page opened: {url}")
#             except Exception as e:
#                 await send_func({
#                     "url": url,
#                     "status": "error",
#                     "message": f"Failed to open: {str(e)}"
#                 })

#         # ------------------------------
#         # Save first-time data
#         # ------------------------------
#         async def save_once(url, data):
#             if saved_once.get(url, False):
#                 return
#             try:
#                 with open("output.txt", "r", encoding="utf-8") as f:
#                     existing = json.load(f)
#             except (FileNotFoundError, json.JSONDecodeError):
#                 existing = {}

#             existing[url] = data
#             with open("output.txt", "w", encoding="utf-8") as f:
#                 json.dump(existing, f, ensure_ascii=False, indent=2)

#             saved_once[url] = True
#             logging.info(f"💾 Saved first result for {url}")

#         # ------------------------------
#         # Format JSON helper
#         # ------------------------------
#         def format_custom_json(target_cfg, records):
#             name = target_cfg.get("name", "Unnamed")
#             domain = target_cfg.get("url")

#             return {
#                 name: {
#                     "domain": domain,
#                     "records": records
#                 }
#             }

#         # ------------------------------
#         # 🔥 NO-SKIP HTML WATCHER
#         # ------------------------------
#         async def watch_page(target_cfg, page):
#             url = target_cfg["url"]
#             selector = target_cfg.get("target")
#             mode = target_cfg.get("mode", "css")
#             only_on_change = target_cfg.get("only_on_change", True)

#             query = (
#                 f"#{selector.strip()}" if mode == "id"
#                 else f".{selector.strip()}" if mode == "class"
#                 else selector.strip()
#             )

#             def hash_text(text):
#                 return hashlib.md5(text.encode("utf-8")).hexdigest()

#             logging.info(f"🔍 NO-SKIP Watching: {url} ({query})")
#             prev_hash = None

#             # Wait until selector exists
#             try:
#                 await page.wait_for_selector(query, timeout=10000)
#             except Exception:
#                 logging.warning(f"⚠ Selector not found for {url}: {query}")

#             while not stop_event.is_set():
#                 try:
#                     inner_text = await page.eval_on_selector(query, "el => el.innerText")
#                     inner_html = await page.eval_on_selector(query, "el => el.innerHTML")

#                     if inner_text is None and inner_html is None:
#                         await asyncio.sleep(0.1)
#                         continue

#                     combined = (inner_text or "") + (inner_html or "")
#                     new_hash = hash_text(combined)

#                     if not only_on_change or new_hash != prev_hash:
#                         prev_hash = new_hash

#                         table_data = parse_gold_table(inner_text)
#                         df = clean_dataframe(table_data)
#                         df = df.replace({np.nan: None})
#                         records = df.to_dict(orient="records")

#                         await save_once(url, {"records": records})
#                         custom_json = format_custom_json(target_cfg, records)

#                         # Append instead of overwrite
#                         combined_buffer["html_scrape"].append(custom_json)

#                         await send_func({
#                             "type": "combined_scrape",
#                             "data": custom_json
#                         })

#                     await asyncio.sleep(0.1)
#                 except Exception as e:
#                     logging.error(f"Watcher error [{url}]: {str(e)}")
#                     await asyncio.sleep(0.1)
#                     continue

#         # Start watchers
#         watcher_tasks = [
#             asyncio.create_task(watch_page(cfg, page))
#             for cfg, page in html_pages
#         ]

#         # ------------------------------
#         # API Polling
#         # ------------------------------
#         while not stop_event.is_set():
#             for target in api_targets:
#                 url = target["url"]
#                 name = target.get("name", "Unnamed")

#                 try:
#                     resp = await client.get(url)

#                     if resp.status_code == 200:
#                         table_data = parse_table(resp.text)
#                         await save_once(url, table_data)

#                         api_json = {
#                             name: {
#                                 "domain": url,
#                                 "records": table_data
#                             }
#                         }

#                         # Append instead of overwrite
#                         combined_buffer["api_scrape"].append(api_json)

#                         await send_func({
#                             "type": "combined_scrape",
#                             "html_scrape": combined_buffer["html_scrape"],
#                             "api_scrape": combined_buffer["api_scrape"],
#                         })

#                     else:
#                         await send_func({
#                             "url": url,
#                             "status": "error",
#                             "message": f"HTTP {resp.status_code}"
#                         })

#                 except Exception as e:
#                     await send_func({
#                         "url": url,
#                         "status": "error",
#                         "message": str(e)
#                     })

#             await asyncio.sleep(3)

#         # ------------------------------
#         # Cleanup
#         # ------------------------------
#         for t in watcher_tasks:
#             try:
#                 t.cancel()
#             except Exception:
#                 pass

#         await context.close()
#         logging.info("🧹 Browser context closed.")
# =================main code with innerhtml============================

# # scraping_playwright.py
# import asyncio
# import httpx
# import json
# import logging
# import hashlib
# import numpy as np
# from utils.helpers import clean_html, parse_gold_table, parse_table, clean_dataframe
# from utils.globel import init_browser

# # Globals
# html_pages = []
# prev_values = {}
# saved_once = {}

# async def scrape_combined(browser, targets, stop_event, send_func, reload_interval=60):
#     """
#     ⚡ NO-SKIP Updated Unified Scraping Loop
#     - Captures every DOM update (even when innerText same)
#     - 0.1s precision
#     - No delays, no missed updates
#     """

#     global html_pages, prev_values, saved_once
#     html_pages = []
#     prev_values = {}
#     saved_once = {t["url"]: False for t in targets}

#     api_targets = [t for t in targets if t.get("scrap_from") == "API"]
#     html_targets = [t for t in targets if t.get("scrap_from") != "API"]

#     combined_buffer = {"html_scrape": [], "api_scrape": []}

#     # Create new browser context
#     try:
#         context = await browser.new_context()
#         logging.info("✅ New browser context created.")
#     except Exception as e:
#         await send_func({"status": "error", "message": f"Browser init failed: {str(e)}"})
#         return

#     async with httpx.AsyncClient(timeout=10) as client:

#         # Open HTML pages
#         for target_cfg in html_targets:
#             url = target_cfg["url"]
#             try:
#                 page = await context.new_page()
#                 # await page.goto(url, timeout=60000, wait_until="domcontentloaded")
#                 await page.goto(url, wait_until="commit")
#                 html_pages.append((target_cfg, page))
#                 prev_values[url] = None
#                 logging.info(f"✅ Page opened: {url}")
#             except Exception as e:
#                 await send_func({
#                     "url": url,
#                     "status": "error",
#                     "message": f"Failed to open: {str(e)}"
#                 })

#         # Save first-time data
#         async def save_once(url, data):
#             if saved_once.get(url, False):
#                 return
#             try:
#                 with open("output.txt", "r", encoding="utf-8") as f:
#                     existing = json.load(f)
#             except (FileNotFoundError, json.JSONDecodeError):
#                 existing = {}

#             existing[url] = data
#             with open("output.txt", "w", encoding="utf-8") as f:
#                 json.dump(existing, f, ensure_ascii=False, indent=2)

#             saved_once[url] = True
#             logging.info(f"💾 Saved first result for {url}")
            
#         # Format JSON helper
#         def format_custom_json(target_cfg, records, inner_text):
#             name = target_cfg.get("name", "Unnamed")
#             domain = target_cfg.get("url")

#             return {
#                 name: {
#                     "domain": domain,
#                     "inner_text": inner_text,
#                     "records": records
#                 }
#             }


#         # ------------------------------
#         # 🔥 NO-SKIP HTML WATCHER
#         # ------------------------------
#         async def watch_page(target_cfg, page):
#             url = target_cfg["url"]
#             selector = target_cfg.get("target")
#             mode = target_cfg.get("mode", "css")
#             only_on_change = target_cfg.get("only_on_change", True)

#             query = (
#                 f"#{selector.strip()}" if mode == "id"
#                 else f".{selector.strip()}" if mode == "class"
#                 else selector.strip()
#             )

#             def hash_text(text):
#                 return hashlib.md5(text.encode("utf-8")).hexdigest()

#             logging.info(f"🔍 NO-SKIP Watching: {url} ({query})")

#             prev_hash = None

#             while not stop_event.is_set():
#                 try:
#                     # ⭐ Capture BOTH content forms (no skip)
#                     inner_text = await page.eval_on_selector(query, "el => el.innerText")
#                     inner_html = await page.eval_on_selector(query, "el => el.innerHTML")

#                     # Retry fast if selector missing
#                     if inner_text is None and inner_html is None:
#                         await asyncio.sleep(0.1)
#                         continue

#                     combined = (inner_text or "") + (inner_html or "")
#                     new_hash = hash_text(combined)

#                     # ⭐ Guaranteed detection of every update
#                     if not only_on_change or new_hash != prev_hash:
#                         prev_hash = new_hash

#                         table_data = parse_gold_table(inner_text)
#                         df = clean_dataframe(table_data)
#                         df = df.replace({np.nan: None})
#                         records = df.to_dict(orient="records")

#                         await save_once(url, {"records": records})

#                         # html_entry = {
#                         #     "status": "success",
#                         #     "name": target_cfg.get("name", "Unnamed"),
#                         #     "url": url,
#                         #     "text": records,
#                         #     "inner_text": inner_text,
#                         # }
#                         html_entry = format_custom_json(target_cfg, records, inner_text)
#                         combined_buffer["html_scrape"] = [html_entry]

#                         await send_func({
#                             "type": "combined_scrape",
#                             "html_scrape": combined_buffer["html_scrape"],
#                             "api_scrape": combined_buffer["api_scrape"],
#                         })

#                     # 0.1s = No update skipping
#                     await asyncio.sleep(0.1)

#                 except:
#                     await asyncio.sleep(0.1)
#                     continue

#         # Start watchers
#         watcher_tasks = [asyncio.create_task(watch_page(cfg, page)) for cfg, page in html_pages]

#         # ------------------------------
#         # API Polling
#         # ------------------------------
#         while not stop_event.is_set():
#             for target in api_targets:
#                 url = target["url"]
#                 name = target.get("name", "Unnamed")

#                 try:
#                     resp = await client.get(url)

#                     if resp.status_code == 200:
#                         table_data = parse_table(resp.text)
#                         await save_once(url, table_data)

#                         api_entry = {
#                             "status": "success",
#                             "name": name,
#                             "url": url,
#                             "text": table_data,
#                         }

#                         combined_buffer["api_scrape"] = [api_entry]

#                         await send_func({
#                             "type": "combined_scrape",
#                             "html_scrape": combined_buffer["html_scrape"],
#                             "api_scrape": combined_buffer["api_scrape"],
#                         })

#                     else:
#                         await send_func({
#                             "url": url,
#                             "status": "error",
#                             "message": f"HTTP {resp.status_code}"
#                         })

#                 except Exception as e:
#                     await send_func({
#                         "url": url,
#                         "status": "error",
#                         "message": str(e)
#                     })

#             await asyncio.sleep(3)

#         # Cleanup
#         for t in watcher_tasks:
#             t.cancel()
#         await context.close()
#         logging.info("🧹 Browser context closed.")


#  ama ae che ke badhi webpage aek sathe load tay che
# sraping_playwright.py
import asyncio
import httpx
import json
import logging
import hashlib
import numpy as np
from utils.helpers import clean_html, parse_gold_table, parse_table, clean_dataframe
from utils.globel import init_browser

html_pages = []
prev_values = {}
saved_once = {}


async def scrape_combined(browser, targets, stop_event, send_func, reload_interval=60):
    """
    Optimized + Ordered Startup:
    - Open all pages in parallel for speed
    - THEN start watchers sequentially (preserves OLD timing/sequence)
    - Keeps API polling loop and combined_buffer behaviour
    """

    global html_pages, prev_values, saved_once

    html_pages = []
    prev_values = {}
    saved_once = {t["url"]: False for t in targets}

    api_targets = [t for t in targets if t.get("scrap_from") == "API"]
    html_targets = [t for t in targets if t.get("scrap_from") != "API"]

    combined_buffer = {"html_scrape": [], "api_scrape": []}

    # Create new browser context
    try:
        context = await browser.new_context()
        logging.info("✅ Browser context created.")
    except Exception as e:
        await send_func({"status": "error", "message": f"Browser init failed: {str(e)}"})
        return

    async with httpx.AsyncClient(timeout=10) as client:

        # -------------------------
        # Format JSON helper
        # -------------------------
        def format_custom_json(target_cfg, records, inner_text):
            name = target_cfg.get("name", "Unnamed")
            domain = target_cfg.get("url")

            return {
                name: {
                    "domain": domain,
                    "type": target_cfg.get("scrap_from", "HTML"),
                    "inner_text": inner_text,
                    "records": records
                }
            }

        # -------------------------
        # Save first-time data
        # -------------------------
        async def save_once(url, data):
            if saved_once.get(url, False):
                return
            try:
                with open("output.txt", "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing = {}

            existing[url] = data
            with open("output.txt", "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

            saved_once[url] = True
            logging.info(f"💾 Saved first result for {url}")

        # -------------------------
        # Watcher function (unchanged logic)
        # -------------------------
        async def watch_page(target_cfg, page):
            url = target_cfg["url"]
            selector = target_cfg.get("target")
            mode = target_cfg.get("mode", "css")
            only_on_change = target_cfg.get("only_on_change", True)

            query = (
                f"#{selector.strip()}" if mode == "id"
                else f".{selector.strip()}" if mode == "class"
                else selector.strip()
            )

            def hash_text(text):
                return hashlib.md5(text.encode("utf-8")).hexdigest()

            prev_hash = None

            logging.info(f"🔍 Watching live DOM: {url} ({query})")

            while not stop_event.is_set():
                try:
                    inner_text = await page.eval_on_selector(query, "el => el.innerText")
                    inner_html = await page.eval_on_selector(query, "el => el.innerHTML")

                    if inner_text is None and inner_html is None:
                        await asyncio.sleep(0.5)
                        continue

                    combined = (inner_text or "") + (inner_html or "")
                    new_hash = hash_text(combined)

                    if not only_on_change or new_hash != prev_hash:
                        prev_hash = new_hash

                        table_data = parse_gold_table(inner_text)
                        df = clean_dataframe(table_data)
                        df = df.replace({np.nan: None})
                        records = df.to_dict(orient="records")

                        await save_once(url, {"records": records})

                        entry = format_custom_json(target_cfg, records, inner_text)
                        combined_buffer["html_scrape"] = [entry]

                        await send_func({
                            "type": "combined_scrape",
                            "html_scrape": combined_buffer["html_scrape"],
                            "api_scrape": combined_buffer["api_scrape"],
                        })

                except Exception as e:
                    # don't spam logs, but record occasionally if needed
                    # logging.debug(f"watch_page error for {url}: {e}")
                    await asyncio.sleep(0.1)
                    continue

                await asyncio.sleep(0.1)

        # ----------------------------------------
        # PARALLEL PAGE OPEN (fast) -> returns (cfg, page) pairs
        # ----------------------------------------
        async def open_page_pair(target_cfg):
            url = target_cfg["url"]
            try:
                page = await context.new_page()
                # Using 'commit' to match OLD timing behavior (fastest start)
                await page.goto(url, wait_until="commit", timeout=30000)
                logging.info(f"⚡ Page opened: {url}")
                return (target_cfg, page)
            except Exception as e:
                await send_func({
                    "url": url,
                    "status": "error",
                    "message": f"Failed to open: {e}"
                })
                return None

        # Launch open_page_pair tasks in parallel
        open_tasks = [open_page_pair(cfg) for cfg in html_targets]
        opened_results = await asyncio.gather(*open_tasks)

        # Filter only successfully opened pages and store in html_pages list
        html_pages = [res for res in opened_results if res]
        for cfg, page in html_pages:
            prev_values[cfg["url"]] = None

        logging.info(f"✅ Opened pages: {len(html_pages)}")

        # ----------------------------------------
        # START WATCHERS SEQUENTIALLY (OLD timing)
        # ----------------------------------------
        watcher_tasks = []
        for cfg, page in html_pages:
            # start watcher for one page, then move to next — preserves order/timing
            task = asyncio.create_task(watch_page(cfg, page))
            watcher_tasks.append(task)
            logging.info(f"▶ Watcher started (sequential): {cfg['url']}")
            # no simultaneous start spikes: small sleep to preserve ordering (can be 0)
            await asyncio.sleep(0)  

        logging.info(f"🔥 Total Watchers Active: {len(watcher_tasks)}")

        # ----------------------------------------
        # API Polling Loop
        # ----------------------------------------
        try:
            while not stop_event.is_set():
                for target in api_targets:
                    url = target["url"]
                    name = target.get("name", "Unnamed")

                    try:
                        resp = await client.get(url)

                        if resp.status_code == 200:
                            table_data = parse_table(resp.text)
                            await save_once(url, table_data)

                            api_entry = {
                                "status": "success",
                                "name": name,
                                "url": url,
                                "text": table_data,
                            }

                            combined_buffer["api_scrape"] = [api_entry]

                            await send_func({
                                "type": "combined_scrape",
                                "html_scrape": combined_buffer["html_scrape"] or [],
                                "api_scrape": combined_buffer["api_scrape"],
                            })

                        else:
                            await send_func({
                                "url": url,
                                "status": "error",
                                "message": f"HTTP {resp.status_code}"
                            })

                    except Exception as e:
                        await send_func({
                            "url": url,
                            "status": "error",
                            "message": str(e)
                        })

                await asyncio.sleep(3)

        finally:
            # CLEANUP
            for t in watcher_tasks:
                try:
                    t.cancel()
                except:
                    pass

            # close pages explicitly (best practice)
            for _, page in html_pages:
                try:
                    await page.close()
                except:
                    pass

            await context.close()
            logging.info("🧹 Browser context closed.")
