import sys
from types import SimpleNamespace

from android_documents import AndroidDocumentPicker, DOCUMENT_REQUEST


def environment(monkeypatch):
    callbacks = {}
    launches = []
    class Intent:
        ACTION_CREATE_DOCUMENT = 'create-document'
        CATEGORY_OPENABLE = 'openable'
        EXTRA_TITLE = 'title'
        def __init__(self, action):
            self.action = action
        def setType(self, mime):
            self.mime = mime
        def addCategory(self, category):
            self.category = category
        def putExtra(self, key, value):
            self.filename = value
    activity = SimpleNamespace(bind=lambda **kw: callbacks.update(kw),
                               unbind=lambda **kw: callbacks.clear())
    host = SimpleNamespace(mActivity=SimpleNamespace(
        startActivityForResult=lambda intent, request: launches.append((intent, request))))
    monkeypatch.setitem(sys.modules, 'android', SimpleNamespace(activity=activity))
    monkeypatch.setitem(sys.modules, 'android.runnable', SimpleNamespace(run_on_ui_thread=lambda fn: fn))
    monkeypatch.setitem(sys.modules, 'jnius', SimpleNamespace(
        autoclass=lambda name: Intent if name == 'android.content.Intent' else host))
    return callbacks, launches


def test_picker_uses_pdf_system_save_and_delivers_selected_uri(monkeypatch):
    callbacks, launches = environment(monkeypatch)
    scheduled, received = [], []
    picker = AndroidDocumentPicker(scheduled.append)
    picker.create('vitadex-card.pdf', received.append, received.append, lambda: received.append('cancel'))
    intent, request = launches[0]
    assert intent.action == 'create-document'
    assert intent.mime == 'application/pdf'
    assert intent.filename == 'vitadex-card.pdf'
    assert request == DOCUMENT_REQUEST
    result = callbacks['on_activity_result']
    result(999, -1, None)
    assert picker.pending
    result(DOCUMENT_REQUEST, -1, SimpleNamespace(getData=lambda: SimpleNamespace(toString=lambda: 'content://chosen/pdf')))
    assert not picker.pending
    assert received == []
    scheduled.pop()()
    assert received == ['content://chosen/pdf']
    assert not callbacks


def test_picker_cancel_calls_cleanup_on_ui_scheduler(monkeypatch):
    callbacks, _ = environment(monkeypatch)
    scheduled, cancelled = [], []
    picker = AndroidDocumentPicker(scheduled.append)
    picker.create('card.pdf', lambda _: None, lambda _: None, lambda: cancelled.append(True))
    callbacks['on_activity_result'](DOCUMENT_REQUEST, 0, None)
    assert cancelled == []
    scheduled.pop()()
    assert cancelled == [True]
    assert not picker.pending
