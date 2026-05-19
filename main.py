import random

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

from database import DATABASE


def build_wrapped_label(text, font_size='18sp', height=140):
    label = Label(
        text=text,
        font_size=font_size,
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


class Card:
    def __init__(self, entry):
        self.entry = entry
        self.card_art = random.choice(entry.image_assets) if entry.image_assets else entry.art


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='home', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=18)

        layout.add_widget(Label(
            text='VitaDex',
            font_size='36sp',
            bold=True,
            size_hint=(1, None),
            height=60,
        ))

        layout.add_widget(build_wrapped_label(
            'VitaDex is a pocket field guide for cataloging and exploring the living systems around you. ' 
            'Scan organisms in the wild, review cards in your collection, and build a personal nature catalog for offline use.',
            font_size='17sp',
            height=180,
        ))

        button_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=280, spacing=16)
        button_layout.add_widget(Button(
            text='🔍 Start Scan',
            font_size='24sp',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_scan,
        ))
        button_layout.add_widget(Button(
            text='📒 Card Book',
            font_size='24sp',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_card_book,
        ))

        layout.add_widget(button_layout)

        feature_box = BoxLayout(orientation='vertical', spacing=8)
        feature_box.add_widget(Label(text='• Scan and identify organisms in the field', halign='left', valign='middle', size_hint_y=None, height=28, text_size=(Window.width - 40, None)))
        feature_box.add_widget(Label(text='• Collect cards for every encounter', halign='left', valign='middle', size_hint_y=None, height=28, text_size=(Window.width - 40, None)))
        feature_box.add_widget(Label(text='• Maintain a local, offline-friendly catalog', halign='left', valign='middle', size_hint_y=None, height=28, text_size=(Window.width - 40, None)))
        feature_box.add_widget(Label(text='• Designed for safe, child-friendly exploration', halign='left', valign='middle', size_hint_y=None, height=28, text_size=(Window.width - 40, None)))

        for child in feature_box.children:
            child.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))

        layout.add_widget(feature_box)
        self.add_widget(layout)

    def goto_scan(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'scan'

    def goto_card_book(self, _=None):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'cardbook'


class ScanScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='scan', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=18)

        layout.add_widget(Label(
            text='Scan Overview',
            font_size='28sp',
            size_hint=(1, None),
            height=50,
        ))

        layout.add_widget(build_wrapped_label(
            'Scan creatures in the wild and let VitaDex create the card automatically for your collection. ' 
            'Successful matches are stored in your card book so you can review and compare your discoveries.',
            font_size='17sp',
            height=180,
        ))

        layout.add_widget(Button(
            text='🔍 Scan Now',
            font_size='24sp',
            size_hint=(1, None),
            height=120,
            on_release=self.perform_scan,
        ))
        layout.add_widget(Button(
            text='🏠 Back to Home',
            font_size='22sp',
            size_hint=(1, None),
            height=120,
            on_release=self.goto_home,
        ))
        self.add_widget(layout)

    def perform_scan(self, _=None):
        app = App.get_running_app()
        entry = random.choice(DATABASE)
        card = Card(entry)
        app.card_book_screen.add_card(card)
        self.manager.current = 'cardbook'

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class CardBookScreen(Screen):
    cards = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(name='cardbook', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=18)

        layout.add_widget(Label(
            text='Card Book',
            font_size='28sp',
            size_hint=(1, None),
            height=50,
        ))

        control_row = BoxLayout(size_hint=(1, None), height=80, spacing=12)
        control_row.add_widget(Button(
            text='✨ Auto organize',
            font_size='18sp',
            on_release=self.auto_organize,
        ))
        control_row.add_widget(Button(
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
        layout.add_widget(Button(
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
        self.card_list.clear_widgets()
        if not self.cards:
            self.card_list.add_widget(Label(
                text='No cards yet. Scan a creature to add cards to your collection.',
                font_size='16sp',
                halign='center',
                valign='middle',
                size_hint=(1, None),
                height=120,
                text_size=(Window.width - 40, None),
            ))
            return

        for card in reversed(self.cards):
            card_box = BoxLayout(orientation='vertical', padding=14, spacing=10, size_hint=(0.48, None), height=300)
            card_box.canvas.before.clear()
            card_box.add_widget(Label(
                text=card.card_art,
                font_size='40sp',
                size_hint=(1, None),
                height=70,
                halign='center',
                valign='middle',
                text_size=(Window.width / 2 - 40, None),
            ))
            card_box.add_widget(Label(text=card.entry.name, font_size='18sp', bold=True, size_hint=(1, None), height=28, halign='center', valign='middle', text_size=(Window.width / 2 - 40, None)))
            rel_line = []
            if card.entry.lifecycle_stage:
                rel_line.append(card.entry.lifecycle_stage)
            if card.entry.group:
                rel_line.append(card.entry.group)
            if rel_line:
                card_box.add_widget(Label(text=' • '.join(rel_line), font_size='13sp', size_hint=(1, None), height=24, halign='center', valign='middle', text_size=(Window.width / 2 - 40, None)))
            card_box.add_widget(Label(text=f'{card.entry.type} • {card.entry.rarity}', font_size='14sp', size_hint=(1, None), height=24, halign='center', valign='middle', text_size=(Window.width / 2 - 40, None)))
            card_box.add_widget(Label(text=f'Moves: {", ".join(card.entry.move_set)}', font_size='13sp', halign='left', valign='top', size_hint=(1, None), height=42, text_size=(Window.width / 2 - 40, None)))
            card_box.add_widget(Label(text=card.entry.description, font_size='13sp', halign='left', valign='top', size_hint=(1, None), height=58, text_size=(Window.width / 2 - 40, None)))
            if card.entry.related_forms:
                card_box.add_widget(Label(text=f'Related: {", ".join(card.entry.related_forms)}', font_size='12sp', italic=True, size_hint=(1, None), height=24, halign='left', valign='middle', text_size=(Window.width / 2 - 40, None)))
            card_box.add_widget(Label(text=f'Habitat: {card.entry.habitat}', font_size='12sp', italic=True, size_hint=(1, None), height=24, halign='left', valign='middle', text_size=(Window.width / 2 - 40, None)))
            for child in card_box.children:
                if isinstance(child, Label):
                    child.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
            self.card_list.add_widget(card_box)

    def on_enter(self, *args):
        self.refresh_cards()

    def auto_organize(self, _=None):
        self.cards.sort(key=lambda card: (card.entry.rarity, card.entry.name))
        self.refresh_cards()

    def sort_by_type(self, _=None):
        self.cards.sort(key=lambda card: (card.entry.type, card.entry.name))
        self.refresh_cards()

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class VitaDexApp(App):
    def build(self):
        Window.clearcolor = (0.96, 0.97, 1, 1)
        self.card_book_screen = CardBookScreen()
        manager = ScreenManager()
        manager.add_widget(HomeScreen())
        manager.add_widget(ScanScreen())
        manager.add_widget(self.card_book_screen)
        return manager


if __name__ == '__main__':
    VitaDexApp().run()
