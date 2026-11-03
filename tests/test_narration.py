from threading import Event

from narration import LocalSpeaker


def test_speech_engine_failure_is_reported_without_blocking_caller(monkeypatch):
    speaker = LocalSpeaker(platform='linux')
    received = []
    finished = Event()
    def missing_engine():
        raise RuntimeError('No system voice installed')
    monkeypatch.setattr(speaker, '_command', missing_engine)
    def failed(message):
        received.append(message)
        finished.set()
    speaker.speak('An introduction', failed)
    assert finished.wait(timeout=2)
    assert received == ['No system voice installed']
    speaker.stop()


def test_fifo_events_cancel_pause_resume_and_shutdown():
    from narration import SpeechUnavailable
    import pytest
    from queue import Queue

    began, release = Event(), Event()
    class Engine:
        def run(self, text, cancel, started):
            started()
            began.set()
            assert release.wait(2)
        def stop(self):
            release.set()
        def close(self):
            self.stop()
    speaker = LocalSpeaker(engine=Engine(), capacity=1)
    events = Queue()
    speaker.speak('first', card_id='dog', utterance_id='one', on_event=events.put)
    assert began.wait(2)
    speaker.speak('second', card_id='cat', utterance_id='two', on_event=events.put)
    speaker.speak('overflow', card_id='tree', utterance_id='three', on_event=events.put)
    speaker.pause()
    with pytest.raises(SpeechUnavailable):
        speaker.speak('background')
    speaker.resume()
    speaker.close()
    speaker.worker.join(2)
    assert not speaker.worker.is_alive()
    collected = []
    while not events.empty():
        collected.append(events.get_nowait())
    states = {uid: [e.state for e in collected if e.utterance_id == uid] for uid in ('one', 'two', 'three')}
    assert states['one'] == ['requested', 'started', 'cancelled']
    assert states['two'] == ['requested', 'cancelled']
    assert states['three'] == ['requested', 'failed']
    assert all(e.card_id == 'cat' for e in collected if e.utterance_id == 'two')


def test_completed_event_identifies_the_card():
    from queue import Queue
    class Engine:
        def run(self, text, cancel, started):
            started()
        def stop(self):
            pass
        def close(self):
            pass
    events = Queue()
    speaker = LocalSpeaker(engine=Engine())
    uid = speaker.speak('test', card_id='robin', on_event=events.put)
    actual = [events.get(timeout=2) for _ in range(3)]
    assert [e.state for e in actual] == ['requested', 'started', 'completed']
    assert all(e.utterance_id == uid and e.card_id == 'robin' for e in actual)
    speaker.close()
    speaker.worker.join(2)
    assert not speaker.worker.is_alive()


def test_native_lifecycle_with_simulated_android_handle(monkeypatch):
    import native_speech
    from native_speech import NativeEngine
    monkeypatch.setattr(native_speech, 'on_ui', lambda function: function())
    class Handle:
        def __init__(self):
            self.polls = 0
            self.stopped = self.disposed = False
        def speak(self, *args):
            return 0
        def isSpeaking(self):
            self.polls += 1
            return self.polls < 3
        def stop(self):
            self.stopped = True
        def shutdown(self):
            self.disposed = True
    engine, handle = NativeEngine('android'), Handle()
    def initialize():
        engine.synth, engine.status = handle, 0
        engine.ready.set()
    monkeypatch.setattr(engine, '_initialize', initialize)
    monkeypatch.setattr(engine, '_offline_android_voice', lambda: None)
    starts = []
    engine.run('Introduction', Event(), lambda: starts.append(True))
    assert starts == [True]
    engine.close()
    assert handle.stopped and handle.disposed and engine.synth is None
    engine.resume()
    assert not engine.closed and not engine.ready.is_set()


def test_android_never_selects_network_or_downloadable_voice():
    from native_speech import NativeEngine
    class Features:
        def __init__(self, needs_download):
            self.needs_download = needs_download
        def contains(self, key):
            return key == 'notInstalled' and self.needs_download
    class Locale:
        def getLanguage(self):
            return 'en'
        def getCountry(self):
            return 'US'
    class Voice:
        def __init__(self, network, download):
            self.network, self.download = network, download
        def getFeatures(self):
            return Features(self.download)
        def isNetworkConnectionRequired(self):
            return self.network
        def getLocale(self):
            return Locale()
        def getName(self):
            return 'voice'
    wanted = Voice(False, False)
    class Iterator:
        def __init__(self):
            self.items = iter([Voice(False, True), Voice(True, False), wanted])
            self.left = 3
        def hasNext(self):
            return self.left > 0
        def next(self):
            self.left -= 1
            return next(self.items)
    class Voices:
        def iterator(self):
            return Iterator()
    class Engine:
        def getVoices(self):
            return Voices()
        def setVoice(self, voice):
            assert voice is wanted
            return 0
    native = NativeEngine('android')
    native.synth = Engine()
    native._offline_android_voice()
    assert native.voice_configured
