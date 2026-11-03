"""Cancellable local speech with bounded FIFO requests and per-card events."""
from dataclasses import dataclass
import shutil
import subprocess
import sys
from queue import Empty, Full, Queue
from threading import Event, Lock, RLock, Thread
from uuid import uuid4


class SpeechUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SpeechEvent:
    utterance_id: str
    card_id: str
    state: str
    message: str = ''


class DesktopEngine:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.lock = Lock()

    def run(self, text, cancel, started):
        with self.lock:
            if cancel.is_set():
                return
            self.process = subprocess.Popen(self.command(), stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            process = self.process
        try:
            started()
            process.communicate(input=text, timeout=60)
            if process.returncode and not cancel.is_set():
                raise SpeechUnavailable('The speech engine could not play the introduction.')
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise SpeechUnavailable('The speech engine timed out.')
        finally:
            with self.lock:
                self.process = None

    def stop(self):
        with self.lock:
            if self.process is not None:
                self.process.terminate()

    def close(self):
        self.stop()


class LocalSpeaker:
    def __init__(self, platform=None, engine=None, capacity=8):
        self.platform = platform or sys.platform
        if engine is None and self.platform in ('android', 'ios'):
            from native_speech import NativeEngine
            engine = NativeEngine(self.platform)
        self.engine = engine or DesktopEngine(lambda: self._command())
        self.pending = Queue(maxsize=capacity)
        self.lock = RLock()
        self.requests = {}
        self.active = None
        self.closed = False
        self.paused = False
        self.worker = Thread(target=self._work, daemon=True)
        self.worker.start()

    @staticmethod
    def _emit(request, state, message=''):
        uid, card_id, text, error, callback, cancel = request
        try:
            if callback:
                callback(SpeechEvent(uid, card_id, state, message))
            if state == 'failed' and error:
                error(message)
        except Exception:
            # A UI callback must not destroy the speech worker.
            import logging
            logging.exception('Speech callback failed')

    def speak(self, text, on_error=None, on_event=None, card_id='', utterance_id=None):
        request = (utterance_id or uuid4().hex, card_id, text, on_error, on_event, Event())
        with self.lock:
            if self.closed or self.paused:
                raise SpeechUnavailable('Speech is paused or has shut down.')
            # Requested precedes any started event, even on a very fast engine.
            self._emit(request, 'requested')
            if self.closed or self.paused:
                self._emit(request, 'cancelled')
                return request[0]
            try:
                self.requests[request[0]] = request
                self.pending.put_nowait(request)
            except Full:
                self.requests.pop(request[0], None)
                self._emit(request, 'failed', 'Voice queue is full. Replay this card when it is free.')
        return request[0]

    def stop(self):
        with self.lock:
            for request in self.requests.values():
                request[-1].set()
            self.engine.stop()
            while True:
                try:
                    request = self.pending.get_nowait()
                except Empty:
                    break
                if request is None:
                    self.pending.put_nowait(None)
                    break
                request[-1].set()
                self._emit(request, 'cancelled')
                self.requests.pop(request[0], None)

    def pause(self):
        with self.lock:
            self.paused = True
            self.stop()
            self.engine.close()

    def resume(self):
        with self.lock:
            if hasattr(self.engine, 'resume'):
                self.engine.resume()
            self.paused = False

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.stop()
            self.pending.put_nowait(None)
        self.engine.close()

    def _command(self):
        if self.platform == 'darwin':
            return ['say']
        if self.platform == 'win32':
            return ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                    'Add-Type -AssemblyName System.Speech; '
                    '$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                    '$voice.Speak([Console]::In.ReadToEnd())']
        engine = shutil.which('espeak-ng') or shutil.which('espeak')
        if engine:
            return [engine, '--stdin']
        raise SpeechUnavailable('Install espeak-ng or espeak to hear narration on Linux.')

    def _work(self):
        while True:
            request = self.pending.get()
            if request is None:
                return
            with self.lock:
                self.active = request
            try:
                if not request[-1].is_set():
                    self.engine.run(request[2], request[-1], lambda: self._emit(request, 'started'))
                self._emit(request, 'cancelled' if request[-1].is_set() else 'completed')
            except Exception as error:
                self._emit(request, 'cancelled' if request[-1].is_set() else 'failed', str(error))
            finally:
                with self.lock:
                    self.active = None
                    self.requests.pop(request[0], None)
