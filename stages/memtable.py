# Handles the data in RAM
import threading
import bisect
import sys
from types import MappingProxyType

class MemTable:
    def __init__(self, max_bytes: int = 4 * 1024 ** 2):
        self.max_bytes = max_bytes
        self._table: dict[str, list[tuple[int, float]]] = {}
        self.data = []
        self.lock = threading.RLock()
        self.current_size = 0
        self.is_immutable = False

    def put(self, series_id : str, timestamp : int, value : float) -> bool:
        with self.lock:
            if self.is_immutable:
                return False

            entry_size = len(series_id.encode('utf-8')) + 8 + 8
            if self.current_size + entry_size > self.max_bytes:
                return False

            points = self._table.setdefault(series_id, [])
            data_point = (timestamp, value)

            if not points or timestamp > points[-1][0]:
                points.append(data_point)
                self.current_size += entry_size
            else:
                index = self.index_of_timestamp(points, timestamp)
                if index is not None:
                    points[index] = data_point
                else:
                    bisect.insort(points, data_point)
                    self.current_size += entry_size
            return True

    def index_of_timestamp(points: list[tuple[int, float]], timestamp: int) -> int | None:
        lo = bisect.bisect_left([p[0] for p in points], timestamp)
        if lo < len(points) and points[lo][0] == timestamp:
            return lo
        return None

    def freeze(self) -> MappingProxyType:
        with self.lock:
            self.is_immutable = True
            snapshot = {series_id: points[:] for series_id, points in self._table.items()}
            return MappingProxyType(snapshot)

    def is_full(self) -> bool:
        with self.lock:
            return self.current_size >= self.max_bytes

    def clear(self):
        with self.lock:
            self._table = {}
            self.current_size = 0
            self.is_immutable = False

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

    def get(self, series_id : str, timestamp : int) -> float | None:
        with self.lock:
            points = self._table.get(series_id)
            if not points:
                return None

            index = self.index_of_timestamp(points, timestamp)
            return points[index][1] if index is not None else None

    def delete_point(self, series_id: str, timestamp: int) -> bool:
        with self.lock:
            if self.is_immutable:
                return False

            points = self._table.get(series_id)
            if not points:
                return False

            index = self.index_of_timestamp(points, timestamp)
            if index is None:
                return False

            entry_size = len(series_id('utf-8')) + 8 + 8
            del points[index]
            self.current_size -= entry_size

            if not points:
                del self._table[series_id]

            return True

    def delete_series(self, series_id: str) -> bool:
        with self.lock:
            if self.is_immutable:
                return False

            points = self._table.pop(series_id, None)
            if points is None:
                return False

            entry_size_per_point = len(series_id.encode('utf-8')) + 8 + 8
            self.current_size -= entry_size_per_point * len(points)
            return True

        
    