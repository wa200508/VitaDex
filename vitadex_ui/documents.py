"""Explicit file selection: Android Storage Access Framework or desktop chooser."""

import os
from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.utils import platform

from documents import copy_document
from .widgets import Action, column, label, PAPER, GREEN


class DocumentPicker:
    def __init__(self, app):
        self.app = app
        self.pending = None
        self.closed = False

    def close(self):
        self.closed = True
        if self.pending:
            from android import activity

            activity.unbind(on_activity_result=self._android_result)
            self.pending = None

    def choose(self, callback, source=None):
        if platform == "android":
            self._android(callback, source)
        else:
            self._desktop(callback, source)

    def _desktop(self, callback, source):
        chooser = FileChooserListView(path=str(Path.home()), filters=["*.json"])
        body = column(padding=12)
        # FileChooser needs a fixed viewport inside the content-height layout.
        chooser.size_hint_y = None
        chooser.height = 320
        body.add_widget(chooser)
        filename = TextInput(
            text=Path(source).name if source else "",
            multiline=False,
            size_hint_y=None,
            height=48,
            hint_text="Backup filename.json",
        )
        if source:
            body.add_widget(filename)
        status = label(
            "Choose a destination folder." if source else "Choose a VitaDex backup file."
        )
        body.add_widget(status)
        choose = Action(text="Save backup" if source else "Open backup", primary=True)
        body.add_widget(choose)
        popup = Popup(
            title="Export journal" if source else "Open backup",
            content=body,
            size_hint=(0.95, 0.95),
            background="",
            background_color=PAPER,
            title_color=GREEN,
        )
        overwrite = {"path": None}

        def selected(*_):
            try:
                if source:
                    name = filename.text.strip()
                    if not name or Path(name).name != name or name in (".", ".."):
                        raise ValueError("Enter a filename without folders.")
                    destination = Path(chooser.path) / name
                    if destination.exists() and overwrite["path"] != destination:
                        overwrite["path"] = destination
                        status.text = "This file exists. Press Save backup again to replace it."
                        return
                    with Path(source).open("rb") as stream:
                        path = copy_document(stream, destination)
                else:
                    if not chooser.selection or not Path(chooser.selection[0]).is_file():
                        raise ValueError("Choose a backup file first.")
                    path = Path(chooser.selection[0])
                popup.dismiss()
                callback(path, None)
            except (OSError, ValueError) as error:
                status.text = str(error)

        choose.bind(on_release=selected)
        body.add_widget(Action(text="Cancel", on_release=popup.dismiss))
        popup.open()

    def _android(self, callback, source):
        if self.pending:
            callback(None, "A document chooser is already open.")
            return
        from android import activity
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        intent = Intent(Intent.ACTION_CREATE_DOCUMENT if source else Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        # Some providers classify JSON as text/plain or application/octet-stream.
        intent.setType("application/json" if source else "*/*")
        if source:
            intent.putExtra(Intent.EXTRA_TITLE, Path(source).name)
        self.pending = (callback, source)
        activity.bind(on_activity_result=self._android_result)

        @run_on_ui_thread
        def launch():
            if self.closed or not self.pending:
                return
            try:
                autoclass("org.kivy.android.PythonActivity").mActivity.startActivityForResult(
                    intent, 7105
                )
            except Exception:
                activity.unbind(on_activity_result=self._android_result)
                self.pending = None
                Clock.schedule_once(
                    lambda _: callback(None, "The system document chooser could not be opened."), 0
                )

        launch()

    def _android_result(self, request, result, intent):
        if request != 7105 or not self.pending:
            return
        from android import activity
        from jnius import autoclass

        activity.unbind(on_activity_result=self._android_result)
        callback, source = self.pending
        self.pending = None
        if result != -1 or intent is None:
            return
        uri = intent.getData()

        def transfer():
            descriptor = None
            try:
                resolver = autoclass(
                    "org.kivy.android.PythonActivity"
                ).mActivity.getContentResolver()
                descriptor = resolver.openFileDescriptor(uri, "rwt" if source else "r")
                if descriptor is None:
                    raise OSError("Document could not be opened.")
                fd = descriptor.detachFd()
                with os.fdopen(fd, "wb" if source else "rb") as stream:
                    if source:
                        with Path(source).open("rb") as saved:
                            while chunk := saved.read(65536):
                                stream.write(chunk)
                        stream.flush()
                        path = Path(source)
                    else:
                        path = Path(self.app.user_data_dir) / "incoming-backup.json"
                        copy_document(stream, path)
                error = None
            except Exception:
                path, error = None, "Document transfer failed. The local journal was not changed."
            finally:
                if descriptor:
                    descriptor.close()

            def finished(_):
                if not self.closed:
                    callback(path, error)

            Clock.schedule_once(finished, 0)

        Thread(target=transfer, daemon=True).start()
