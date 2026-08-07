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

            entry_size = len(series_id.encode('utf-8')) + 8 + 8
            if self.current_size + entry_size > self.max_bytes:
                return False

            if series_id not in self._table:
                self._table[series_id] = []

            points = self._table[series_id]
            data_point = (timestamp, value)

            if not points or timestamp >= points[-1][0]:
                points.append(data_point)

            else:
                bisect.insort(points, data_point)

            self.current_size += entry_size
            return True


    def freeze(self) -> dict[str, list[tuple[int, float]]]:
        with self.lock:
            self.isimmutable = True
            return self.table

    def is_full(self) -> bool:
        with self.lock:
            return self.current_size > self.max_bytes

        
