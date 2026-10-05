import os
from pathlib import Path

# Disable Kivy Inspector to prevent red dots on right-click
os.environ['KIVY_INSPECTOR'] = '0'

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.logger import Logger
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.utils import platform
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

from database import CARD_DB, NATURE_DB
from identification import DEFAULT_SAFETY_MESSAGE, DemoIdentificationService, IdentificationResult
from journal import JournalError, JournalRepository, JournalSession
from local_model import LocalIdentificationService
from photos import PhotoStore
from scan_jobs import ScanWorker
from android_photos import AndroidPhotoPicker
from build_identity import build_identity
from field_guide import TOPICS, introduction, read_topic


def build_wrapped_label(text, font_size='18sp', height=140):
    label = Label(
        text=text,
        font_size=font_size,
        color=(1, 1, 1, 1),
        halign='center',
        valign='middle',
        size_hint=(1, None),
        height=height,
        text_size=(Window.width - 40, None),
    )

    def update_text_size(_, width):
        label.text_size = (width, None)

    label.bind(width=update_text_size)
    label.bind(texture_size=lambda instance, size: setattr(instance, 'height', max(height, size[1] + 16)))
    return label


def scrollable_layout(layout):
    layout.size_hint_y = None
    layout.bind(minimum_height=layout.setter('height'))
    scroll = ScrollView(do_scroll_x=False)
    scroll.add_widget(layout)
    return scroll


def track_popup(popup):
    app = App.get_running_app()
    if app is None:
        return
    previous = getattr(app, 'active_popup', None)
    app.active_popup = popup

    def dismissed(*_):
        if app.active_popup is popup:
            app.active_popup = previous if previous is not None and previous.parent is not None else None

    popup.bind(on_dismiss=dismissed)


def show_message(title, message):
    content = BoxLayout(orientation='vertical', padding=12, spacing=12)
    body = BoxLayout(orientation='vertical')
    body.add_widget(build_wrapped_label(message, height=100))
    content.add_widget(scrollable_layout(body))
    popup = Popup(title=title, content=content, size_hint=(0.94, 0.8))
    content.add_widget(OutlineButton(
        text='Close', size_hint_y=None, height=56, on_release=lambda *_: popup.dismiss(),
    ))
    track_popup(popup)
    popup.open()


def styled_layout(layout):
    with layout.canvas.before:
        Color(0.03, 0.05, 0.1, 1)
        layout._bg_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[24])
        Color(0.08, 0.14, 0.22, 1)
        layout._bg_border = Line(rounded_rectangle=(layout.x, layout.y, layout.width, layout.height, 24), width=2)

    def update_layout(_, __):
        layout._bg_rect.pos = layout.pos
        layout._bg_rect.size = layout.size
        layout._bg_border.rounded_rectangle = (layout.x, layout.y, layout.width, layout.height, 24)

    layout.bind(pos=update_layout, size=update_layout)
    return layout


class OutlineButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('color', (1, 1, 1, 1))
        kwargs.setdefault('font_size', '16sp')
        kwargs.setdefault('bold', True)
        kwargs.setdefault('markup', False)
        kwargs.setdefault('padding', (16, 12))
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.05, 0.1, 0.2, 0.95)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
            Color(0.3, 0.6, 0.92, 0.35)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=1.4)
        with self.canvas.after:
            self._flash_color = Color(1, 0.84, 0.2, 0)
            self._flash_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=2)
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 20)
        self._flash_line.rounded_rectangle = (self.x, self.y, self.width, self.height, 20)

    def flash(self):
        anim = Animation(a=1, d=0.15) + Animation(a=0, d=0.85)
        anim.start(self._flash_color)



def card_photo_path(card):
    root = Path(App.get_running_app().user_data_dir).resolve()
    for asset in (card.local_art_asset, card.photo_asset):
        if asset:
            photo = (root / asset).resolve()
            if photo.is_relative_to(root) and photo.is_file():
                return photo
    return None


def card_background_color(card):
    return {
        'emerald': (0.03, 0.18, 0.12, 1),
        'blue': (0.04, 0.12, 0.24, 1),
        'gold': (0.22, 0.15, 0.04, 1),
    }.get(card.background.style, (0.06, 0.1, 0.18, 1))

class CardTile(ButtonBehavior, BoxLayout):
    def __init__(self, card, on_open, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', 14)
        kwargs.setdefault('spacing', 6)
        super().__init__(**kwargs)
        self.card = card
        self.on_open = on_open
        with self.canvas.before:
            Color(*card_background_color(card))
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
            Color(0.2, 0.45, 0.85, 0.35)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=1.4)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        photo = card_photo_path(card)
        if photo is not None:
            self.add_widget(Image(source=str(photo), size_hint_y=None, height=82, fit_mode='contain'))
        else:
            self.add_widget(Label(
                text='Fictional sample' if card.organism.is_demo else 'Photo unavailable',
                font_size='16sp', size_hint_y=None, height=82,
            ))
        self.add_widget(Label(
            text=card.title,
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True,
            size_hint=(1, None),
            height=34,
            halign='center',
            valign='middle',
            text_size=(self.width - 28, None),
        ))
        self.add_widget(Label(
            text=f'{card.organism.type} • {"Demo" if card.organism.is_demo else "Suggested"}',
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            size_hint=(1, None),
            height=24,
            halign='center',
            valign='middle',
            text_size=(self.width - 28, None),
        ))

    def update_graphics(self, *args):
        for child in self.children:
            if isinstance(child, Label):
                child.text_size = (max(1, self.width - 28), None)
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 20)

    def on_release(self):
        self.on_open(self.card)


class CardDetailView(BoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', 16)
        kwargs.setdefault('spacing', 10)
        super().__init__(**kwargs)
        self.card = None
        with self.canvas.before:
            self._background_color = Color(0.06, 0.1, 0.18, 0.96)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[24])
            Color(0.2, 0.45, 0.85, 0.2)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 24), width=2)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.title_label = Label(
            text='',
            color=(1, 1, 1, 1),
            font_size='22sp',
            bold=True,
            size_hint=(1, None),
            height=36,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.65 - 32, None),
        )
        self.meta_label = Label(
            text='',
            color=(0.75, 0.9, 1, 1),
            font_size='14sp',
            size_hint=(1, None),
            height=24,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.65 - 32, None),
        )
        self.details_label = Label(
            text='',
            color=(1, 1, 1, 1),
            font_size='14sp',
            halign='left',
            valign='top',
            size_hint=(1, None),
            height=150,
            text_size=(Window.width * 0.65 - 32, None),
        )
        self.stats_label = Label(
            text='',
            color=(0.8, 0.92, 1, 1),
            font_size='13sp',
            halign='left',
            valign='top',
            size_hint=(1, None),
            height=100,
            text_size=(Window.width * 0.65 - 32, None),
        )
        self.add_widget(self.title_label)
        self.add_widget(self.meta_label)
        self.photo = Image(size_hint_y=None, height=0, fit_mode='contain')
        self.add_widget(self.photo)
        self.add_widget(self.details_label)
        self.add_widget(self.stats_label)
        self.add_widget(OutlineButton(text='Explore this organism', size_hint_y=None,
                                      height=48, on_release=self.open_guide))
        for label in (self.title_label, self.meta_label, self.details_label, self.stats_label):
            label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
            label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1] + 16))

    def open_guide(self, *_):
        if self.card is None:
            return
        entry = self.card.organism
        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        body = BoxLayout(orientation='vertical', spacing=12)
        reading = build_wrapped_label(introduction(entry), height=140)
        body.add_widget(reading)
        for topic, question in TOPICS.items():
            button = OutlineButton(text=question, size_hint_y=None, height=52)
            button.bind(on_release=lambda _, key=topic: setattr(reading, 'text', read_topic(entry, key)))
            body.add_widget(button)
        body.add_widget(build_wrapped_label(
            'Read from the local field guide. Voice and open-ended discussion are not available yet.',
            font_size='14sp', height=70,
        ))
        content.add_widget(scrollable_layout(body))
        popup = Popup(title=f'Field Guide: {entry.name}', content=content, size_hint=(0.94, 0.94))
        content.add_widget(OutlineButton(text='Close', size_hint_y=None, height=48,
                                        on_release=lambda *_: popup.dismiss()))
        track_popup(popup)
        popup.open()

    def update_graphics(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 24)

    def set_card(self, card):
        self.card = card
        if not card:
            self.title_label.text = 'No card selected'
            self.meta_label.text = ''
            self.details_label.text = 'Tap a card from the stack to view it here.'
            self.stats_label.text = ''
            return
        self.title_label.text = card.title
        self._background_color.rgba = card_background_color(card)
        provenance = 'Fictional demo' if card.organism.is_demo else 'Suggested category; not verified'
        review = '' if card.organism.is_demo else f' • Facts: {card.organism.review_status}'
        self.meta_label.text = f'{card.organism.type} • {provenance}{review}'
        photo = card_photo_path(card)
        self.photo.source = str(photo) if photo is not None else ''
        self.photo.height = 220 if photo is not None else 0
        self.details_label.text = (
            introduction(card.organism)
            + f'\n\n{card.organism.safety_message} {DEFAULT_SAFETY_MESSAGE}'
        )
        self.stats_label.text = (
            f'Habitat: {card.selected_details["Habitat"]}\n'
            f'Size: {card.selected_details["Size"]}\n'
            f'Role: {card.organism.environment_role}\n'
            f'Notes: {card.organism.notes or "None"}\n'
            f'Recorded: {card.observed_at or "Not recorded"}'
        )


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='home', **kwargs)
        layout = styled_layout(BoxLayout(orientation='vertical', padding=20, spacing=18))
        app_title, test_notice = build_identity()

        layout.add_widget(Label(
            text=app_title,
            color=(1, 1, 1, 1),
            font_size='36sp',
            bold=True,
            size_hint=(1, None),
            height=60,
            halign='center',
            valign='middle',
            text_size=(Window.width - 40, None),
        ))

        if test_notice:
            layout.add_widget(build_wrapped_label(test_notice, font_size='14sp', height=32))

        layout.add_widget(build_wrapped_label(
            'Explore nature with local photo suggestions and your personal card book. Suggestions can be wrong; observe safely and verify with a trusted field guide.',
            font_size='17sp',
            height=140,
        ))

        button_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=240, spacing=12)
        button_layout.add_widget(OutlineButton(
            text='Scan a Photo',
            size_hint=(1, None),
            height=72,
            on_release=self.goto_scan,
        ))
        self.collection_button = OutlineButton(
            text='Card Book',
            size_hint=(1, None),
            height=72,
            on_release=self.goto_card_book,
        )
        button_layout.add_widget(self.collection_button)
        button_layout.add_widget(OutlineButton(
            text='Try Fictional Demo', size_hint_y=None, height=60, on_release=self.goto_demo,
        ))

        layout.add_widget(button_layout)

        feature_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        feature_box.bind(minimum_height=feature_box.setter('height'))
        feature_box.add_widget(Label(
            text='• Photo processing stays on this device',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• No microphone, location, or account needed',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• Observe living things from a safe distance; ask an adult for help',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))

        for child in feature_box.children:
            child.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
            child.bind(texture_size=lambda instance, size: setattr(instance, 'height', max(28, size[1] + 12)))

        layout.add_widget(feature_box)
        self.add_widget(scrollable_layout(layout))
        self.update_new_card_badge()

    def update_new_card_badge(self):
        app = App.get_running_app()
        count = len(getattr(app, 'new_cards', []))
        if count:
            self.collection_button.text = f'Card Book  •  {count} new'
        else:
            self.collection_button.text = 'Card Book'

    def goto_scan(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'scan'

    def goto_demo(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'demo'

    def goto_card_book(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'cardbook'


class ScanScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='scan', **kwargs)
        self.camera = None
        self.camera_popup = None
        self.review_popup = None
        layout = styled_layout(BoxLayout(orientation='vertical', padding=20, spacing=16))
        layout.add_widget(build_wrapped_label('Scan a Photo', font_size='28sp', height=50))
        layout.add_widget(build_wrapped_label(
            'Choose a photo or take one. VitaDex processes it locally and suggests a category '
            'from a small starter catalog. It cannot identify every organism or tell you what is safe '
            'to touch or eat. ' + DEFAULT_SAFETY_MESSAGE, height=100,
        ))
        self.status = build_wrapped_label('Ready to choose a photo.', font_size='16sp', height=50)
        layout.add_widget(self.status)
        self.pick_button = OutlineButton(
            text='Choose Photo', size_hint_y=None, height=60, on_release=self.choose_photo,
        )
        self.capture_button = OutlineButton(
            text='Take Photo', size_hint_y=None, height=60, on_release=self.capture_photo,
        )
        layout.add_widget(self.pick_button)
        layout.add_widget(self.capture_button)
        layout.add_widget(OutlineButton(
            text='Back to Home', size_hint_y=None, height=60, on_release=self.goto_home,
        ))
        self.add_widget(scrollable_layout(layout))

    def set_busy(self, busy):
        self.pick_button.disabled = busy
        self.capture_button.disabled = busy

    def choose_photo(self, *_):
        app = App.get_running_app()
        if platform == 'android':
            app.photo_picker.select(self.process_photo, lambda error: show_message('Photo unavailable', error))
            return
        content = BoxLayout(orientation='vertical', spacing=12)
        chooser = FileChooserIconView(filters=['*.jpg', '*.jpeg', '*.png', '*.webp'], multiselect=False)
        content.add_widget(chooser)
        buttons = BoxLayout(size_hint_y=None, height=56, spacing=12)
        popup = Popup(title='Choose Photo', content=content, size_hint=(0.94, 0.94))

        def selected(*_):
            if chooser.selection:
                path = chooser.selection[0]
                popup.dismiss()
                self.process_photo(path)

        buttons.add_widget(OutlineButton(text='Use Photo', on_release=selected))
        buttons.add_widget(OutlineButton(text='Cancel', on_release=lambda *_: popup.dismiss()))
        content.add_widget(buttons)
        track_popup(popup)
        popup.open()

    def capture_photo(self, *_):
        if platform == 'android':
            from android.permissions import Permission, check_permission, request_permissions
            if not check_permission(Permission.CAMERA):
                def permission_result(_permissions, grants):
                    def show():
                        if self.manager.current != 'scan':
                            return
                        if grants and all(grants):
                            self.open_camera()
                        else:
                            show_message('Camera access declined', 'You can still choose a photo or browse your card book.')
                    Clock.schedule_once(lambda _: show(), 0)
                request_permissions([Permission.CAMERA], permission_result)
                return
        self.open_camera()

    def open_camera(self):
        from kivy.uix.camera import Camera
        try:
            self.camera = Camera(play=True, resolution=(640, 480))
        except Exception as error:
            self.release_camera()
            show_message('Camera unavailable', f'You can choose an existing photo instead. {error}')
            return
        content = BoxLayout(orientation='vertical', spacing=12)
        content.add_widget(self.camera)
        caption = build_wrapped_label('Keep a safe distance. Wait for the camera preview.', height=50)
        content.add_widget(caption)
        buttons = BoxLayout(size_hint_y=None, height=56, spacing=12)
        popup = Popup(title='Take Photo', content=content, size_hint=(0.94, 0.94))
        self.camera_popup = popup
        temporary = Path(App.get_running_app().user_data_dir) / 'capture.png'

        def capture(*_):
            if self.camera is None or self.camera.texture is None:
                caption.text = 'The camera is not ready. Choose Cancel to use an existing photo.'
                return
            try:
                self.camera.export_to_png(str(temporary))
                popup.dismiss()
                self.process_photo(temporary, delete_source=True)
            except Exception as error:
                caption.text = f'Could not capture a photo: {error}'

        buttons.add_widget(OutlineButton(text='Capture', on_release=capture))
        buttons.add_widget(OutlineButton(text='Cancel', on_release=lambda *_: popup.dismiss()))
        content.add_widget(buttons)
        popup.bind(on_dismiss=lambda *_: self.release_camera())
        track_popup(popup)
        popup.open()

    def release_camera(self):
        if self.camera is not None:
            camera, self.camera = self.camera, None
            camera.play = False
            provider = camera._camera
            if platform == 'android' and provider is not None:
                # Kivy 2.3.1 stops preview on play=False but releases Android hardware
                # only in its provider destructor. Release it now on pause/dismiss.
                provider.unbind(on_texture=camera.on_tex)
                provider._release_camera()
                camera._camera = None
        if self.camera_popup is not None:
            popup, self.camera_popup = self.camera_popup, None
            popup.dismiss()

    def process_photo(self, source, delete_source=False):
        if self.manager.current != 'scan':
            return
        app = App.get_running_app()

        def clean_source():
            if delete_source:
                Path(source).unlink(missing_ok=True)

        def done(encounter, result):
            clean_source()
            self.set_busy(False)
            self.status.text = 'Local processing finished.'
            if not result.has_confident_match:
                app.photo_store.discard(encounter)
                show_message('Keep observing', 'No clear suggestion in the starter catalog. Try a clear photo of one organism. ' + result.safety_message)
                return
            self.review_match(encounter, result)

        def failed(error):
            clean_source()
            self.set_busy(False)
            self.status.text = 'Photo processing could not finish.'
            show_message('Scan unavailable', str(error))

        def cancelled():
            clean_source()
            self.set_busy(False)
            self.status.text = 'Scan cancelled. Your photo was not added to the journal.'

        if app.scan_worker.start(source, done, failed, cancelled):
            self.set_busy(True)
            self.status.text = 'Processing on this device…'

    def review_match(self, encounter, result):
        app = App.get_running_app()
        candidate = result.top_candidate
        card = NATURE_DB.build_card(candidate.organism)
        card.encounter_id = encounter.id
        card.observed_at = encounter.observed_at
        card.photo_asset = str(encounter.photo_path.relative_to(Path(app.user_data_dir)))
        if encounter.art_path is not None:
            card.local_art_asset = str(encounter.art_path.relative_to(Path(app.user_data_dir)))
        card.identification_source = result.source
        card.confidence = candidate.confidence
        content = BoxLayout(orientation='vertical', padding=12, spacing=12)
        body = BoxLayout(orientation='vertical', spacing=12)
        body.add_widget(build_wrapped_label(
            'Suggested category, not a verified identification. Compare it with what you saw. '
            'Saving this card records the suggestion, not proof of the species.', height=60,
        ))
        detail = CardDetailView()
        detail.set_card(card)
        detail.size_hint_y = None
        detail.bind(minimum_height=detail.setter('height'))
        body.add_widget(detail)
        content.add_widget(scrollable_layout(body))
        buttons = BoxLayout(orientation='vertical', size_hint_y=None, height=174, spacing=8)
        content.add_widget(buttons)
        popup = Popup(title='Review Suggested Match', content=content, size_hint=(0.94, 0.94))
        saved = False

        def save(*_):
            nonlocal saved
            if saved:
                return
            try:
                app.journal_session.add_card(card)
            except JournalError as error:
                show_message('Card not saved', str(error))
                return
            saved = True
            app.new_cards.append(card)
            app.card_book_screen.add_card(card)
            app.home_screen.update_new_card_badge()
            self.status.text = 'Suggested encounter saved on this device.'
            popup.dismiss()
            self.goto_home()

        def dismissed(*_):
            self.review_popup = None
            if not saved:
                app.photo_store.discard(encounter)

        def toggle_art(button):
            if card.local_art_asset:
                card.local_art_asset = ''
                button.text = 'Use cartoon artwork'
            elif encounter.art_path is not None:
                card.local_art_asset = str(encounter.art_path.relative_to(Path(app.user_data_dir)))
                button.text = 'Use original photo'
            detail.set_card(card)

        buttons.add_widget(OutlineButton(text='Use original photo', on_release=toggle_art))
        buttons.add_widget(OutlineButton(text='Save Suggested Card', on_release=save))
        buttons.add_widget(OutlineButton(text='Discard', on_release=lambda *_: popup.dismiss()))
        popup.bind(on_dismiss=dismissed)
        self.review_popup = popup
        track_popup(popup)
        popup.open()

    def on_leave(self, *_):
        App.get_running_app().scan_worker.cancel()
        self.release_camera()
        if self.review_popup is not None:
            self.review_popup.dismiss()

    def goto_home(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class DemoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='demo', **kwargs)
        layout = styled_layout(BoxLayout(orientation='vertical', padding=20, spacing=18))

        layout.add_widget(Label(
            text='Demo Cards',
            color=(1, 1, 1, 1),
            font_size='28sp',
            size_hint=(1, None),
            height=50,
            halign='left',
            valign='middle',
            text_size=(Window.width - 40, None),
        ))

        layout.add_widget(build_wrapped_label(
            'Create a randomly chosen sample card. These organisms are fictional and do not identify anything around you. '
            + DEFAULT_SAFETY_MESSAGE,
            font_size='17sp',
            height=160,
        ))

        layout.add_widget(OutlineButton(
            text='Create Sample Card',
            size_hint=(1, None),
            height=68,
            on_release=self.perform_scan,
        ))
        layout.add_widget(OutlineButton(
            text='Back to Home',
            size_hint=(1, None),
            height=68,
            on_release=self.goto_home,
        ))
        self.add_widget(scrollable_layout(layout))

    def perform_scan(self, _=None):
        app = App.get_running_app()
        result = app.demo_identification_service.identify()
        candidate = result.top_candidate
        if result.source != 'demo' and not result.has_confident_match:
            self.show_no_match(result)
            return

        if candidate is None:
            self.show_no_match(result)
            return
        organism = candidate.organism
        card = CARD_DB.build_card(organism)
        card.identification_source = 'demo'
        try:
            app.journal_session.add_card(card)
        except JournalError as error:
            show_message('Card not saved', str(error))
            return
        app.new_cards.append(card)
        app.card_book_screen.add_card(card)
        self.show_card_preview(card)

    def show_no_match(self, result: IdentificationResult):
        message = 'VitaDex could not find a match for this encounter.'
        if result.top_candidate is not None:
            message = 'VitaDex is not confident enough to identify this encounter.'

        show_message('Keep observing', f'{message} {result.safety_message}')

    def show_card_preview(self, card):
        content = BoxLayout(orientation='vertical', padding=12, spacing=12)
        body = BoxLayout(orientation='vertical', spacing=12)
        body.add_widget(build_wrapped_label(
            'This fictional sample was chosen at random. It is not an organism identification.',
            height=60,
        ))
        detail = CardDetailView()
        detail.set_card(card)
        detail.size_hint_y = None
        detail.bind(minimum_height=detail.setter('height'))
        body.add_widget(detail)
        content.add_widget(scrollable_layout(body))
        popup = Popup(title='Sample card saved', content=content, size_hint=(0.94, 0.94))
        content.add_widget(OutlineButton(
            text='Back to Home', size_hint_y=None, height=56,
            on_release=lambda *_: popup.dismiss(),
        ))

        def on_dismiss(*_):
            app = App.get_running_app()
            app.home_screen.update_new_card_badge()
            app.home_screen.collection_button.flash()
            self.goto_home()

        popup.bind(on_dismiss=on_dismiss)
        track_popup(popup)
        popup.open()

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class CardBookScreen(Screen):
    cards = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(name='cardbook', **kwargs)
        root = styled_layout(BoxLayout(orientation='vertical', padding=16, spacing=12))

        header = BoxLayout(size_hint=(1, None), height=54, spacing=10)
        header.add_widget(OutlineButton(
            text='‹  Home',
            font_size='16sp',
            size_hint=(None, 1),
            width=110,
            on_release=self.goto_home,
        ))
        header.add_widget(Label(
            text='My Card Book',
            color=(1, 1, 1, 1),
            font_size='25sp',
            bold=True,
            halign='center',
            valign='middle',
            text_size=(Window.width - 160, None),
        ))
        root.add_widget(header)

        self.collection_status = Label(
            color=(0.72, 0.85, 1, 1),
            font_size='15sp',
            size_hint=(1, None),
            height=24,
            halign='left',
            valign='middle',
        )
        root.add_widget(self.collection_status)

        controls = BoxLayout(orientation='vertical', size_hint=(1, None), height=174, spacing=8)
        controls.add_widget(OutlineButton(
            text='Sort A–Z',
            on_release=self.sort_by_name,
        ))
        controls.add_widget(OutlineButton(
            text='Sort by type',
            on_release=self.sort_by_type,
        ))
        self.mark_seen_button = OutlineButton(
            text='Mark new as seen',
            on_release=self.put_away_cards,
        )
        controls.add_widget(self.mark_seen_button)
        root.add_widget(controls)

        self.tiles_area = GridLayout(
            cols=2,
            spacing=12,
            padding=(2, 6),
            size_hint=(1, None),
            row_default_height=188,
            row_force_default=True,
        )
        self.tiles_area.bind(minimum_height=self.tiles_area.setter('height'))
        self.tiles_area.bind(width=lambda instance, width: setattr(instance, 'cols', max(1, int(width / 220))))
        tiles_scroll = ScrollView(size_hint=(1, 1), bar_width=8)
        tiles_scroll.add_widget(self.tiles_area)
        root.add_widget(tiles_scroll)

        self.add_widget(root)

    def add_card(self, card):
        self.cards.append(card)
        self.refresh_cards()

    def open_fullscreen_card(self, card):
        content = BoxLayout(orientation='vertical', padding=20, spacing=14)
        detail = CardDetailView(size_hint=(1, 1))
        detail.set_card(card)
        content.add_widget(scrollable_layout(detail))
        content.add_widget(OutlineButton(
            text='Close', size_hint_y=None, height=56, on_release=lambda *_: popup.dismiss(),
        ))
        popup = Popup(title=card.title, content=content, size_hint=(0.96, 0.96), auto_dismiss=True)
        track_popup(popup)
        popup.open()

    def refresh_cards(self):
        app = App.get_running_app()
        self.tiles_area.clear_widgets()
        new_count = len(app.new_cards)
        self.collection_status.text = f'{len(self.cards)} discoveries'
        if new_count:
            self.collection_status.text += f'  •  {new_count} new'
        self.mark_seen_button.disabled = not new_count

        if not self.cards:
            self.tiles_area.add_widget(Label(
                text='No cards yet. Try the demo to add a sample card.',
                color=(1, 1, 1, 1),
                font_size='16sp',
                halign='center',
                valign='middle',
                size_hint=(1, None),
                height=200,
                text_size=(Window.width - 40, None),
            ))
            return

        for card in self.cards:
            self.tiles_area.add_widget(CardTile(card, on_open=self.open_fullscreen_card))

    def on_enter(self, *args):
        self.refresh_cards()

    def put_away_cards(self, _=None):
        app = App.get_running_app()
        app.new_cards.clear()
        self.refresh_cards()
        app.home_screen.update_new_card_badge()

    def sort_by_name(self, _=None):
        self.cards.sort(key=lambda card: card.organism.name)
        self.refresh_cards()

    def sort_by_type(self, _=None):
        self.cards.sort(key=lambda card: (card.organism.type, card.organism.name))
        self.refresh_cards()

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class VitaDexApp(App):
    def build(self):
        self.title = build_identity()[0]
        # Disable Kivy Inspector (prevents red dots on right-click)
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_keyboard)
        
        Window.clearcolor = (0, 0, 0, 1)
        self.journal_repository = JournalRepository(
            Path(self.user_data_dir) / 'journal.sqlite3',
            legacy_path=Path(self.user_data_dir) / 'journal.json',
        )
        self.demo_identification_service = DemoIdentificationService(CARD_DB)
        self.identification_service = LocalIdentificationService(NATURE_DB)
        self.photo_store = PhotoStore(Path(self.user_data_dir) / 'photos')
        schedule = lambda callback: Clock.schedule_once(lambda _: callback(), 0)
        self.scan_worker = ScanWorker(self.photo_store, self.identification_service, schedule)
        self.photo_picker = AndroidPhotoPicker(schedule)
        self.journal_session = JournalSession(self.journal_repository)
        self.cards = self.journal_session.cards
        self.new_cards = []
        self.active_popup = None
        self.home_screen = HomeScreen()
        self.scan_screen = ScanScreen()
        self.demo_screen = DemoScreen()
        self.card_book_screen = CardBookScreen()

        for card in self.cards:
            self.card_book_screen.add_card(card)

        manager = ScreenManager()
        manager.add_widget(self.home_screen)
        manager.add_widget(self.scan_screen)
        manager.add_widget(self.demo_screen)
        manager.add_widget(self.card_book_screen)
        return manager

    def on_start(self):
        if self.journal_session.error:
            Logger.error(f'VitaDex: {self.journal_session.error}')
            show_message(
                'Journal unavailable',
                'Your existing journal could not be read. Adding cards is disabled to keep '
                f'your saved discoveries safe. {self.journal_session.error}',
            )

    def on_pause(self):
        self.scan_worker.cancel()
        self.scan_screen.release_camera()
        if self.scan_screen.review_popup is not None:
            self.scan_screen.review_popup.dismiss()
        if self.active_popup is not None and self.active_popup.parent is not None:
            self.active_popup.dismiss()
        return True

    def on_stop(self):
        self.scan_worker.close()
        self.photo_picker.cancel()
        self.scan_screen.release_camera()
        if self.scan_screen.review_popup is not None:
            self.scan_screen.review_popup.dismiss()

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # Android Back / desktop Escape
            if self.active_popup is not None and self.active_popup.parent is not None:
                self.active_popup.dismiss()
                return True
            if self.root is not None and self.root.current != 'home':
                self.root.transition = SlideTransition(direction='right')
                self.root.current = 'home'
                return True
        # Block F1 which opens the inspector and Ctrl+E
        if key == 282:  # F1
            return True
        if key == 101 and 'ctrl' in modifier:  # Ctrl+E
            return True
        return False


if __name__ == '__main__':
    VitaDexApp().run()
