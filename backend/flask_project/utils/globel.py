# ==========================main==========================
# utils/globel.py
from playwright.async_api import async_playwright
import asyncio

_playwright = None
_browser = None
_browser_lock = asyncio.Lock()

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

async def new_page():
    browser = await init_browser()
    page = await browser.new_page()

    async def block_unwanted(route, request):
        if request.resource_type in ["image", "media", "font", "stylesheet", "script"]:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", block_unwanted)
    return page

async def close_browser():
    global _playwright, _browser
    if _browser is not None:
        await _browser.close()
        await _playwright.stop()
        _browser, _playwright = None, None
        
        
# ==========================================runninbg code==========================================
# ========================== main ==========================
# from playwright.async_api import async_playwright
# import asyncio
# import logging

# _playwright = None
# _browser = None
# _browser_lock = asyncio.Lock()
# browser_ready = False  # ✅ Flag to track initialization


# async def init_browser():
#     """Initialize the global Playwright browser only once."""
#     global _playwright, _browser, browser_ready

#     async with _browser_lock:
#         if not browser_ready or _browser is None:
#             logging.info("🌐 Launching Playwright browser...")
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
#             browser_ready = True
#             logging.info("✅ Browser ready and persisted globally.")
#         else:
#             logging.info("♻️ Using existing global browser instance.")

#     return _browser


# async def new_page():
#     """Open a new page in the existing global browser."""
#     browser = await init_browser()
#     page = await browser.new_page()

#     async def block_unwanted(route, request):
#         if request.resource_type in ["image", "media", "font", "stylesheet", "script"]:
#             await route.abort()
#         else:
#             await route.continue_()

#     await page.route("**/*", block_unwanted)
#     return page


# async def close_browser(force=False):
#     """Close the browser only if explicitly asked or force=True."""
#     global _playwright, _browser, browser_ready

#     if not force:
#         logging.info("🟡 Skipping browser close (persistent mode active).")
#         return

#     if _browser is not None:
#         try:
#             logging.info("🧹 Closing global browser and stopping Playwright...")
#             await _browser.close()
#             await _playwright.stop()
#         except Exception as e:
#             logging.warning(f"Error closing browser: {e}")
#         finally:
#             _browser = None
#             _playwright = None
#             browser_ready = False
#             logging.info("✅ All browser resources released.")
