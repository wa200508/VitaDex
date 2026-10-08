"""On-demand device narration; no model, microphone, or network client."""
import time


class AndroidSpeechBridge:
    def __init__(self):
        self.engine = None
        self.generation = 0
        self.started_generation = None
        self.error = None

    def speak(self, text):
        from android.runnable import run_on_ui_thread
        from jnius import autoclass
        generation = self.generation
        self.started_generation = None
        self.error = None

        @run_on_ui_thread
        def start():
            if generation != self.generation:
                return
            try:
                if self.engine is not None and str(self.engine.getState()).startswith('error:'):
                    self.engine.close()
                    self.engine = None
                if self.engine is None:
                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    self.engine = autoclass('org.vitadex.OfflineNarrator')(activity)
                self.engine.speak(text)
                self.started_generation = generation
            except Exception as error:
                self.error = str(error)
        start()

    def state(self):
        if self.error is not None:
            return 'error:' + self.error
        if self.started_generation != self.generation:
            return 'loading'
        return str(self.engine.getState()) if self.engine is not None else 'loading'

    def stop(self):
        self.generation += 1
        if self.engine is not None:
            from android.runnable import run_on_ui_thread
            engine = self.engine
            @run_on_ui_thread
            def stop_engine():
                engine.stop()
            stop_engine()

    def close(self):
        self.generation += 1
        if self.engine is not None:
            from android.runnable import run_on_ui_thread
            engine, self.engine = self.engine, None
            @run_on_ui_thread
            def close_engine():
                engine.close()
            close_engine()


class NarrationSession:
    """Watch only an active utterance; cancel callbacks when navigation stops it."""
    def __init__(self, bridge, schedule_interval, now=time.monotonic):
        self.bridge = bridge
        self.schedule_interval = schedule_interval
        self.now = now
        self.event = None
        self.active = False
        self.closed = False
        self.generation = 0

    def speak(self, text, on_finished, on_error):
        self.stop()
        if self.closed:
            on_error('Narration has closed.')
            return
        if not text.strip() or len(text) > 3000:
            on_error('Choose a passage of at most 3000 characters to read.')
            return
        generation = self.generation
        started = self.now()
        self.active = True
        try:
            self.bridge.speak(text)
        except Exception as error:
            self.active = False
            on_error(str(error))
            return

        def check(_):
            if generation != self.generation or not self.active:
                return False
            try:
                state = self.bridge.state()
                if state.startswith('error:'):
                    self.stop()
                    on_error(state.split(':', 1)[1])
                    return False
                if state == 'loading' and self.now() - started > 15:
                    self.stop()
                    on_error('Device speech did not start. Check the installed offline voice.')
                    return False
                if self.now() - started > 300:
                    self.stop()
                    on_error('Reading timed out. Choose a shorter passage.')
                    return False
                if state == 'ready':
                    self.stop()
                    on_finished()
                    return False
            except Exception as error:
                self.stop()
                on_error(str(error))
                return False
            return True
        self.event = self.schedule_interval(check, .25)

    def stop(self):
        self.generation += 1
        self.active = False
        if self.event is not None:
            self.event.cancel()
            self.event = None
        self.bridge.stop()

    def close(self):
        self.stop()
        self.closed = True
        self.bridge.close()
