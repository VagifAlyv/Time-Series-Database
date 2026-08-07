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

    def clear(self):
        with self.lock:
            self._table = {}
            self.current_size = 0
            self.isimmutable = False
            self.data = []

    def count(self) -> int:
       with self.lock:
        return sum(len(series_points) for series_points in self._table.values())

    def get_latest(self, series_id : str) -> tuple[int, float] | None:
        with self.lock:
            points = self._table.get(series_id)
            return points[-1] if points else None
        
    def is_empty(self) -> bool:
        with self.lock:
            return not self._table

    def size_bytes(self) -> int:
        with self.lock:
            return self.current_size

    def get(self, series_id : str, timestamp : int) -> float:
        with self.lock:
            points = self._table.get(series_id)
            if not points:
                return None

            for ts, value in points:
                if ts == timestamp:
                    return value
            return None

    def delete(self, series_id: str, timestamp: int) -> bool:
        with self.lock:
            if self.isimmutable:
                return False

        if series_id in self._table:
            del self._table[series_id]
            return True

        return False
    