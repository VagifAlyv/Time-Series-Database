# Handles the data in RAM
import threading
import bisect

class MemTable:
    def __init__(self, max_bytes: int = 4 * 1024 ** 2):
        self.max_bytes = max_bytes
        self._table = {}
        self.data = []
        self.lock = threading.Lock()
        self.current_size = 0
        self.isimmutable = False

    def put(self, series_id : str, timestamp : int, value : float) -> bool:
        with self.lock:
            if self.isimmutable is True:
                return False



    def is_full(self) -> bool:
        with self.lock:
            return self.current_size > self.max_bytes