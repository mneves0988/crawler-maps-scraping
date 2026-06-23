import os
from dotenv import load_dotenv

load_dotenv()

SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "http://localhost:8080")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
