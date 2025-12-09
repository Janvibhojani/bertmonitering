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

async def new_context():
    """
    Create a new browser context — reuse single browser but separate context.
    """
    browser = await init_browser()
    return await browser.new_context()

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
    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:
            pass
    _browser, _playwright = None, None
