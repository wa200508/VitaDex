"""Explicitly enabled, bounded, local-only device-test events. Not analytics."""
from collections import deque
from pathlib import Path
from threading import Lock
import time

from editorial import atomic_json


class DeviceTrace:
    def __init__(self, directory, enabled=False, capacity=256):
        self.directory, self.enabled = Path(directory), enabled
        self.events = deque(maxlen=capacity)
        self.lock = Lock()

    def record(self, event, **fields):
        if not self.enabled:
            return
        # No narration, questions, credentials, or user notes enter this stream.
        allowed = {key: str(value)[:120] for key, value in fields.items()
                   if key in ('utterance_id', 'card_id', 'state')}
        with self.lock:
            self.events.append({'monotonic_seconds': time.monotonic(), 'event': event, **allowed})

    def flush(self):
        if self.enabled:
            with self.lock:
                try:
                    atomic_json(self.directory / 'device-trace.json',
                                {'version': 1, 'events': list(self.events)})
                except OSError:
                    return False
                return True
        return False
