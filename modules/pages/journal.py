import dash
from dash import html
import pymongo
import dotenv
import os

from modules.custom_logger import create_logger

dash.register_page(__name__)

dotenv.load_dotenv()

logger = create_logger()

def get_db_connection():
    root_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    client = pymongo.MongoClient(f"mongodb://{root_username}:{root_password}@mongo:27017/")
    return client["HumanFlowTaskManagerDB"]

def check_connection(db):
    try:
        db.command("ping")
        logger.info("Successfully connected to MongoDB.")
        return True
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return False

db = get_db_connection()

layout = html.Div([
    html.Div([
        html.H1(db.name)
    ]) if check_connection(db) else html.H1("Error connecting to MongoDB.")
])
