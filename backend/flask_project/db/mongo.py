# db/mongo.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://janvibhojani04:J123456@test.klofke5.mongodb.net/BertMonitoring")
client = MongoClient(MONGO_URL)

try:
    db = client.get_default_database()
except Exception:
    db_name = os.getenv("DB_NAME", "BertMonitoring")
    db = client[db_name]

users_collection = db["users"]
urls_collection = db["urls"]
