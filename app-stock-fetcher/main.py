import time
from datetime import datetime
from config import config
from src.fetcher import StockFetcher
from src.storage import get_storage_backend

def main():
    print(f"[{datetime.now()}] Starting stock data collection...")
    print(f"Tickers: {config.STOCK_TICKERS}")
    print(f"Storage Mode: {config.STORAGE_MODE}")

    fetcher = StockFetcher(config.STOCK_TICKERS)
    storage_backends = get_storage_backend(config)

    if not storage_backends:
        print("Error: No storage backends available. Exiting.")
        return

    while True:
        try:
            for ticker in fetcher.tickers:
                data = fetcher.fetch_data(ticker)
                
                if data is not None:
                    # Store in all available backends (e.g. InfluxDB with CSV fallback implemented in factory logic)
                    # Here we just iterate through whatever the factory gave us
                    stored = False
                    for backend in storage_backends:
                        if backend.store(ticker, data):
                            stored = True
                            break # Use the first successful backend in prioritized list
                    
                    if not stored:
                        print(f"Failed to store data for {ticker} in any backend")

            print(f"\n[{datetime.now()}] Waiting {config.FETCH_INTERVAL} seconds until next fetch...")
            time.sleep(config.FETCH_INTERVAL)

        except Exception as e:
            print(f"Error in main loop: {e}")
            print(f"Retrying in {config.FETCH_INTERVAL} seconds...")
            time.sleep(config.FETCH_INTERVAL)

if __name__ == "__main__":
    main()
