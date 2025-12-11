# services/scraper_service.py
import asyncio
import logging
from utils.sraping_playwright import scrape_combined
from Services.url_Service import fetch_all_urls_from_db
from utils.globel import init_browser, close_browser

browser = None
stop_event = None  # This was missing!
scraper_task = None
is_running = False
scraper_loop = None


async def run_scraper(sio, connected_clients, authenticated_clients):
    global browser, stop_event, scraper_task, is_running, scraper_loop

    try:
        # Prevent double start
        if is_running:
            logging.info("Scraper already running. New user will receive data.")
            return

        logging.info("🚀 Starting scraper (ONE browser ONLY)")
        is_running = True

        # Fetch URLs
        targets = fetch_all_urls_from_db()
        if not targets:
            logging.warning("No targets found in database")
            return

        # Save the current event loop
        scraper_loop = asyncio.get_running_loop()

        # Create stop event (FIXED)
        stop_event = asyncio.Event()
        
        # Initialize browser
        browser = await init_browser()

        from Services.broadcast_service import broadcast_to_clients

        async def send_func(payload):
            await broadcast_to_clients(
                sio,
                connected_clients,
                authenticated_clients,
                payload
            )

        async def scraper_main():
            global browser, is_running
            max_retries = 3
            retry_count = 0
    
            while retry_count < max_retries and not stop_event.is_set():
                try:
                    await scrape_combined(browser, targets, stop_event, send_func)
                    break  # If scrape_combined completes normally
            
                except asyncio.CancelledError:
                    logging.info("Scraper cancelled")
                    break
            
                except Exception as e:
                    logging.exception(f"Scraper crashed: {e}")
                    retry_count += 1
            
                    if retry_count < max_retries:
                        logging.info(f"Restarting scraper in 5 seconds (attempt {retry_count}/{max_retries})")
                        await asyncio.sleep(5)
                        continue

        # Create task
        scraper_task = asyncio.create_task(scraper_main())
        await scraper_task

    except Exception as e:
        is_running = False
        logging.exception("Error in run_scraper:", exc_info=e)


def stop_scraper():
    global stop_event, scraper_task, is_running

    if stop_event and not stop_event.is_set():
        stop_event.set()
        logging.info("🛑 Scraper stop requested")

    if scraper_task and not scraper_task.done():
        scraper_task.cancel()
        logging.info("🛑 Scraper task cancelled")
    
    is_running = False


def schedule_on_scraper_loop(coro):
    """
    Schedule a coroutine to run on the scraper's event loop.
    Handles both running and non-running loops.
    """
    try:
        # Try to get the running event loop
        loop = asyncio.get_running_loop()
        
        # Schedule the coroutine
        task = loop.create_task(coro)
        return task
    except RuntimeError:
        # No running event loop (scraper not running)
        # Just log it - the target will be picked up on next scraper start
        print(f"⚠ No running event loop. Target will be picked up on next scraper start.")
        return None
 
 
#  ===============templated code above ================
# # services/scraper_service.py
# import asyncio
# import logging
# from utils.sraping_playwright import scrape_combined
# from Services.url_Service import fetch_all_urls_from_db
# from utils.globel import init_browser, close_browser

# browser = None
# stop_event = None
# scraper_task = None
# is_running = False
# scraper_loop = None 

# async def run_scraper(sio, connected_clients, authenticated_clients):
#     global browser, stop_event, scraper_task, is_running

#     try:
#         # ✅ Already running? then don't start again
#         if is_running:
#             logging.info("Scraper already running. New user will receive data.")
#             return

#         logging.info("🚀 Starting scraper (ONE browser ONLY)")

#         is_running = True

#         # Only admin/all URLs (since this is combined feed)
#         targets = fetch_all_urls_from_db()
      

#         if not targets:
#             logging.warning("No targets found in database")
#             return

#         browser = await init_browser()
#         stop_event = asyncio.Event()

#         from Services.broadcast_service import broadcast_to_clients

#         async def send_func(payload):
#             await broadcast_to_clients(
#                 sio,
#                 connected_clients,
#                 authenticated_clients,
#                 payload
#             )

#         async def scraper_loop():
#             global browser, is_running
#             active_pages = {} 
#             try:
#                 await scrape_combined(browser, targets, stop_event, send_func)

#             except asyncio.CancelledError:
#                 logging.info("Scraper cancelled")
#             except Exception as e:
#                 logging.exception(f"Scraper crashed: {e}")
#             finally:
#                 is_running = False
#                 stop_event.set()

#                 if browser:
#                     await close_browser()
#                     browser = None

#                 logging.info("🛑 Scraper stopped")

#         scraper_task = asyncio.create_task(scraper_loop())
#         await scraper_task
        

#     except Exception as e:
#         is_running = False
#         logging.exception("Error in run_scraper:", exc_info=e)

# def stop_scraper():
    
#     global stop_event, scraper_task
    
#     if stop_event and not stop_event.is_set():
#         stop_event.set()
#         logging.info("🛑 Scraper stop requested")

#     if scraper_task and not scraper_task.done():
#         scraper_task.cancel()
#         logging.info("🛑 Scraper task cancelled")
        
# # -------------------------
# # Schedule coroutine onto scraper loop
# # -------------------------
# def schedule_on_scraper_loop(coro):
#     """
#     Thread-safe helper to schedule a coroutine onto the scraper's event loop.
#     Use this in your Flask handlers to add/update/delete live targets.
#     """
#     global scraper_loop
#     if scraper_loop:
#         try:
#             asyncio.run_coroutine_threadsafe(coro, scraper_loop)
#         except Exception as e:
#             logging.warning(f"Failed to schedule coroutine on scraper_loop: {e}")
#     else:
#         logging.warning("Scraper loop not running. Cannot schedule coroutine.")