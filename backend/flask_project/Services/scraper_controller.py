# scraper_controller.py
from utils.globel import init_browser, close_browser
from Services.scraper_service import stop_scraper, run_scraper

import asyncio

active_pages = {}   # {url_id: page_object}

async def reload_single_url(browser, context, target_cfg, send_func):
    url_id = target_cfg["_id"]
    domain = target_cfg["url"]

    # old page band karo
    if url_id in active_pages:
        try:
            await active_pages[url_id].close()
        except:
            pass

    # new page open
    page = await context.new_page()
    await page.goto(domain, wait_until="commit")

    active_pages[url_id] = page

    # watch_page chalavu
    from utils.sraping_playwright import start_watch_for_cfg
    asyncio.create_task(start_watch_for_cfg(target_cfg, page, send_func))
