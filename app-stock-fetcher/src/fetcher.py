import yfinance as yf
from datetime import datetime
import pandas as pd

class StockFetcher:
    def __init__(self, tickers):
        self.tickers = [t.strip() for t in tickers]

    def fetch_data(self, ticker, period="1d", interval="1m"):
        """Fetch stock data using yfinance"""
        try:
            print(f"[{datetime.now()}] Fetching data for {ticker}...")
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if data.empty:
                print(f"No data received for {ticker}")
                return None
            
            # If the columns are MultiIndex (e.g. from newer yfinance versions), flatten them
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
