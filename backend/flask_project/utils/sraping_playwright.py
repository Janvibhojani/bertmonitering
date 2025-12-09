

#  ama ae che ke badhi webpage aek sathe load tay che
# sraping_playwright.py
import asyncio
import httpx
import json
import logging
import hashlib
import numpy as np
from Services.json_manager import update_records
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

                        # await save_once(url, {"records": records})
                        update_records(name, records, inner_text)
                        entry = {
                            name: {
                                "domain": url,
                                "type": target_cfg.get("scrap_from", "HTML"),
                                "inner_text": inner_text,
                                "records": records
                            }
                        }
                        combined_buffer["html_scrape"] = [entry]

                      

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
            await asyncio.sleep(0.1)  

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
                            # await save_once(url, table_data)
                            update_records(name, table_data, "")
                            print("URL ID => ", target.get("_id"))
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

# # sraping_playwright.py
# import asyncio
# import httpx
# import json
# import logging
# import hashlib
# import numpy as np
# from utils.helpers import clean_html, parse_gold_table, parse_table, clean_dataframe
# from utils.globel import init_browser
# from Services.json_manager import update_records_by_id

# # Module-level state (kept minimal)
# html_pages = []
# prev_values = {}
# saved_once = {}

# # -----------------------
# # Helper: hashing
# # -----------------------
# def _hash_text(text: str) -> str:
#     return hashlib.md5(text.encode("utf-8")).hexdigest()

# # -----------------------
# # Reusable watcher: starts watching a single page for a target_cfg
# # -----------------------
# async def start_watch_for_cfg(target_cfg: dict, page, stop_event: asyncio.Event, send_func):
#     """
#     Watch a single Playwright page for changes and send updates using send_func.
#     This function can be called from inside scrape_combined OR externally (for single-URL reload).
#     Args:
#         target_cfg: dict containing target configuration (must include url, _id, target, mode, only_on_change etc.)
#         page: Playwright page object already navigated to target_cfg['url']
#         stop_event: asyncio.Event to signal shutdown
#         send_func: async callable(payload) to send combined payloads to socket clients
#     """
#     selector = target_cfg.get("target")
#     mode = target_cfg.get("mode", "css")
#     only_on_change = target_cfg.get("only_on_change", True)
#     name = target_cfg.get("name", "Unnamed")

#     if not selector:
#         logging.warning(f"No selector defined for target '{name}' ({target_cfg.get('url')}). Skipping watcher.")
#         return

#     query = (
#         f"#{selector.strip()}" if mode == "id"
#         else f".{selector.strip()}" if mode == "class"
#         else selector.strip()
#     )

#     prev_hash = None

#     # small helper to format payload
#     def format_custom_json(cfg, records, inner_text):
#         nm = cfg.get("name", "Unnamed")
#         domain = cfg.get("url")
#         url_id = str(cfg.get("_id", ""))
#         # print(f"📤 Sending update for {nm} ({domain}), records: {len(records)}")
#         return {
#             nm: {
#                 "domain": domain,
#                 "url_id": url_id,
#                 "type": cfg.get("scrap_from", "HTML"),
#                 "inner_text": inner_text,
#                 "records": records
#             }
#         }

#     while not stop_event.is_set():
#         try:
#             inner_text = await page.eval_on_selector(query, "el => el.innerText")
#             inner_html = await page.eval_on_selector(query, "el => el.innerHTML")

#             if inner_text is None and inner_html is None:
#                 await asyncio.sleep(0.5)
#                 continue

#             combined = (inner_text or "") + (inner_html or "")
#             new_hash = _hash_text(combined)

#             if (not only_on_change) or (new_hash != prev_hash):
#                 prev_hash = new_hash

#                 # parse table if applicable
#                 table_data = parse_gold_table(inner_text)
#                 df = clean_dataframe(table_data)
#                 df = df.replace({np.nan: None})
#                 records = df.to_dict(orient="records")

#                 entry = format_custom_json(target_cfg, records, inner_text)

#                 # update JSON records for that URL id
#                 try:
#                     update_records_by_id(str(target_cfg.get("_id", "")), records, inner_text or "")
#                     print("URL ID => ", target_cfg.get("_id"))
                    
#                 except Exception as e:
#                     logging.exception(f"Failed to update JSON for {target_cfg.get('url')}: {e}")

#                 # send payload (combined type)
#                 try:
#                     await send_func({
#                         "type": "combined_scrape",
#                         "html_scrape": [entry],
#                         "api_scrape": []
#                     })
#                 except Exception:
#                     # send_func failure shouldn't kill watcher; just log
#                     logging.exception("send_func failed in start_watch_for_cfg")

#         except Exception:
#             # swallow individual iteration errors and retry quickly
#             await asyncio.sleep(0.1)
#             continue

#         await asyncio.sleep(0.1)


# # -----------------------
# # Open page helper (safe)
# # -----------------------
# async def open_page(context, url, timeout=30000):
#     """
#     Open a page in the provided browser context and navigate to url.
#     Returns page or raises.
#     """
#     page = await context.new_page()
#     await page.goto(url, wait_until="commit", timeout=timeout)
#     return page


# # -----------------------
# # Open page and start watcher (returns page and the watcher task)
# # -----------------------
# async def open_page_and_start_watch(context, target_cfg: dict, stop_event: asyncio.Event, send_func):
#     """
#     Opens a page for target_cfg and starts a watcher task using start_watch_for_cfg.
#     Returns (page, task).
#     """
#     url = target_cfg.get("url")
#     try:
#         page = await open_page(context, url)
#     except Exception as e:
#         # report failure via send_func and return None
#         try:
#             await send_func({
#                 "url": url,
#                 "status": "error",
#                 "message": f"Failed to open page: {e}"
#             })
#         except Exception:
#             logging.exception("send_func failed while reporting open_page error")
#         return None, None

#     # start the watcher task
#     task = asyncio.create_task(start_watch_for_cfg(target_cfg, page, stop_event, send_func))
#     return page, task


# # -----------------------
# # Main combined scraper (original logic, updated to use helpers)
# # -----------------------
# async def scrape_combined(browser, targets, stop_event, send_func, reload_interval=60):
#     """
#     Combined scraper:
#       - launches a browser context
#       - opens all HTML targets and starts watchers
#       - polls API targets and sends API results
#     """
#     global html_pages, prev_values, saved_once

#     html_pages = []
#     prev_values = {}
#     saved_once = {t["url"]: False for t in targets}

#     api_targets = [t for t in targets if t.get("scrap_from") == "API"]
#     html_targets = [t for t in targets if t.get("scrap_from") != "API"]

#     combined_buffer = {"html_scrape": [], "api_scrape": []}

#     try:
#         context = await browser.new_context()
#         logging.info("✅ Browser context created.")
#     except Exception as e:
#         await send_func({"status": "error", "message": f"Browser init failed: {str(e)}"})
#         return

#     async with httpx.AsyncClient(timeout=10) as client:
#         # Open HTML pages and start watchers
#         open_tasks = [open_page_and_start_watch(context, cfg, stop_event, send_func) for cfg in html_targets]
#         opened_results = await asyncio.gather(*open_tasks)
#         # opened_results is list of tuples (page, task) or (None, None)
#         html_pages = [(cfg, page, task) for cfg, (page, task) in zip(html_targets, opened_results) if page is not None]

#         # initialize prev_values
#         for cfg, page, task in html_pages:
#             prev_values[cfg["url"]] = None

#         try:
#             # API polling loop
#             while not stop_event.is_set():
#                 for target in api_targets:
#                     url = target.get("url")
#                     name = target.get("name", "Unnamed")

#                     try:
#                         resp = await client.get(url)

#                         if resp.status_code == 200:
#                             text_data = parse_table(resp.text)
#                             api_entry = {
#                                 "status": "success",
#                                 "name": name,
#                                 "url": url,
#                                 "text": text_data,
#                             }

#                             combined_buffer["api_scrape"] = [api_entry]

#                             # update JSON for API scrape also
#                             records = [{"data": text_data}]
#                             try:
#                                 update_records_by_id(str(target.get("_id", "")), records, "")
#                             except Exception:
#                                 logging.exception("Failed to update JSON for API target")

#                             # send combined payload (include any latest html_scrape if present)
#                             try:
#                                 await send_func({
#                                     "type": "combined_scrape",
#                                     "html_scrape": combined_buffer["html_scrape"] or [],
#                                     "api_scrape": combined_buffer["api_scrape"],
#                                 })
#                             except Exception:
#                                 logging.exception("send_func failed when sending API payload")

#                         else:
#                             try:
#                                 await send_func({
#                                     "url": url,
#                                     "status": "error",
#                                     "message": f"HTTP {resp.status_code}"
#                                 })
#                             except Exception:
#                                 logging.exception("send_func failed when reporting HTTP error")

#                     except Exception as e:
#                         try:
#                             await send_func({
#                                 "url": url,
#                                 "status": "error",
#                                 "message": str(e)
#                             })
#                         except Exception:
#                             logging.exception("send_func failed when reporting exception for API target")

#                 await asyncio.sleep(3)

#         finally:
#             # cancel watcher tasks and close pages
#             for cfg, page, task in html_pages:
#                 try:
#                     if task and not task.done():
#                         task.cancel()
#                 except Exception:
#                     pass

#             for cfg, page, task in html_pages:
#                 try:
#                     await page.close()
#                 except Exception:
#                     pass

#             try:
#                 await context.close()
#             except Exception:
#                 pass

#             logging.info("🧹 Browser context closed.")
