from types import SimpleNamespace
import sys

from narration import AndroidSpeechBridge, NarrationSession


class Bridge:
    def __init__(self):
        self.status = 'loading'
        self.spoken = []
        self.stops = 0
        self.closed = False
    def speak(self, text):
        self.spoken.append(text)
    def state(self):
        return self.status
    def stop(self):
        self.stops += 1
    def close(self):
        self.closed = True


def setup():
    callbacks = []
    cancelled = []
    def schedule(callback, interval):
        callbacks.append(callback)
        return SimpleNamespace(cancel=lambda: cancelled.append(True))
    bridge = Bridge()
    now = [0]
    session = NarrationSession(bridge, schedule, lambda: now[0])
    return session, bridge, callbacks, cancelled, now


def test_reading_requires_explicit_action_and_cancels_on_stop():
    session, bridge, callbacks, cancelled, _ = setup()
    assert not bridge.spoken
    finished, errors = [], []
    session.speak('A sourced field-guide description.', lambda: finished.append(True), errors.append)
    assert bridge.spoken == ['A sourced field-guide description.']
    bridge.status = 'speaking'
    assert callbacks[-1](0)
    session.stop()
    assert cancelled
    assert callbacks[-1](0) is False
    assert not finished and not errors


def test_completed_utterance_ends_monitoring():
    session, bridge, callbacks, _, _ = setup()
    finished = []
    session.speak('Facts', lambda: finished.append(True), lambda _: None)
    bridge.status = 'ready'
    assert callbacks[-1](0) is False
    assert finished == [True]
    assert not session.active


def test_missing_voice_and_initialization_timeout_are_reported():
    for status in ('error:No offline voice.', 'loading'):
        session, bridge, callbacks, _, now = setup()
        errors = []
        session.speak('Facts', lambda: None, errors.append)
        bridge.status = status
        now[0] = 16
        assert callbacks[-1](0) is False
        assert errors
        assert not session.active


def test_new_reading_invalidates_old_callbacks_and_close_releases_engine():
    session, bridge, callbacks, _, _ = setup()
    session.speak('First', lambda: None, lambda _: None)
    old = callbacks[-1]
    session.speak('Second', lambda: None, lambda _: None)
    assert old(0) is False
    session.close()
    assert bridge.closed
    errors = []
    session.speak('Third', lambda: None, errors.append)
    assert errors == ['Narration has closed.']
    assert bridge.spoken == ['First', 'Second']


def test_android_queue_cannot_speak_after_stop(monkeypatch):
    queued, spoken = [], []
    monkeypatch.setitem(sys.modules, 'android', SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'android.runnable', SimpleNamespace(
        run_on_ui_thread=lambda fn: lambda: queued.append(fn)))
    engine = SimpleNamespace(speak=spoken.append, getState=lambda: 'ready', stop=lambda: None,
                             close=lambda: None)
    monkeypatch.setitem(sys.modules, 'jnius', SimpleNamespace(autoclass=lambda name:
        SimpleNamespace(mActivity=object()) if 'PythonActivity' in name else lambda _: engine))
    bridge = AndroidSpeechBridge()
    bridge.speak('Facts')
    assert bridge.state() == 'loading'
    bridge.stop()
    queued.pop(0)()
    assert not spoken
    bridge.speak('New facts')
    queued.pop(0)()
    assert spoken == ['New facts']
    assert bridge.state() == 'ready'
