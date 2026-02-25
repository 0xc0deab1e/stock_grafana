from .influx import InfluxDBStorage
from .csv import CSVStorage

def get_storage_backend(config):
    """Factory to get the appropriate storage backend based on configuration"""
    backends = []
    
    # Try InfluxDB first if mode allows
    if config.STORAGE_MODE in ['influxdb', 'auto']:
        influx = InfluxDBStorage(
            url=config.INFLUXDB_URL,
            token=config.INFLUXDB_TOKEN,
            org=config.INFLUXDB_ORG,
            bucket=config.INFLUXDB_BUCKET
        )
        if influx.is_available():
            backends.append(influx)
        elif config.STORAGE_MODE == 'influxdb':
            print("CRITICAL: InfluxDB mode required but connection failed.")
            return []

    # Fallback to CSV if auto or explicitly requested
    if config.STORAGE_MODE in ['csv', 'auto']:
        # If mode is 'csv', or if 'auto', always add CSVStorage as a reliable fallback
        backends.append(CSVStorage(config.DATA_DIR))

    return backends
