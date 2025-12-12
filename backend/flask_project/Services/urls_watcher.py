import threading
import asyncio
import logging
from bson.objectid import ObjectId
from db.mongo import urls_collection
from utils.globel import current_context, current_stop_event
from utils.sraping_playwright import (
    add_new_target,
    update_existing_target,
    delete_existing_target
)
from Services.url_Service import fetch_all_urls_from_db

def start_url_watcher(send_func):
    def watcher():
        try:
            with urls_collection.watch() as stream:
                logging.info("🔍 MongoDB URL Watcher started...")

                for change in stream:
                    op = change["operationType"]

                    if op == "insert":
                        cfg = change["fullDocument"]
                        asyncio.run_coroutine_threadsafe(
                            add_new_target(
                                current_context,
                                cfg,
                                current_stop_event,
                                send_func
                            ),
                            asyncio.get_event_loop()
                        )

                    elif op == "update":
                        url_id = change["documentKey"]["_id"]
                        cfg = urls_collection.find_one({"_id": ObjectId(url_id)})
                        asyncio.run_coroutine_threadsafe(
                            update_existing_target(
                                current_context,
                                cfg,
                                current_stop_event,
                                send_func
                            ),
                            asyncio.get_event_loop()
                        )

                    elif op == "delete":
                        url_id = str(change["documentKey"]["_id"])
                        asyncio.run_coroutine_threadsafe(
                            delete_existing_target(url_id),
                            asyncio.get_event_loop()
                        )

        except Exception as e:
            logging.error(f"Watcher error: {e}")

    threading.Thread(target=watcher, daemon=True).start()
