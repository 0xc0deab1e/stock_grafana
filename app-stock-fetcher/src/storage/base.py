from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    def store(self, ticker, data):
        """Store the fetched data"""
        pass

    @abstractmethod
    def is_available(self):
        """Check if the backend is available"""
        pass
