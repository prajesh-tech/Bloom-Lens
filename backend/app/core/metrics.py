from collections import defaultdict, deque
from threading import Lock
from typing import Any, Dict


class MetricsStore:
    """Small in-process metrics store for lightweight production visibility."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.request_count = 0
        self.error_count = 0
        self.endpoint_usage: Dict[str, int] = defaultdict(int)
        self.request_durations = deque(maxlen=500)
        self.upload_durations = deque(maxlen=100)
        self.analysis_durations = deque(maxlen=100)

    def record_request(self, endpoint: str, duration: float, status_code: int) -> None:
        with self._lock:
            self.request_count += 1
            self.endpoint_usage[endpoint] += 1
            self.request_durations.append(duration)
            if status_code >= 500:
                self.error_count += 1

    def record_upload(self, upload_duration: float, analysis_duration: float) -> None:
        with self._lock:
            self.upload_durations.append(upload_duration)
            self.analysis_durations.append(analysis_duration)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            durations = list(self.request_durations)
            uploads = list(self.upload_durations)
            analyses = list(self.analysis_durations)
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "endpoint_usage": dict(self.endpoint_usage),
                "avg_request_duration_ms": _avg_ms(durations),
                "avg_upload_processing_ms": _avg_ms(uploads),
                "avg_analysis_processing_ms": _avg_ms(analyses),
            }


def _avg_ms(values: list[float]) -> float:
    if not values:
        return 0.0
    return round((sum(values) / len(values)) * 1000, 2)


metrics = MetricsStore()
