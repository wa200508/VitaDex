"""Android's permission-free document picker; camera permission is requested separately."""

PHOTO_REQUEST = 4817


class AndroidPhotoPicker:
    def __init__(self, schedule):
        self.schedule = schedule
        self.pending = False

    def select(self, on_selected, on_error):
        from android import activity
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        if self.pending:
            return
        self.pending = True

        def result(request, status, intent):
            if request != PHOTO_REQUEST:
                return
            self.cancel()
            if status == -1 and intent is not None and intent.getData() is not None:
                uri = str(intent.getData().toString())
                self.schedule(lambda: on_selected(uri))

        self.callback = result
        activity.bind(on_activity_result=result)

        @run_on_ui_thread
        def launch():
            try:
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.setType('image/*')
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                autoclass('org.kivy.android.PythonActivity').mActivity.startActivityForResult(
                    intent, PHOTO_REQUEST,
                )
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
