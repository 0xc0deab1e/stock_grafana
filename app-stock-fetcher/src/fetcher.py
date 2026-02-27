import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

# Existing StockFetcher for real-time data
import threading

def _download_data(symbol: str, *, start: str = None, end: str = None, period: str = None, interval: str = "1d"):
    """Common helper to download data with yfinance.
    - If `period` is provided, `start`/`end` are ignored.
    - If `start`/`end` are provided, they must be YYYY-MM-DD strings.
    Returns a pandas DataFrame or None.
    """
    try:
        print(f"[{datetime.now()}] Downloading data for {symbol} (period={period}, start={start}, end={end}, interval={interval})")
        if period:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
        else:
            df = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
        if df.empty:
            print(f"No data received for {symbol}")
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        print(f"Error downloading data for {symbol}: {e}")
        return None
class StockFetcher:
    def __init__(self, tickers):
        self.tickers = [t.strip() for t in tickers]

    def fetch_data(self, ticker, period="1d", interval="1m"):
        """Fetch recent real‑time data for a ticker using the shared helper."""
        return _download_data(ticker, period=period, interval=interval)

# ---------------------------------------------------------------------------
# Historical data fetch & write to InfluxDB
# ---------------------------------------------------------------------------
from influxdb_client import InfluxDBClient, Point, WritePrecision
from config import config

_historical_fetch_lock = threading.Lock()
_historical_fetch_in_progress = set()

def fetch_and_write_historical(symbol: str, years: int = 5, chunk_years: int = 1):
    """Fetch up to `years` years of daily OHLCV data for `symbol` and write to InfluxDB.
    Data is fetched in `chunk_years`‑year batches to avoid long requests and timeouts.
    If a fetch for the same `symbol` is already in progress, the call is ignored.
    """
    # Guard against concurrent fetches for the same symbol
    with _historical_fetch_lock:
        if symbol in _historical_fetch_in_progress:
            print(f"[{datetime.now()}] Historical fetch for {symbol} already in progress – skipping.")
            return
        _historical_fetch_in_progress.add(symbol)
    try:
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=years * 365)
        chunk_start = start_dt
        while chunk_start < end_dt:
            chunk_end = min(chunk_start + timedelta(days=chunk_years * 365), end_dt)
            start_str = chunk_start.strftime("%Y-%m-%d")
            end_str = chunk_end.strftime("%Y-%m-%d")
            print(f"[{datetime.now()}] Fetching historical chunk for {symbol} from {start_str} to {end_str}")
            df = _download_data(symbol, start=start_str, end=end_str, interval="1d")
            if df is None or df.empty:
                # No data for this chunk – move to next
                chunk_start = chunk_end
                continue
            # Write chunk to InfluxDB
            client = InfluxDBClient(url=config.INFLUXDB_URL, token=config.INFLUXDB_TOKEN, org=config.INFLUXDB_ORG)
            write_api = client.write_api()
            points = []
            for ts, row in df.iterrows():
                point = (
                    Point("stock_price")
                    .tag("ticker", symbol)
                    .field("open", float(row["Open"]))
                    .field("high", float(row["High"]))
                    .field("low", float(row["Low"]))
                    .field("close", float(row["Close"]))
                    .field("volume", int(row["Volume"]))
                    .time(ts, WritePrecision.NS)
                )
                points.append(point)
            if points:
                write_api.write(bucket=config.INFLUXDB_BUCKET, record=points)
                print(f"[{datetime.now()}] Written {len(points)} points for {symbol} ({start_str} to {end_str})")
            client.close()
            chunk_start = chunk_end
            
        # Also fetch the last 7 days of 1-minute interval data (yfinance max for 1m is 7 days)
        print(f"[{datetime.now()}] Fetching recent 7 days of 1-minute data for {symbol}")
        df_1m = _download_data(symbol, period="7d", interval="1m")
        if df_1m is not None and not df_1m.empty:
            client = InfluxDBClient(url=config.INFLUXDB_URL, token=config.INFLUXDB_TOKEN, org=config.INFLUXDB_ORG)
            write_api = client.write_api()
            points_1m = []
            for ts, row in df_1m.iterrows():
                point = (
                    Point("stock_price")
                    .tag("ticker", symbol)
                    .field("open", float(row["Open"]))
                    .field("high", float(row["High"]))
                    .field("low", float(row["Low"]))
                    .field("close", float(row["Close"]))
                    .field("volume", int(row["Volume"]))
                    .time(ts, WritePrecision.NS)
                )
                points_1m.append(point)
            if points_1m:
                write_api.write(bucket=config.INFLUXDB_BUCKET, record=points_1m)
                print(f"[{datetime.now()}] Written {len(points_1m)} 1-minute points for {symbol}")
            client.close()

    except Exception as e:
        print(f"Error in historical fetch for {symbol}: {e}")
    finally:
        with _historical_fetch_lock:
            _historical_fetch_in_progress.discard(symbol)
