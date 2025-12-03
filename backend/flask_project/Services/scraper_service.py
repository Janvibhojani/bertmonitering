# # services/scraper_service.py
# import asyncio
# import logging
# from utils.sraping_playwright import scrape_combined
# from controllers.urls_controller import fetch_all_urls_from_db, fetch_user_allocated_urls
# from utils.globel import init_browser, close_browser

# browser = None
# stop_event = None
# scraper_task = None


# async def run_scraper(sio, sid, connected_clients, authenticated_clients):
#     global browser, stop_event, scraper_task

#     try:
#         user_info = authenticated_clients.get(sid)

#         if not user_info:
#             sio.emit("data", {"error": "Unauthorized"}, to=sid)
#             return

#         user_id = user_info.get("user_id")
#         role = user_info.get("role")

#         # ✅ Role based URL fetching
#         if role == "admin":
#             targets = fetch_all_urls_from_db()
#         else:
#             targets = fetch_user_allocated_urls(user_id)

#         if not targets:
#             sio.emit("data", {"error": "No allocated targets found"}, to=sid)
#             return

#         browser = await init_browser()
#         stop_event = asyncio.Event()

#         sio.emit("status", {
#             "status": "scraping_started",
#             "message": f"Scraper started for {role}",
#             "total_targets": len(targets)
#         }, to=sid)
#         logging.info(f"Targets for user {user_id} ({role}): {targets}")
#         from Services.broadcast_service import broadcast_to_clients

#         async def send_func(payload):
#             await broadcast_to_clients(
#                 sio,
#                 connected_clients,
#                 authenticated_clients,
#                 payload
#             )

#         async def scraper_loop():
#             global browser
#             try:
#                 await scrape_combined(browser, targets, stop_event, send_func)
#             except asyncio.CancelledError:
#                 logging.info("Scraper cancelled")
#             except Exception as e:
#                 logging.exception(f"Scraper crashed: {e}")
#             finally:
#                 stop_event.set()
#                 await close_browser()
#                 browser = None
#                 sio.emit("status", {"status": "scraping_stopped"}, to=sid)

#         scraper_task = asyncio.create_task(scraper_loop())
#         await scraper_task

#     except Exception as e:
#         logging.exception("Error in run_scraper")
#         sio.emit("data", {"error": str(e)}, to=sid)

# def stop_scraper():
#     global stop_event, scraper_task

#     if stop_event and not stop_event.is_set():
#         stop_event.set()
#         logging.info("🛑 Scraper stop requested")

#     if scraper_task and not scraper_task.done():
#         scraper_task.cancel()
#         logging.info("🛑 Scraper task cancelled")
 
 
 
 
#  ===============templated code above ================
# services/scraper_service.py
import asyncio
import logging
from utils.sraping_playwright import scrape_combined
from controllers.urls_controller import fetch_all_urls_from_db
from utils.globel import init_browser, close_browser

browser = None
stop_event = None
scraper_task = None
is_running = False


async def run_scraper(sio, connected_clients, authenticated_clients):
    global browser, stop_event, scraper_task, is_running

    try:
        # ✅ Already running? then don't start again
        if is_running:
            logging.info("Scraper already running. New user will receive data.")
            return

        logging.info("🚀 Starting scraper (ONE browser ONLY)")

        is_running = True

        # Only admin/all URLs (since this is combined feed)
        targets = fetch_all_urls_from_db()

        if not targets:
            logging.warning("No targets found in database")
            return

        browser = await init_browser()
        stop_event = asyncio.Event()

        from Services.broadcast_service import broadcast_to_clients

        async def send_func(payload):
            await broadcast_to_clients(
                sio,
                connected_clients,
                authenticated_clients,
                payload
            )

        async def scraper_loop():
            global browser, is_running
            try:
                await scrape_combined(browser, targets, stop_event, send_func)

            except asyncio.CancelledError:
                logging.info("Scraper cancelled")
            except Exception as e:
                logging.exception(f"Scraper crashed: {e}")
            finally:
                is_running = False
                stop_event.set()

                if browser:
                    await close_browser()
                    browser = None

                logging.info("🛑 Scraper stopped")

        scraper_task = asyncio.create_task(scraper_loop())
        await scraper_task
        

    except Exception as e:
        is_running = False
        logging.exception("Error in run_scraper:", exc_info=e)

def stop_scraper():
    
    global stop_event, scraper_task
    
    if stop_event and not stop_event.is_set():
        stop_event.set()
        logging.info("🛑 Scraper stop requested")

    if scraper_task and not scraper_task.done():
        scraper_task.cancel()
        logging.info("🛑 Scraper task cancelled")