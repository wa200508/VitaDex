"""Application lifecycle and coordination; Kivy views live in vitadex_ui."""

from pathlib import Path
from uuid import uuid4
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, NoTransition
from database import CARD_DB
from identification import DemoIdentificationService
from discovery import DiscoveryService, introduction
from narration import LocalSpeaker
from identity import organism_key
from diagnostics import DeviceTrace
from journal import JournalError, JournalRepository, JournalSession
from vitadex_ui.widgets import Action, label, surface, PAPER, WHITE, GREEN, MUTED
from vitadex_ui.screens import HomeScreen, ScanScreen, CardBookScreen
from vitadex_ui.dialogs import CardDialogs
from vitadex_ui.questions import QuestionDialog
from vitadex_ui.documents import DocumentPicker
from vitadex_ui.backups import BackupDialog


class VitaDexApp(App):
    title = "VitaDex · Field journal"

    @property
    def cards(self):
        return self.journal_session.cards

    @property
    def new_cards(self):
        return self.journal_session.new_cards

    @property
    def new_count(self):
        return self.journal_session.new_count

    def is_new(self, card):
        return self.journal_session.is_new(card)

    def build(self):
        self.trace = DeviceTrace(
            self.user_data_dir, enabled=(Path(self.user_data_dir) / "diagnostics.enabled").exists()
        )
        self.trace.record("app.start")
        self.foreground = True
        Window.clearcolor = PAPER
        Window.bind(on_keyboard=self._on_keyboard)
        self.journal_repository = JournalRepository(
            Path(self.user_data_dir) / "journal.sqlite3", Path(self.user_data_dir) / "journal.json"
        )
        self.journal_session = JournalSession(self.journal_repository)
        self.identification_service = DemoIdentificationService(CARD_DB)
        self.discovery_service = DiscoveryService(CARD_DB, self.journal_session)
        self.voice_status = "First discoveries are introduced aloud. You can replay any card."
        try:
            self.voice_enabled = self.journal_repository.load_voice_enabled()
        except JournalError:
            self.voice_enabled = False
            self.voice_status = "Voice settings could not be loaded; automatic narration is off."
        if not hasattr(self, "speaker"):
            from kivy.utils import platform

            self.speaker = LocalSpeaker(
                platform=platform if platform in ("android", "ios") else None
            )
        self.dialogs = CardDialogs(self)
        self.questions = QuestionDialog(self)
        self.documents = DocumentPicker(self)
        self.backups = BackupDialog(self)
        root = surface(BoxLayout(orientation="vertical"), PAPER, radius=0)
        header = surface(
            BoxLayout(padding=(dp(20), dp(10)), spacing=dp(12), size_hint_y=None, height=dp(66)),
            WHITE,
            radius=0,
        )
        header.add_widget(label("VitaDex", size=25, color=GREEN, bold=True))
        header.add_widget(label("FIELD NOTES & SMALL WONDERS", size=10, color=MUTED))
        root.add_widget(header)
        self.manager = ScreenManager(transition=NoTransition())
        self.home_screen, self.scan_screen, self.card_book_screen = (
            HomeScreen(),
            ScanScreen(),
            CardBookScreen(),
        )
        for screen in (self.home_screen, self.scan_screen, self.card_book_screen):
            self.manager.add_widget(screen)
        root.add_widget(self.manager)
        nav = surface(
            BoxLayout(padding=dp(10), spacing=dp(8), size_hint_y=None, height=dp(66)),
            WHITE,
            radius=0,
        )
        self.nav_buttons = {}
        for name, title in [("home", "Journal"), ("scan", "Discover"), ("cardbook", "Card book")]:
            button = Action(text=title, on_release=lambda *_, target=name: self.navigate(target))
            nav.add_widget(button)
            self.nav_buttons[name] = button
        root.add_widget(nav)
        self.navigate("home")
        if self.journal_session.load_error:
            Clock.schedule_once(
                lambda _: self.show_storage_error(str(self.journal_session.load_error)), 0
            )
        return root

    def navigate(self, name):
        self.manager.current = name
        for key, button in self.nav_buttons.items():
            button.primary = key == name
            button.color = WHITE if key == name else GREEN
            button.redraw()
        self.refresh()

    def refresh(self):
        self.home_screen.refresh()
        self.card_book_screen.refresh_cards()

    def handle_encounter(self, result, show_known=False):
        if not self.foreground:
            return
        from threading import current_thread, main_thread

        if current_thread() is not main_thread():
            Clock.schedule_once(lambda _: self.handle_encounter(result, show_known), 0)
            return
        try:
            discovery = self.discovery_service.encounter(result)
        except JournalError as error:
            self.show_storage_error(str(error))
            return
        except ValueError as error:
            self.message("Sources need review", str(error))
            return
        if discovery is None:
            if show_known:
                self.message("Keep observing", result.safety_message)
            return
        self.trace.record(
            "discovery.first" if discovery.is_first else "discovery.repeat",
            card_id=organism_key(discovery.card.organism),
        )
        if discovery.is_first:
            self.refresh()
            self.open_card(discovery.card, saved=True)
            if self.voice_enabled:
                self.read_card(discovery.card)
        elif show_known:
            self.open_card(discovery.card)
        return discovery

    def read_card(self, card):
        if not self.foreground:
            return
        key = organism_key(card.organism)
        uid = uuid4().hex
        self.latest_utterance = uid
        target = self.dialogs.voice_label if self.dialogs.card_key == key else None

        def event(event):
            self.trace.record(
                "speech." + event.state,
                utterance_id=event.utterance_id,
                card_id=event.card_id,
                state=event.state,
            )

            def update(_):
                text = {
                    "requested": "Introduction queued.",
                    "started": "Playing introduction.",
                    "completed": "Introduction finished.",
                    "cancelled": "Introduction stopped.",
                    "failed": "Voice unavailable: " + event.message,
                }.get(event.state, event.state)
                if self.latest_utterance == event.utterance_id:
                    self.voice_status = text
                    self.home_screen.refresh()
                if (
                    target is not None
                    and target is self.dialogs.voice_label
                    and self.latest_utterance == event.utterance_id
                ):
                    target.text = text

            Clock.schedule_once(update, 0)

        try:
            self.speaker.speak(introduction(card), card_id=key, utterance_id=uid, on_event=event)
        except Exception as error:
            from narration import SpeechEvent

            event(SpeechEvent(uid, key, "failed", str(error)))

    def toggle_voice(self):
        if self.journal_session.load_error:
            self.show_storage_error(str(self.journal_session.load_error))
            return
        enabled = not self.voice_enabled
        try:
            self.journal_repository.save_setting("voice_enabled", int(enabled))
        except JournalError as error:
            self.show_storage_error(str(error))
            return
        self.voice_enabled = enabled
        if not enabled:
            self.speaker.stop()
        self.voice_status = (
            "First discoveries are introduced aloud."
            if enabled
            else "Automatic voice is off. Read aloud is still available in each card."
        )
        self.refresh()

    def on_stop(self):
        if hasattr(self, "documents"):
            self.documents.close()
        if hasattr(self, "questions"):
            self.questions.close()
        if hasattr(self, "trace"):
            self.trace.record("app.stop")
        self.foreground = False
        if hasattr(self, "speaker"):
            self.speaker.close()
        if hasattr(self, "trace"):
            self.trace.flush()

    def on_pause(self):
        self.foreground = False
        self.questions.clear()
        self.trace.record("app.pause")
        self.speaker.pause()
        self.trace.flush()
        return True

    def on_resume(self):
        self.speaker.resume()
        self.foreground = True
        self.trace.record("app.resume")

    def show_storage_error(self, text):
        self.message("Journal storage problem", "Your collection was not changed. " + text)

    def _on_keyboard(self, window, key, *args):
        if key == 27:
            if self.dialogs.overlay:
                self.dialogs.overlay.dismiss()
                return True
            if self.dialogs.card_popup:
                self.dialogs.card_popup.dismiss()
            else:
                self.navigate("home")
            return True
        return False

    def open_card(self, card, saved=False):
        return self.dialogs.open_card(card, saved)

    def open_sources(self, card):
        return self.dialogs.open_sources(card)

    def preview_update(self, card, organism):
        return self.dialogs.preview_update(card, organism)

    def message(self, title, text):
        return self.dialogs.message(title, text)

    def open_question(self, card):
        return self.questions.open(card)

    def reload_journal(self):
        """Refresh after restore without routing imported cards through discovery."""
        session = JournalSession(self.journal_repository)
        if session.load_error:
            self.show_storage_error(str(session.load_error))
            return
        self.questions.clear()
        if self.questions.popup:
            self.questions.popup.dismiss()
        if self.dialogs.card_popup:
            self.dialogs.card_popup.dismiss()
        self.speaker.stop()
        self.latest_utterance = None
        session.revision = self.journal_session.revision + 1
        self.journal_session = session
        self.discovery_service = DiscoveryService(CARD_DB, session)
        self.voice_enabled = self.journal_repository.load_voice_enabled()
        self.voice_status = "Journal restored. Introductions play only for new discoveries."
        self.refresh()
