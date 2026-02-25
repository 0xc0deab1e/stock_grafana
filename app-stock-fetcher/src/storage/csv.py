import os
import pandas as pd
from .base import StorageBackend

class CSVStorage(StorageBackend):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def is_available(self):
        return True  # Local CSV is always "available" if the disk is writable

    def store(self, ticker, data):
        try:
            # Drop rows with NaN values to keep data clean
            data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
            if data.empty:
                return True # Nothing to store, but not an error

            file_path = os.path.join(self.data_dir, f"{ticker}_history.csv")

            if os.path.exists(file_path):
                existing_data = pd.read_csv(file_path, index_col=0)
                existing_data.index = pd.to_datetime(existing_data.index)
                combined_data = pd.concat([existing_data, data]).sort_index()
                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                combined_data.to_csv(file_path)
            else:
                data.to_csv(file_path)

            print(f"✓ Stored {len(data)} records for {ticker} in CSV")
            return True
        except Exception as e:
            print(f"CSV storage error for {ticker}: {e}")
            return False
