from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from .base import StorageBackend

class InfluxDBStorage(StorageBackend):
    def __init__(self, url, token, org, bucket):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org, timeout=5000)
            self.client.ping()
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.available = True
            print(f"Connected to InfluxDB at {self.url}")
        except Exception as e:
            print(f"Failed to connect to InfluxDB: {e}")
            self.available = False

    def is_available(self):
        return self.available

    def store(self, ticker, data):
        if not self.available:
            return False
        
        try:
            # yfinance occasionally returns rows with NaN values
            data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
            
            for index, row in data.iterrows():
                point = (
                    Point("stock_price")
                    .tag("ticker", ticker)
                    .field("open", float(row['Open']))
                    .field("high", float(row['High']))
                    .field("low", float(row['Low']))
                    .field("close", float(row['Close']))
                    .field("volume", int(row['Volume']))
                    .time(index, WritePrecision.NS)
                )
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            print(f"✓ Stored {len(data)} records for {ticker} in InfluxDB")
            return True
        except Exception as e:
            print(f"InfluxDB write error for {ticker}: {e}")
            return False
