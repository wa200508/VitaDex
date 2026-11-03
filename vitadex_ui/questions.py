"""Question dialog. Network credentials remain session-only."""

import webbrowser
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from ask import SessionProvider, spoken_answer
from questions import QuestionController
from .widgets import Action, label, column, INK, MUTED, GREEN, WHITE, PAPER


class QuestionDialog:
    def __init__(self, app):
        self.app = app
        self.controller = QuestionController(
            lambda callback: Clock.schedule_once(lambda _: callback(), 0)
        )
        self.key_widget = self.popup = None
        self.cancelled = True

    def clear(self):
        self.controller.cancel()
        self.cancelled = True
        if self.key_widget:
            self.key_widget.text = ""

    def close(self):
        self.clear()
        self.controller.close()

    def open(self, card):
        app = self.app
        self.clear()
        body = column(padding=12)
        body.add_widget(label("Ask about " + card.title, size=22, bold=True))
        question = TextInput(
            multiline=True,
            size_hint_y=None,
            height=dp(90),
            hint_text="What would you like to know?",
            foreground_color=INK,
            background_color=WHITE,
        )
        body.add_widget(question)
        body.add_widget(
            label(
                "Answers use this saved card’s cited facts. Unanswered questions stay unanswered.",
                size=14,
                color=MUTED,
            )
        )
        preview = CheckBox(size_hint_y=None, height=dp(44))
        body.add_widget(
            label(
                "Optional preview: allow source-checked facts awaiting human review.",
                size=13,
                color=MUTED,
            )
        )
        body.add_widget(preview)
        mode = Spinner(
            text="Offline sources",
            values=("Offline sources", "My model (send once)"),
            size_hint_y=None,
            height=dp(46),
        )
        body.add_widget(mode)
        endpoint = TextInput(
            hint_text="HTTPS chat-completions endpoint",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        model = TextInput(hint_text="Model name", multiline=False, size_hint_y=None, height=dp(46))
        key = TextInput(
            hint_text="Session API key (never saved)",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        config = column()
        for widget in (endpoint, model, key):
            config.add_widget(widget)
        config.add_widget(
            label(
                "The question and up to three saved fact passages go to your endpoint only when you press Send once. The key is session-only and clears on close or pause.",
                size=13,
                color=MUTED,
            )
        )
        config_holder = BoxLayout(size_hint_y=None, height=0)
        config_holder.add_widget(config)
        body.add_widget(config_holder)
        result = label("No request has been made.", size=15)
        sources = column()
        body.add_widget(result)
        body.add_widget(sources)
        send = Action(text="Find an answer", primary=True)
        body.add_widget(send)

        def mode_changed(*_):
            send.text = (
                "Send once to my model"
                if mode.text.startswith("My model")
                else "Find in offline sources"
            )
            config.disabled = not mode.text.startswith("My model")
            config.opacity = 1 if not config.disabled else 0
            config_holder.height = config.minimum_height if not config.disabled else 0

        mode.bind(text=mode_changed)
        config.bind(minimum_height=mode_changed)
        mode_changed()
        read = Action(text="Read answer aloud", disabled=True)
        body.add_widget(read)
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(body)
        content = BoxLayout(orientation="vertical", spacing=dp(8))
        content.add_widget(scroll)
        close = Action(text="Close / cancel")
        content.add_widget(close)
        popup = Popup(
            title="Ask VitaDex",
            content=content,
            size_hint=(0.96, 0.94),
            background="",
            background_color=PAPER,
            title_color=GREEN,
        )
        state = {"reading": False, "job": None}
        self.popup, self.key_widget = popup, key
        self.cancelled = False
        app.dialogs.overlay = popup

        def cancel(*_):
            if self.popup is popup:
                self.clear()
                self.popup = None
            key.text = ""
            if state["reading"]:
                app.speaker.stop()
            if app.dialogs.overlay is popup:
                app.dialogs.overlay = None

        popup.bind(on_dismiss=cancel)
        close.bind(on_release=popup.dismiss)

        def submit(*_):
            if not app.foreground or len(question.text) > 1000:
                result.text = "Use a question up to 1000 characters."
                return
            try:
                provider = (
                    SessionProvider(endpoint.text.strip(), model.text.strip(), key.text)
                    if mode.text.startswith("My model")
                    else None
                )
            except ValueError as error:
                result.text = str(error)
                return
            send.disabled = True
            read.disabled = True
            sources.clear_widgets()
            result.text = "Checking the saved evidence…"
            text, provisional = question.text, preview.active

            def finish(answer, error):
                if self.popup is not popup or self.cancelled or not app.foreground:
                    return
                send.disabled = False
                if error:
                    result.text = error
                    return
                result.text = (
                    "Source-checked preview; human review pending.\n\n"
                    if answer.provisional
                    else ""
                ) + answer.text
                for source in answer.references:
                    sources.add_widget(
                        label("[" + source["id"] + "] " + source["title"], size=13, color=MUTED)
                    )
                    sources.add_widget(
                        Action(
                            text="Open cited reference",
                            on_release=lambda *_, url=source.get("revision_url") or source["url"]: (
                                webbrowser.open(url)
                            ),
                        )
                    )
                read.disabled = not bool(answer.passages)
                if hasattr(read, "_answer_callback"):
                    read.unbind(on_release=read._answer_callback)

                def read_answer(*_):
                    state["reading"] = True

                    def failed(message):
                        def show(_):
                            if self.popup is popup and not self.cancelled:
                                result.text += "\nVoice unavailable: " + message

                        Clock.schedule_once(show, 0)

                    try:
                        app.speaker.speak(spoken_answer(answer), on_error=failed)
                    except Exception as error:
                        failed(str(error))

                read._answer_callback = read_answer
                read.bind(on_release=read._answer_callback)

            try:
                state["job"] = self.controller.submit(card, text, finish, provider, provisional)
            except ValueError as error:
                if provider:
                    provider.clear()
                send.disabled = False
                result.text = str(error)

        send.bind(on_release=submit)
        popup.open()
        return popup
