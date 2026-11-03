"""Explicit backup and restore workflow, separate from discovery and speech."""

from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout

from backup import JournalBackup
from .widgets import Action, column, label, PAPER, GREEN


class BackupDialog:
    def __init__(self, app):
        self.app = app
        self.busy = False

    def open(self):
        app = self.app
        if self.busy:
            return app.dialogs.overlay
        service = JournalBackup(app.journal_repository)
        body = column(padding=16)
        body.add_widget(label("Keep a copy of your discoveries", size=22, bold=True))
        body.add_widget(
            label(
                "Backups include saved facts, citations, older fact versions, and discovery history. Model keys are never included. Import only backups you trust: files can contain edited facts and review labels.",
                size=14,
            )
        )
        status = label("No changes have been made.", size=14)
        export = Action(text="Export journal", primary=True)
        choose = Action(text="Choose backup to restore")
        mode = Spinner(
            text="Merge new organisms",
            values=("Merge new organisms", "Replace whole journal"),
            size_hint_y=None,
            height=48,
            shorten=True,
        )
        confirm = Action(text="Confirm restore", disabled=True)
        state = {"path": None, "preview": None}
        directory = Path(app.user_data_dir) / "backups"
        local = Spinner(
            text="Backups on this device",
            values=tuple(sorted((path.name for path in directory.glob("*.json")), reverse=True)),
            size_hint_y=None,
            height=48,
            shorten=True,
        )
        export_local = Action(text="Export selected local backup", disabled=True)
        controls = (export, choose, mode, local, export_local)

        def run(operation, finished):
            if self.busy:
                return
            self.busy = True
            for widget in controls:
                widget.disabled = True
            confirm.disabled = True

            def work():
                try:
                    value, error = operation(), None
                except Exception as caught:
                    value, error = None, str(caught)

                def deliver(_):
                    self.busy = False
                    for widget in controls:
                        widget.disabled = False
                    if error:
                        status.text = error
                    else:
                        finished(value)

                Clock.schedule_once(deliver, 0)

            Thread(target=work, daemon=True).start()

        def exported(path, error=None):
            local.values = tuple(
                sorted((path.name for path in directory.glob("*.json")), reverse=True)
            )
            if error:
                status.text = error
            elif path:
                status.text = "Backup exported. Your local journal is unchanged."

        def export_now(*_):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
            path = Path(app.user_data_dir) / "backups" / ("vitadex-" + stamp + ".json")
            run(lambda: service.export(path), lambda saved: app.documents.choose(exported, saved))

        def previewed(preview):
            state["preview"] = preview
            prefix = (
                "Keep current cards. "
                if preview.mode == "merge"
                else "Replace all current cards, voice settings, and unread badges. "
            )
            status.text = (
                prefix
                + f"{preview.added} cards to restore; {preview.skipped} existing or duplicate cards skipped. "
                f"{preview.total} cards afterward. A safety copy will be saved first. "
                "Restoring never reads introductions aloud."
            )
            confirm.disabled = False

        def preview(*_):
            state["preview"] = None
            confirm.disabled = True
            if state["path"]:
                run(
                    lambda: service.preview(
                        state["path"], "merge" if mode.text.startswith("Merge") else "replace"
                    ),
                    previewed,
                )

        def selected(path, error):
            if error:
                status.text = error
            elif path:
                state["path"] = path
                preview()

        def restored(safety):
            app.reload_journal()
            state["preview"] = None
            local.values = tuple(
                sorted((path.name for path in directory.glob("*.json")), reverse=True)
            )
            status.text = "Journal restored. A safety copy is available in Backups on this device."

        def restore(*_):
            if state["preview"]:
                approved = state["preview"]
                run(
                    lambda: service.restore(approved, Path(app.user_data_dir) / "backups"), restored
                )

        export.bind(on_release=export_now)
        choose.bind(on_release=lambda *_: app.documents.choose(selected))
        mode.bind(text=preview)

        def local_selected(*_):
            if local.text in local.values:
                state["path"] = directory / local.text
                export_local.disabled = False
                preview()

        local.bind(text=local_selected)
        export_local.bind(
            on_release=lambda *_: (
                app.documents.choose(exported, directory / local.text)
                if local.text in local.values
                else None
            )
        )
        confirm.bind(on_release=restore)
        for widget in (export, choose, local, export_local, mode, status, confirm):
            body.add_widget(widget)
        content = BoxLayout(orientation="vertical", spacing=8)
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(body)
        content.add_widget(scroll)
        popup = Popup(
            title="Journal backups",
            content=content,
            size_hint=(0.95, 0.95),
            auto_dismiss=False,
            background="",
            background_color=PAPER,
            title_color=GREEN,
        )
        content.add_widget(
            Action(text="Close", on_release=lambda *_: popup.dismiss() if not self.busy else None)
        )
        app.dialogs.overlay = popup
        popup.bind(on_dismiss=lambda *_: app.dialogs._clear("overlay", popup))
        popup.open()
        return popup
