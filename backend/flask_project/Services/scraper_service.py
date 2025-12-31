
 # Services/scraper_service.py
import asyncio
import logging
from utils.sraping_playwright import scrape_combined
from Services.url_Service import fetch_all_urls_from_db
from utils.globel import init_browser, set_scraper_context, set_stop_event

# Global state - અગત્યનું: અહીં proper initialization
browser = None
stop_event = None
_scraper_context = None 
scraper_task = None
is_running = False
scraper_loop = None
  # Add this for better context management

async def run_scraper(sio, connected_clients, authenticated_clients):
    global browser, stop_event, scraper_task, is_running, scraper_loop, _scraper_context
    
    try:
        # Prevent double start
        if is_running:
            logging.info("Scraper already running. New user will receive data.")
            return

        logging.info("🚀 Starting scraper (ONE browser ONLY)")
        is_running = True

        # Fetch targets
        targets = fetch_all_urls_from_db()
        if not targets:
            logging.warning("No targets found in database")
            is_running = False
            return
        
        # Create stop event first
        stop_event = asyncio.Event()

        # Save stop event globally
        set_stop_event(stop_event)

        # Initialize browser
        browser = await init_browser()

        # Create one browser context (required!)
        context = await browser.new_context()
        _scraper_context = context
        set_scraper_context(context)  # Store locally

        # Save scraper context globally
        set_scraper_context(context)

        from Services.broadcast_service import broadcast_to_clients

        def send_func(payload):
            broadcast_to_clients(
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
                    await scrape_combined(
                        context=_scraper_context,
                        targets=targets,
                        stop_event=stop_event,
                        send_func=send_func
                    )
                except asyncio.CancelledError:
                    logging.info("Scraper cancelled")
                    break
                except Exception as e:
                    logging.exception(f"Scraper crashed: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        logging.info(f"Restarting scraper in 5 sec (attempt {retry_count}/{max_retries})")
                        await asyncio.sleep(5)

        scraper_task = asyncio.create_task(scraper_main())
        scraper_loop = asyncio.get_event_loop()  # Store the event loop
        
        logging.info(f"✅ Scraper started with {len(targets)} targets")
        logging.info(f"✅ Event loop stored: {scraper_loop}")
        logging.info(f"✅ Context available: {_scraper_context is not None}")
        
        await scraper_task

    except Exception as e:
        is_running = False
        logging.exception("Error in run_scraper:", exc_info=e)
    finally:
        is_running = False
        _scraper_context = None
        set_scraper_context(None)
        logging.info("Scraper stopped")

def get_stop_event():
    return stop_event

def get_is_running():
    return is_running

def get_scraper_loop():
    return scraper_loop

def stop_scraper():
    global stop_event, scraper_task, is_running
    
    if stop_event and not stop_event.is_set():
        stop_event.set()
        logging.info("🛑 Scraper stop requested")

    if scraper_task and not scraper_task.done():
        scraper_task.cancel()
        logging.info("🛑 Scraper task cancelled")
    
    is_running = False

# FIXED: Proper async function scheduling
def schedule_on_scraper_loop(coro):
    try:
        loop = get_scraper_loop()
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            logging.info("✅ Task scheduled safely on scraper loop")
            return future
        else:
            logging.warning("⚠ Scraper loop not running")
            return None
    except Exception as e:
        logging.error(f"❌ Schedule failed: {e}")
        return None

# NEW: Direct execution function for synchronous calls
async def execute_on_scraper(coro):
    """
    Directly execute a coroutine on scraper loop.
    Use this for immediate operations.
    """
    try:
        loop = get_scraper_loop()
        if loop and loop.is_running():
            # Run the coroutine directly
            result = await coro
            logging.info(f"✅ Executed on scraper loop: {coro.__name__}")
            return result
        else:
            logging.warning("⚠ Scraper loop not running.")
            return None
    except Exception as e:
        logging.error(f"❌ Failed to execute on scraper: {e}")
        return None