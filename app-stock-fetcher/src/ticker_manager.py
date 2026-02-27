import os
import json
from config import config

class TickerManager:
    def __init__(self):
        self.file_path = os.path.join(config.DATA_DIR, "tickers.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([{"symbol": t, "name": t} for t in config.DEFAULT_STOCK_TICKERS], f)

    def get_tickers(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                result = []
                for item in data:
                    if isinstance(item, str):
                        result.append({"symbol": item, "name": item})
                    else:
                        result.append(item)
                return result
        except Exception as e:
            print(f"Error reading tickers: {e}")
            return [{"symbol": t, "name": t} for t in config.DEFAULT_STOCK_TICKERS]

    def get_ticker_symbols(self):
        return [t["symbol"] for t in self.get_tickers()]

    def add_ticker(self, symbol, name=""):
        tickers = self.get_tickers()
        symbol = symbol.strip().upper()
        if symbol and symbol not in [t["symbol"] for t in tickers]:
            tickers.append({"symbol": symbol, "name": name or symbol})
            with open(self.file_path, "w") as f:
                json.dump(tickers, f)
            return True
        return False

    def remove_ticker(self, symbol):
        tickers = self.get_tickers()
        symbol = symbol.strip().upper()
        filtered = [t for t in tickers if t["symbol"] != symbol]
        if len(filtered) < len(tickers):
            with open(self.file_path, "w") as f:
                json.dump(filtered, f)
            return True
        return False
