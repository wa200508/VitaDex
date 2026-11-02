"""Native mobile speech ownership. Actual-device acceptance remains required."""
from threading import Event, current_thread, main_thread
import time


def on_ui(function):
    if current_thread() is main_thread():
        return function()
    from kivy.clock import Clock
    done, result = Event(), []
    def call(_):
        try:
            result.append((True, function()))
        except Exception as error:
            result.append((False, error))
        finally:
            done.set()
    scheduled = Clock.schedule_once(call, 0)
    if not done.wait(5):
        scheduled.cancel()
        raise RuntimeError('The speech UI operation timed out.')
    if not result[0][0]:
        raise result[0][1]
    return result[0][1]


class NativeEngine:
    def __init__(self, platform):
        self.platform, self.synth = platform, None
        self.closed = False
        self.ready = Event()
        self.status = None

    def _initialize(self):
        if self.closed:
            raise RuntimeError('Speech engine is closed.')
        if self.synth is not None:
            return
        if self.platform == 'android':
            from jnius import autoclass, PythonJavaClass, java_method
            from android import mActivity
            owner = self
            class InitListener(PythonJavaClass):
                __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
                __javacontext__ = 'app'
                @java_method('(I)V')
                def onInit(self, status):
                    owner.status = status
                    owner.ready.set()
            self.listener = InitListener()
            self.synth = autoclass('android.speech.tts.TextToSpeech')(mActivity, self.listener)
        else:
            from pyobjus import autoclass
            from pyobjus.dylib_manager import load_framework
            load_framework('/System/Library/Frameworks/AVFoundation.framework')
            self.synth = autoclass('AVSpeechSynthesizer').alloc().init()
            self.status = 0
            self.ready.set()

    def run(self, text, cancel, started):
        on_ui(self._initialize)
        deadline = time.monotonic() + 10
        while not self.ready.wait(.05):
            if cancel.is_set():
                return
            if time.monotonic() > deadline:
                raise RuntimeError('Native speech initialization timed out.')
        if cancel.is_set():
            return
        if self.status != 0:
            raise RuntimeError('Native speech is unavailable.')
        def speak():
            if cancel.is_set() or self.closed:
                return
            if self.platform == 'android':
                self._offline_android_voice()
                if self.synth.speak(text, 0, None, 'vitadex-introduction') == -1:
                    raise RuntimeError('Android speech request failed.')
            else:
                from pyobjus import autoclass, objc_str
                self.utterance = autoclass('AVSpeechUtterance').speechUtteranceWithString_(objc_str(text))
                self.synth.speakUtterance_(self.utterance)
        on_ui(speak)
        began = False
        deadline = time.monotonic() + 60
        while not cancel.wait(.05):
            if self.closed:
                return
            speaking = on_ui(lambda: self.synth.isSpeaking())
            if speaking and not began:
                began = True
                started()
            if began and not speaking:
                return
            if time.monotonic() > deadline:
                self.stop()
                raise RuntimeError('Native speech did not complete.')
        self.stop()

    def _offline_android_voice(self):
        if getattr(self, 'voice_configured', False):
            return
        voices = self.synth.getVoices()
        if voices is None:
            raise RuntimeError('No installed offline voice. Install an English system voice to listen.')
        iterator = voices.iterator()
        candidates = []
        while iterator.hasNext():
            voice = iterator.next()
            features = voice.getFeatures()
            installed = features is not None and not features.contains('notInstalled')
            if installed and not voice.isNetworkConnectionRequired() and str(voice.getLocale().getLanguage()) == 'en':
                candidates.append(voice)
        candidates.sort(key=lambda voice: (str(voice.getLocale().getCountry()) != 'US', str(voice.getName())))
        if not candidates or self.synth.setVoice(candidates[0]) != 0:
            raise RuntimeError('No usable offline English voice. Read the card or install a system voice.')
        self.voice_configured = True

    def stop(self):
        def stop():
            if self.synth is not None:
                if self.platform == 'android':
                    self.synth.stop()
                else:
                    self.synth.stopSpeakingAtBoundary_(0)
        # Do not block the UI while a worker is waiting for a scheduled UI operation.
        if current_thread() is main_thread():
            stop()
        else:
            from kivy.clock import Clock
            Clock.schedule_once(lambda _: stop(), 0)

    def resume(self):
        self.closed = False
        self.ready.clear()
        self.voice_configured = False
        self.status = None

    def close(self):
        self.closed = True
        def close():
            self.stop()
            if self.synth is not None and self.platform == 'android':
                self.synth.shutdown()
            self.synth = None
        if current_thread() is main_thread():
            close()
        else:
            from kivy.clock import Clock
            Clock.schedule_once(lambda _: close(), 0)
