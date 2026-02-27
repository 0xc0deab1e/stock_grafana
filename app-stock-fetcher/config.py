import os
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

class Config:
    INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
    INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "your-token-here")
    INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "your-org")
    INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "stock_data")

    # Storage settings
    STORAGE_MODE = os.getenv("STORAGE_MODE", "auto")  # 'influxdb', 'csv', 'auto'
    DATA_DIR = os.getenv("DATA_DIR", "./data")

    # Stock settings
    DEFAULT_STOCK_TICKERS = os.getenv("STOCK_TICKERS", "005930.KS").split(",")
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))

config = Config()
