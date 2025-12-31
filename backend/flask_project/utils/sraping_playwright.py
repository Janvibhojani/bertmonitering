# utils/sraping_playwright.py
import asyncio
import httpx
import logging
import hashlib
import numpy as np
from typing import Tuple, Optional, Callable, Any, List

from utils.helpers import parse_gold_table, parse_table, clean_dataframe
from Services.json_manager import update_records,update_api_records
from utils.globel import get_scraper_context # for global current_context

# Module-level state (kept minimal)
# html_pages: list of tuples (cfg, page, task)
html_pages: List[Tuple[dict, Any, asyncio.Task]] = []
prev_values = {}
saved_once = {}

# -----------------------
# Helper: hashing
# -----------------------
def _hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# -----------------------
# Watcher: watch a single page for a target_cfg and call send_func(payload)
# -----------------------
async def start_watch_for_cfg(target_cfg: dict, page, stop_event: asyncio.Event, send_func: Callable[[dict], Any]):
    """
    Watch a single Playwright page for changes and send updates using send_func.
    """
    selector = target_cfg.get("target")
    mode = target_cfg.get("mode", "css")
    only_on_change = target_cfg.get("only_on_change", True)
    name = target_cfg.get("name", "Unnamed")

    if not selector:
        logging.warning(f"No selector defined for target '{name}' ({target_cfg.get('domain')}). Skipping watcher.")
        return

    # Build selector string
    query = (
        f"#{selector.strip()}" if mode == "id"
        else f".{selector.strip()}" if mode == "class"
        else selector.strip()
    )

    prev_hash = None

    def format_custom_json(cfg, records, inner_text):
        nm = cfg.get("name", "Unnamed")
        domain = cfg.get("domain")
        url_id = str(cfg.get("_id", ""))
        scrap_from = cfg.get("scrap_from", "HTML")
        target = cfg.get("target", "")
        mode = cfg.get("mode", "css")
        only_on_change = cfg.get("only_on_change", False)
        interval_ms = cfg.get("interval_ms", 0)
        created_at = cfg.get("created_at", None)
        updated_at = cfg.get("updated_at", None)
        return {
            nm: {
                "domain": domain,
                "url_id": url_id,
                "type": cfg.get("scrap_from", "HTML"),
                "inner_text": inner_text,
                "records": records,
                "target": target,
                "mode": mode,
                "only_on_change": only_on_change,
                "interval_ms": interval_ms,
                "created_at": created_at,
                "updated_at": updated_at
            }
        }

    logging.info(f"▶ Watcher started for {name} | selector={query}")

    while not stop_event.is_set():
        try:
            # Check if page is closed before trying to access it
            if page.is_closed():
                logging.warning(f"Page for {name} is closed, stopping watcher")
                break

            # check selector existence safely
            element = await page.query_selector(query)
            if not element:
                # selector missing on the page — wait and retry
                await asyncio.sleep(0.5)
                continue

            # Extract text/html with timeout
            try:
                inner_text = await asyncio.wait_for(element.inner_text(), timeout=5.0)
                inner_html = await asyncio.wait_for(element.inner_html(), timeout=5.0)
            except asyncio.TimeoutError:
                logging.warning(f"Timeout extracting content for {name}, retrying...")
                await asyncio.sleep(0.5)
                continue
            except Exception as e:
                # If element is detached or page closed, break the loop
                logging.warning(f"Element access failed for {name}: {e}")
                break

            combined = (inner_text or "") + (inner_html or "")
            new_hash = _hash_text(combined)

            if (not only_on_change) or (new_hash != prev_hash):
                prev_hash = new_hash

                # parse table if applicable
                table_data = parse_gold_table(inner_text)
                df = clean_dataframe(table_data)
                df = df.replace({np.nan: None})
                records = df.to_dict(orient="records")

                entry = format_custom_json(target_cfg, records, inner_text)

                # update JSON records for that URL name
                try:
                    update_records(name, records, inner_text, target_cfg)
                except Exception:
                    logging.exception(f"Failed to update JSON for {target_cfg.get('domain')}")

                # send payload to socket
                try:
                    send_func({
                        "type": "combined_scrape",
                        "html_scrape": [entry],
                        "api_scrape": []
                    })
                except Exception:
                    logging.exception("send_func failed in start_watch_for_cfg")

        except asyncio.CancelledError:
            # Task cancellation requested
            logging.info(f"Watcher for {name} cancelled.")
            break
        except Exception as e:
            # Check if page/browser is closed
            if "closed" in str(e).lower() or "TargetClosedError" in str(type(e).__name__):
                logging.info(f"Browser/page closed for {name}, stopping watcher")
                break
            # swallow transient errors and retry
            logging.exception(f"⚠ Watch iteration error in {name}: {e}")
            await asyncio.sleep(0.5)
            continue

        await asyncio.sleep(0.1)
# -----------------------
# Open page helper (safe)
# -----------------------
async def open_page(context, url: str, timeout: int = 30000):
    """
    Open a page in the provided browser context and navigate to url.
    Returns page or raises.
    """
    page = await context.new_page()
    await page.goto(url, wait_until="commit", timeout=timeout)
    return page


# -----------------------
# Open page and start watcher (returns page and the watcher task)
# -----------------------
async def open_page_and_start_watch(context, target_cfg: dict, stop_event: asyncio.Event, send_func: Callable[[dict], Any]):
    """
    Opens a page for target_cfg and starts a watcher task using start_watch_for_cfg.
    Returns (page, task).
    """
    url = target_cfg.get("domain")
    try:
        page = await open_page(context, url)
    except Exception as e:
        # report failure via send_func and return None
        try:
            send_func({
                "url": url,
                "status": "error",
                "message": f"Failed to open page: {e}"
            })
        except Exception:
            logging.exception("send_func failed while reporting open_page error")
        return None, None

    # start the watcher task
    task = asyncio.create_task(start_watch_for_cfg(target_cfg, page, stop_event, send_func))
    return page, task


# ----------------------------------------------------------------------
# ADD / UPDATE / DELETE handlers for dynamic live reload
# ----------------------------------------------------------------------
# utils/sraping_playwright.py

async def add_new_target(context, target_cfg: dict, stop_event: asyncio.Event, send_func: Callable[[dict], Any]):
    """
    Live add a new target into running scraper without restarting.
    Creates a new page, starts watcher, and appends to html_pages.
    """
    global html_pages
    
    logging.info(f"🔍 add_new_target called for: {target_cfg.get('domain')}")
    logging.info(f"🔍 Context valid: {context is not None}")
    logging.info(f"🔍 Stop event set: {stop_event.is_set()}")
    
    if context is None:
        context = get_scraper_context()

    
    page, task = await open_page_and_start_watch(context, target_cfg, stop_event, send_func)
    
    if not page:
        logging.error(f"❌ Failed to open new page for {target_cfg.get('domain')}")
        return
    
    html_pages.append((target_cfg, page, task))
    logging.info(f"✅ Successfully added NEW target live: {target_cfg.get('domain')}")
    logging.info(f"📊 Total pages now: {len(html_pages)}")

async def update_existing_target(context, updated_cfg: dict, stop_event: asyncio.Event, send_func):
    """
    Update existing target live:
      - close old page & task
      - open new page & start watcher
      - keep same index in html_pages
    """
    global html_pages

    if context is None:
        context = get_scraper_context()

  

    for i, (cfg, page, task) in enumerate(list(html_pages)):
        if str(cfg.get("_id")) == str(updated_cfg.get("_id")):
            try:
                if task:
                    task.cancel()
                    try:
                        await task
                    except:
                        pass
                if page and not page.is_closed():
                    await page.close()
            except Exception:
                pass

            new_page, new_task = await open_page_and_start_watch(
                context, updated_cfg, stop_event, send_func
            )

            if not new_page:
                logging.error("Failed to open updated page")
                return

            html_pages[i] = (updated_cfg, new_page, new_task)
            logging.info(f"🟡 Updated target live: {updated_cfg.get('domain')}")
            return

    logging.warning(f"No live target found to update for ID: {updated_cfg.get('_id')}")

async def delete_existing_target(url_id: str, notify_clients=None):
    global html_pages
    found = False
    for i, (cfg, page, task) in enumerate(list(html_pages)):
        if str(cfg.get("_id")) == str(url_id):
            found = True
            # Cancel watcher
            if task:
                task.cancel()
                try:
                    await task
                except:
                    pass

            # Close page safely
            try:
                if page and not page.is_closed():   # ✅ correct check
                    await page.close()
            except Exception as e:
                logging.warning(f"Page close error: {e}")

            # Remove from list
            html_pages = [entry for entry in html_pages if str(entry[0].get("_id")) != str(url_id)]
            logging.info(f"🔴 Deleted target live: {url_id}")

            # Notify clients
            if notify_clients:
                try:
                    await notify_clients({"action": "delete", "url_id": url_id})
                except Exception:
                    logging.exception("notify_clients failed after delete")
            break

    if not found:
        logging.warning(f"No live target found to delete for ID: {url_id}")



# -----------------------
# Main combined scraper
# -----------------------
async def scrape_combined(context, targets, stop_event, send_func):
    """
    Combined scraper:
      - launches a browser context (created from browser param)
      - opens all HTML targets and starts watchers
      - polls API targets and sends API results
    """
    global html_pages, prev_values, saved_once

    html_pages = []
    prev_values = {}
    saved_once = {t["domain"]: False for t in targets if t.get("scrap_from") != "API"}

    api_targets = [t for t in targets if t.get("scrap_from") == "API"]
    html_targets = [t for t in targets if t.get("scrap_from") != "API"]

    combined_buffer = {"html_scrape": [], "api_scrape": []}

    try:
        logging.info("✅ Browser context created and exported to utils.globel")
    except Exception as e:
        {"status": "error", "message": f"Browser init failed: {str(e)}"}
        return

    async with httpx.AsyncClient(timeout=10) as client:
        # Open HTML pages and start watchers
        open_tasks = [open_page_and_start_watch(context, cfg, stop_event, send_func) for cfg in html_targets]
        opened_results = await asyncio.gather(*open_tasks)
        # opened_results is list of tuples (page, task) or (None, None)
        html_pages = [(cfg, page, task) for cfg, (page, task) in zip(html_targets, opened_results) if page is not None]

        # initialize prev_values
        for cfg, page, task in html_pages:
            prev_values[cfg["domain"]] = None

        try:
            # API polling loop
            while not stop_event.is_set():
                for target in api_targets:
                    url = target.get("domain")
                    name = target.get("name", "Unnamed")

                    try:
                        resp = await client.get(url)

                        if resp.status_code == 200:
                            text_data = parse_table(resp.text)
                            api_entry = {
                                "status": "success",
                                "name": name,
                                "url": url,
                                "url_id": str(target.get("_id")),
                                "text": text_data,
                            }

                            combined_buffer["api_scrape"] = [api_entry]

                            # update JSON for API scrape also
                            records = [{"data": text_data}]
                            try:
                                update_api_records(name, text_data, target)
                            except Exception:
                                logging.exception("Failed to update JSON for API target")

                            # send combined payload (include any latest html_scrape if present)
                            try:
                                send_func({
                                    "type": "combined_scrape",
                                    "html_scrape": combined_buffer["html_scrape"] or [],
                                    "api_scrape": combined_buffer["api_scrape"],
                                })
                            except Exception:
                                logging.exception("send_func failed when sending API payload")

                        else:
                            try:
                                send_func({
                                    "url": url,
                                    "status": "error",
                                    "message": f"HTTP {resp.status_code}"
                                })
                            except Exception:
                                logging.exception("send_func failed when reporting HTTP error")

                    except Exception as e:
                        try:
                            send_func({
                                "url": url,
                                "status": "error",
                                "message": str(e)
                            })
                        except Exception:
                            logging.exception("send_func failed when reporting exception for API target")

                await asyncio.sleep(3)

        finally:
        # Set stop event first to signal all watchers to stop
            stop_event.set()
        
        # Give watchers a moment to notice the stop signal
            await asyncio.sleep(0.5)
        # CANCEL watcher tasks
            cancel_tasks = []
            for cfg, page, task in html_pages:
                if task and not task.done():
                    task.cancel()
                    cancel_tasks.append(task)
            
            # Wait for all tasks to finish cancellation
                if cancel_tasks:
                    await asyncio.gather(*cancel_tasks, return_exceptions=True) 
            # CLOSE pages
            close_tasks = []
            for cfg, page, task in html_pages:
                try:
                    if page and not page.is_closed():
                        close_tasks.append(page.close())
                except Exception:
                    pass
            # Wait for all pages to close
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            # globel.current_context = None
            html_pages.clear()  # Clear the list
            logging.info("🧹 Scraper stopped, watchers cleaned up.")
       