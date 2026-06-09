import random

from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

from database import CARD_DB


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
    return label


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
        kwargs.setdefault('font_size', '20sp')
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.05, 0.1, 0.2, 0.9)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[24])
            Color(0.4, 0.75, 1, 0.35)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 24), width=1.5)
        with self.canvas.after:
            Color(1, 1, 1, 0.08)
            self._glow = RoundedRectangle(pos=(self.x + 12, self.y + self.height * 0.55), size=(self.width * 0.5, self.height * 0.22), radius=[18])
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 24)
        self._glow.pos = (self.x + 12, self.y + self.height * 0.55)
        self._glow.size = (self.width * 0.5, self.height * 0.22)


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
            'Scan creatures, collect cards, and build a nature collection that feels like a real card book.',
            font_size='17sp',
            height=140,
        ))

        button_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=280, spacing=16)
        button_layout.add_widget(OutlineButton(
            text='🔍 Start Scan',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_scan,
        ))
        self.collection_button = OutlineButton(
            text='📒 Card Book',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_card_book,
        )
        button_layout.add_widget(self.collection_button)

        layout.add_widget(button_layout)

        feature_box = BoxLayout(orientation='vertical', spacing=10)
        feature_box.add_widget(Label(
            text='• Easy scan flow for kids and grown-ups',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• Cards appear automatically after each scan',
            color=(1, 1, 1, 1),
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=28,
            text_size=(Window.width - 40, None),
        ))
        feature_box.add_widget(Label(
            text='• Black background, white text, and clear outlines for readability',
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

        layout.add_widget(feature_box)
        self.add_widget(layout)
        self.update_new_card_badge()

    def update_new_card_badge(self):
        app = App.get_running_app()
        count = len(getattr(app, 'new_cards', []))
        if count:
            self.collection_button.text = f'📒 Card Book  •  {count} new'
        else:
            self.collection_button.text = '📒 Card Book'

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
            text='Scan',
            color=(1, 1, 1, 1),
            font_size='28sp',
            size_hint=(1, None),
            height=50,
            halign='left',
            valign='middle',
            text_size=(Window.width - 40, None),
        ))

        layout.add_widget(build_wrapped_label(
            'Scan creatures and let VitaDex create the card for your collection. ' 
            'When the scan completes, you return to the main page with a new-card alert.',
            font_size='17sp',
            height=160,
        ))

        layout.add_widget(OutlineButton(
            text='🔍 Scan Now',
            size_hint=(1, None),
            height=120,
            on_release=self.perform_scan,
        ))
        layout.add_widget(OutlineButton(
            text='🏠 Back to Home',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_home,
        ))
        self.add_widget(layout)

    def perform_scan(self, _=None):
        app = App.get_running_app()
        organism = CARD_DB.get_random_organism()
        card = CARD_DB.build_card(organism)
        app.cards.append(card)
        app.new_cards.append(card)
        app.card_book_screen.add_card(card)
        self.show_scan_animation(card)

    def show_scan_animation(self, card):
        preview = FloatLayout(size_hint=(0.9, None), height=280, pos_hint={'center_x': 0.5, 'center_y': 0.55}, opacity=0)
        card_box = BoxLayout(orientation='vertical', padding=18, spacing=10, size_hint=(1, 1))
        with card_box.canvas.before:
            Color(0.08, 0.12, 0.2, 0.96)
            RoundedRectangle(pos=card_box.pos, size=card_box.size, radius=[24])
            Color(0.4, 0.75, 1, 0.12)
            Line(rounded_rectangle=(card_box.x, card_box.y, card_box.width, card_box.height, 24), width=2)

        def update_box(_, __):
            card_box.canvas.before.clear()
            with card_box.canvas.before:
                Color(0.08, 0.12, 0.2, 0.96)
                RoundedRectangle(pos=card_box.pos, size=card_box.size, radius=[24])
                Color(0.4, 0.75, 1, 0.12)
                Line(rounded_rectangle=(card_box.x, card_box.y, card_box.width, card_box.height, 24), width=2)

        card_box.bind(pos=update_box, size=update_box)

        card_box.add_widget(Label(
            text='New card created!',
            color=(1, 1, 1, 1),
            font_size='22sp',
            size_hint=(1, None),
            height=30,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8 - 40, None),
        ))
        card_box.add_widget(Label(
            text=card.background.preview,
            color=(1, 1, 1, 1),
            font_size='48sp',
            size_hint=(1, None),
            height=90,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8 - 40, None),
        ))
        card_box.add_widget(Label(
            text=card.title,
            color=(1, 1, 1, 1),
            font_size='24sp',
            bold=True,
            size_hint=(1, None),
            height=34,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8 - 40, None),
        ))
        card_box.add_widget(Label(
            text=f'{card.organism.type} • {card.organism.rarity} • {card.background.name}',
            color=(0.7, 0.85, 1, 1),
            font_size='16sp',
            size_hint=(1, None),
            height=26,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8 - 40, None),
        ))

        preview.add_widget(card_box)
        self.add_widget(preview)

        def on_animation_complete(*args):
            self.remove_widget(preview)
            app = App.get_running_app()
            app.home_screen.update_new_card_badge()
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'home'

        Animation(opacity=1, d=0.35).start(preview)
        anim = Animation(opacity=1, d=1.15) + Animation(opacity=0, d=0.35)
        anim.bind(on_complete=on_animation_complete)
        anim.start(preview)

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class CardBookScreen(Screen):
    cards = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(name='cardbook', **kwargs)
        layout = styled_layout(BoxLayout(orientation='vertical', padding=20, spacing=18))

        layout.add_widget(Label(
            text='Card Book',
            color=(1, 1, 1, 1),
            font_size='28sp',
            size_hint=(1, None),
            height=50,
            halign='left',
            valign='middle',
            text_size=(Window.width - 40, None),
        ))

        self.new_stack_area = FloatLayout(size_hint=(1, None), height=180)
        layout.add_widget(self.new_stack_area)

        control_row = BoxLayout(size_hint=(1, None), height=80, spacing=12)
        control_row.add_widget(OutlineButton(
            text='📥 Put away new cards',
            font_size='18sp',
            on_release=self.put_away_cards,
        ))
        control_row.add_widget(OutlineButton(
            text='🧩 Organize by type',
            font_size='18sp',
            on_release=self.sort_by_type,
        ))
        layout.add_widget(control_row)

        self.scroll_view = ScrollView()
        self.card_list = GridLayout(cols=2, spacing=16, size_hint_y=None, padding=(0, 10))
        self.card_list.bind(minimum_height=self.card_list.setter('height'))
        self.scroll_view.add_widget(self.card_list)

        layout.add_widget(self.scroll_view)
        layout.add_widget(OutlineButton(
            text='🏠 Back to Home',
            font_size='22sp',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_home,
        ))
        self.add_widget(layout)

    def add_card(self, card):
        self.cards.append(card)
        self.refresh_cards()

    def refresh_cards(self):
        app = App.get_running_app()
        self.new_stack_area.clear_widgets()

        if app.new_cards:
            self.new_stack_area.add_widget(Label(
                text=f'{len(app.new_cards)} new cards collected today',
                color=(1, 1, 1, 1),
                font_size='18sp',
                size_hint=(1, None),
                height=32,
                pos_hint={'top': 1},
                halign='left',
                valign='middle',
                text_size=(Window.width - 40, None),
            ))
            for index, card in enumerate(app.new_cards[-3:]):
                preview = FloatLayout(
                    size_hint=(None, None),
                    size=(Window.width * 0.38, 120),
                    pos=(index * 26, index * 16),
                )
                with preview.canvas.before:
                    Color(0.05, 0.1, 0.16, 1)
                    RoundedRectangle(pos=preview.pos, size=preview.size, radius=[20])
                    Color(0.2, 0.45, 0.85, 0.35)
                    Line(rounded_rectangle=(preview.x, preview.y, preview.width, preview.height, 20), width=1.4)
                def update_preview(_, __):
                    preview.canvas.before.clear()
                    with preview.canvas.before:
                        Color(0.05, 0.1, 0.16, 1)
                        RoundedRectangle(pos=preview.pos, size=preview.size, radius=[20])
                        Color(0.2, 0.45, 0.85, 0.35)
                        Line(rounded_rectangle=(preview.x, preview.y, preview.width, preview.height, 20), width=1.4)
                preview.bind(pos=update_preview, size=update_preview)
                preview.add_widget(Label(
                    text=card.card_art,
                    color=(1, 1, 1, 1),
                    font_size='34sp',
                    size_hint=(1, None),
                    height=60,
                    pos_hint={'top': 1},
                    halign='center',
                    valign='middle',
                    text_size=(preview.width, None),
                ))
                preview.add_widget(Label(
                    text=card.title,
                    color=(0.9, 0.95, 1, 1),
                    font_size='14sp',
                    size_hint=(1, None),
                    height=24,
                    pos_hint={'x': 0, 'y': 0},
                    halign='center',
                    valign='middle',
                    text_size=(preview.width, None),
                ))
                self.new_stack_area.add_widget(preview)
        else:
            self.new_stack_area.add_widget(Label(
                text='No new cards to put away yet.',
                color=(0.8, 0.9, 1, 1),
                font_size='16sp',
                size_hint=(1, None),
                height=120,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                halign='center',
                valign='middle',
                text_size=(Window.width - 40, None),
            ))

        self.card_list.clear_widgets()
        if not self.cards:
            self.card_list.add_widget(Label(
                text='No cards yet. Scan a creature to add cards to your collection.',
                color=(1, 1, 1, 1),
                font_size='16sp',
                halign='center',
                valign='middle',
                size_hint=(1, None),
                height=120,
                text_size=(Window.width - 40, None),
            ))
            return

        for card in reversed(self.cards):
            card_box = styled_layout(BoxLayout(orientation='vertical', padding=12, spacing=8, size_hint=(1, None), height=330))
            card_box.add_widget(Label(
                text=card.background.preview,
                color=(1, 1, 1, 1),
                font_size='38sp',
                size_hint=(1, None),
                height=70,
                halign='center',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            card_box.add_widget(Label(
                text=card.title,
                color=(1, 1, 1, 1),
                font_size='18sp',
                bold=True,
                size_hint=(1, None),
                height=28,
                halign='center',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            rel_line = []
            if card.organism.lifecycle_stage:
                rel_line.append(card.organism.lifecycle_stage)
            if card.organism.group:
                rel_line.append(card.organism.group)
            if rel_line:
                card_box.add_widget(Label(
                    text=' • '.join(rel_line),
                    color=(0.7, 0.85, 1, 1),
                    font_size='13sp',
                    size_hint=(1, None),
                    height=24,
                    halign='center',
                    valign='middle',
                    text_size=(Window.width / 2 - 40, None),
                ))
            card_box.add_widget(Label(
                text=f'{card.organism.type} • {card.organism.rarity} • {card.background.name}',
                color=(0.8, 0.9, 1, 1),
                font_size='14sp',
                size_hint=(1, None),
                height=24,
                halign='center',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            card_box.add_widget(Label(
                text=f'Moves: {", ".join(card.selected_moves)}',
                color=(1, 1, 1, 1),
                font_size='13sp',
                halign='left',
                valign='top',
                size_hint=(1, None),
                height=42,
                text_size=(Window.width / 2 - 40, None),
            ))
            card_box.add_widget(Label(
                text=card.organism.description,
                color=(1, 1, 1, 1),
                font_size='13sp',
                halign='left',
                valign='top',
                size_hint=(1, None),
                height=58,
                text_size=(Window.width / 2 - 40, None),
            ))
            if card.organism.related_forms:
                card_box.add_widget(Label(
                    text=f'Related: {", ".join(card.organism.related_forms)}',
                    color=(0.7, 0.85, 1, 1),
                    font_size='12sp',
                    italic=True,
                    size_hint=(1, None),
                    height=24,
                    halign='left',
                    valign='middle',
                    text_size=(Window.width / 2 - 40, None),
                ))
            card_box.add_widget(Label(
                text=f'Habitat: {card.selected_details["Habitat"]}',
                color=(0.7, 0.85, 1, 1),
                font_size='12sp',
                italic=True,
                size_hint=(1, None),
                height=24,
                halign='left',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            card_box.add_widget(Label(
                text=f'Size: {card.selected_details["Size"]}',
                color=(0.7, 0.85, 1, 1),
                font_size='12sp',
                italic=True,
                size_hint=(1, None),
                height=24,
                halign='left',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            if card.organism.notes:
                card_box.add_widget(Label(
                    text=f'Notes: {card.organism.notes}',
                    color=(0.7, 0.85, 1, 1),
                    font_size='11sp',
                    italic=True,
                    size_hint=(1, None),
                    height=26,
                    halign='left',
                    valign='middle',
                    text_size=(Window.width / 2 - 40, None),
                ))
            for child in card_box.children:
                if isinstance(child, Label):
                    child.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
            self.card_list.add_widget(card_box)

    def on_enter(self, *args):
        self.refresh_cards()

    def put_away_cards(self, _=None):
        app = App.get_running_app()
        app.new_cards.clear()
        self.refresh_cards()
        app.home_screen.update_new_card_badge()

    def auto_organize(self, _=None):
        self.cards.sort(key=lambda card: (card.organism.rarity, card.organism.name))
        self.refresh_cards()

    def sort_by_type(self, _=None):
        self.cards.sort(key=lambda card: (card.organism.type, card.organism.name))
        self.refresh_cards()

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class VitaDexApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.cards = []
        self.new_cards = []
        self.home_screen = HomeScreen()
        self.scan_screen = ScanScreen()
        self.card_book_screen = CardBookScreen()

        manager = ScreenManager()
        manager.add_widget(self.home_screen)
        manager.add_widget(self.scan_screen)
        manager.add_widget(self.card_book_screen)
        return manager


if __name__ == '__main__':
    VitaDexApp().run()
