import os
from pathlib import Path

# Disable Kivy Inspector to prevent red dots on right-click
os.environ['KIVY_INSPECTOR'] = '0'

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
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

from database import CARD_DB
from identification import DEFAULT_SAFETY_MESSAGE, DemoIdentificationService, IdentificationResult
from journal import JournalError, JournalRepository, JournalSession


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


def show_message(title, message):
    content = BoxLayout(orientation='vertical', padding=12, spacing=12)
    body = BoxLayout(orientation='vertical')
    body.add_widget(build_wrapped_label(message, height=100))
    content.add_widget(scrollable_layout(body))
    popup = Popup(title=title, content=content, size_hint=(0.94, 0.8))
    content.add_widget(OutlineButton(
        text='Close', size_hint_y=None, height=56, on_release=lambda *_: popup.dismiss(),
    ))
    app = App.get_running_app()
    if app is not None:
        app.active_popup = popup
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


class CardTile(ButtonBehavior, BoxLayout):
    def __init__(self, card, on_open, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', 14)
        kwargs.setdefault('spacing', 6)
        super().__init__(**kwargs)
        self.card = card
        self.on_open = on_open
        with self.canvas.before:
            Color(0.06, 0.1, 0.18, 1)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
            Color(0.2, 0.45, 0.85, 0.35)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=1.4)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.add_widget(Label(
            text=card.card_art,
            color=(1, 1, 1, 1),
            font_size='34sp',
            size_hint=(1, None),
            height=62,
            halign='center',
            valign='middle',
            text_size=(self.width - 28, None),
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
            text=f'{card.organism.type} • {card.organism.rarity}',
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
            Color(0.06, 0.1, 0.18, 0.96)
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
        self.add_widget(self.details_label)
        self.add_widget(self.stats_label)
        for label in (self.title_label, self.meta_label, self.details_label, self.stats_label):
            label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
            label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1] + 16))

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
        self.meta_label.text = f'{card.organism.type} • {card.organism.rarity} • {card.background.name}'
        self.details_label.text = (
            f'{card.organism.description}\n\nMoves: {", ".join(card.selected_moves)}'
            f'\n\n{DEFAULT_SAFETY_MESSAGE}'
        )
        self.stats_label.text = (
            f'Habitat: {card.selected_details["Habitat"]}\n'
            f'Size: {card.selected_details["Size"]}\n'
            f'Role: {card.organism.environment_role}\n'
            f'Notes: {card.organism.notes or "None"}'
        )


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='home', **kwargs)
        layout = styled_layout(BoxLayout(orientation='vertical', padding=20, spacing=18))

        layout.add_widget(Label(
            text='VitaDex',
            color=(1, 1, 1, 1),
            font_size='36sp',
            bold=True,
            size_hint=(1, None),
            height=60,
            halign='center',
            valign='middle',
            text_size=(Window.width - 40, None),
        ))

        layout.add_widget(build_wrapped_label(
            'Explore the VitaDex demo and collect sample cards. The sample creatures are fictional; this demo cannot identify wildlife.',
            font_size='17sp',
            height=140,
        ))

        button_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=170, spacing=12)
        button_layout.add_widget(OutlineButton(
            text='Try Demo',
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

        layout.add_widget(button_layout)

        feature_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        feature_box.bind(minimum_height=feature_box.setter('height'))
        feature_box.add_widget(Label(
            text='• Fictional sample creatures for exploring the card book',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• Sample cards are saved on this device',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• Observe wildlife from a safe distance; ask an adult for help',
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

    def goto_card_book(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'cardbook'


class ScanScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='scan', **kwargs)
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
            'Create a randomly chosen sample card. These creatures are fictional and do not identify anything around you. '
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
        result = app.identification_service.identify()
        candidate = result.top_candidate
        if result.source != 'demo' and not result.has_confident_match:
            self.show_no_match(result)
            return

        if candidate is None:
            self.show_no_match(result)
            return
        organism = candidate.organism
        card = CARD_DB.build_card(organism)
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
            'This fictional sample was chosen at random. It is not a wildlife identification.',
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
        App.get_running_app().active_popup = popup
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
        popup.open()
        app = App.get_running_app()
        app.active_popup = popup

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
        # Disable Kivy Inspector (prevents red dots on right-click)
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_keyboard)
        
        Window.clearcolor = (0, 0, 0, 1)
        self.journal_repository = JournalRepository(
            Path(self.user_data_dir) / 'journal.sqlite3',
            legacy_path=Path(self.user_data_dir) / 'journal.json',
        )
        self.identification_service = DemoIdentificationService(CARD_DB)
        self.journal_session = JournalSession(self.journal_repository)
        self.cards = self.journal_session.cards
        self.new_cards = []
        self.active_popup = None
        self.home_screen = HomeScreen()
        self.scan_screen = ScanScreen()
        self.card_book_screen = CardBookScreen()

        for card in self.cards:
            self.card_book_screen.add_card(card)

        manager = ScreenManager()
        manager.add_widget(self.home_screen)
        manager.add_widget(self.scan_screen)
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

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # Android Back / desktop Escape
            if self.active_popup is not None and self.active_popup.parent is not None:
                self.active_popup.dismiss()
                self.active_popup = None
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
