# ==========================main==========================
# # utils/globel.py
# from playwright.async_api import async_playwright
# import asyncio

# _playwright = None
# _browser = None
# _browser_lock = asyncio.Lock()

# async def init_browser():
#     global _playwright, _browser
#     async with _browser_lock:
#         if _browser is None:
#             _playwright = await async_playwright().start()
#             _browser = await _playwright.chromium.launch(
#                 headless=False,
#                 args=[
#                     "--disable-gpu",
#                     "--disable-software-rasterizer",
#                     "--disable-dev-shm-usage",
#                     "--disable-background-timer-throttling",
#                     "--disable-renderer-backgrounding",
#                     "--disable-extensions",
#                     "--disable-features=IsolateOrigins,site-per-process",
#                     "--blink-settings=imagesEnabled=false",
#                     "--disable-sync",
#                     "--disable-translate",
#                     "--disable-features=AudioServiceOutOfProcess",
#                     "--mute-audio",
#                     "--no-sandbox",
#                     "--no-zygote",
#                     "--single-process"
#                 ]
#             )
#     return _browser

# async def new_page():
#     browser = await init_browser()
#     page = await browser.new_page()

#     async def block_unwanted(route, request):
#         if request.resource_type in ["image", "media", "font", "stylesheet", "script"]:
#             await route.abort()
#         else:
#             await route.continue_()

#     await page.route("**/*", block_unwanted)
#     return page

# async def close_browser():
#     global _playwright, _browser
#     if _browser is not None:
#         await _browser.close()
#         await _playwright.stop()
#         _browser, _playwright = None, None
        
        
# ==========================================runninbg code==========================================
# ========================== main ==========================
# utils/globel.py
from playwright.async_api import async_playwright
import asyncio
from typing import Optional

_playwright = None
_browser = None
current_stop_event = None 
current_context = None
_browser_lock = asyncio.Lock()
_active_scraper_context = None  # Add this for scraper context

async def init_browser():
    global _playwright, _browser
    async with _browser_lock:
        if _browser is None:
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
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
    return _browser

def set_scraper_context(context):
    """Set the active scraper context for dynamic additions"""
    global _active_scraper_context
    _active_scraper_context = context
    
def set_stop_event(event):
    global current_stop_event
    current_stop_event = event

def get_stop_event():
    return current_stop_event

def get_scraper_context():
    """Get the active scraper context"""
    return _active_scraper_context

def is_scraper_running():
    """Check if scraper is running"""
    return _active_scraper_context is not None and not _active_scraper_context.is_closed()

async def new_context():
    browser = await init_browser()
    ctx = await browser.new_context()
    return ctx

async def close_browser():
    global _playwright, _browser, current_context, _active_scraper_context
    
    # Clear scraper context first
    _active_scraper_context = None
    
    if current_context is not None:
        try:
            await current_context.close()
        except Exception:
            pass
        current_context = None
        from utils.globel import current_context
        import logging
        if current_context is None:
                logging.warning("No active browser context for deletion!")

    if _browser is not None:
        await _browser.close()
        _browser = None

    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None

    print("🛑 Playwright closed")
    
# utils/globel.py - add these functions

def is_scraper_running():
    """Check if scraper is running"""
    from Services.scraper_service import get_is_running
    running = get_is_running()
    context_running = _active_scraper_context is not None 
    if _active_scraper_context and hasattr(_active_scraper_context, 'is_closed'):
        context_running = not _active_scraper_context.is_closed()
    
    print(f"🔍 Global scraper check: Running={running}, Context={context_running}")
    return running and context_running

def get_stop_event():
    from Services.scraper_service import get_stop_event
    return get_stop_event()