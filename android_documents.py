"""User-directed PDF destination selection, without broad storage permission."""

DOCUMENT_REQUEST = 4818


class AndroidDocumentPicker:
    def __init__(self, schedule):
        self.schedule = schedule
        self.pending = False

    def create(self, filename, on_selected, on_error, on_cancelled):
        from android import activity
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        if self.pending:
            raise RuntimeError('A document destination is already being selected.')
        self.pending = True

        def result(request, status, intent):
            if request != DOCUMENT_REQUEST:
                return
            self.cancel()
            if status == -1 and intent is not None and intent.getData() is not None:
                uri = str(intent.getData().toString())
                self.schedule(lambda: on_selected(uri))
            else:
                self.schedule(on_cancelled)

        self.callback = result
        activity.bind(on_activity_result=result)

        @run_on_ui_thread
        def launch():
            try:
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
                intent.setType('application/pdf')
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.putExtra(Intent.EXTRA_TITLE, filename)
                autoclass('org.kivy.android.PythonActivity').mActivity.startActivityForResult(
                    intent, DOCUMENT_REQUEST)
            except Exception as error:
                self.cancel()
                message = str(error)
                self.schedule(lambda: on_error(message))

        launch()

    def cancel(self):
        if self.pending:
            from android import activity
            activity.unbind(on_activity_result=self.callback)
            self.pending = False


def write_document(source, uri):
    from jnius import autoclass
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    autoclass('org.vitadex.PhotoIO').writeUri(activity, str(source), uri)
