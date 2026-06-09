import os
import random
import time

# Disable Kivy Inspector to prevent red dots on right-click
os.environ['KIVY_INSPECTOR'] = '0'

from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
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


class FloatingPanel(BoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('padding', (8, 8))
        kwargs.setdefault('spacing', 8)
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self._drag_offset = (0, 0)
        self._is_dragging = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._drag_offset = (self.x - touch.x, self.y - touch.y)
            touch.grab(self)
            self._is_dragging = False
            return super().on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            # If movement is >10px, treat as drag, otherwise allow button clicks
            dx = touch.x - touch.ox
            dy = touch.y - touch.oy
            distance = (dx**2 + dy**2) ** 0.5
            if distance > 10:
                self._is_dragging = True
                self.pos = (touch.x + self._drag_offset[0], touch.y + self._drag_offset[1])
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if not self._is_dragging:
                # If not dragging, let child widgets (buttons) handle the touch
                return super().on_touch_down(touch)
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)


class CardStackPreview(ButtonBehavior, BoxLayout):
    def __init__(self, card, on_select, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('width', 160)
        kwargs.setdefault('height', 220)
        super().__init__(**kwargs)
        self.card = card
        self.on_select = on_select
        with self.canvas.before:
            Color(0.06, 0.1, 0.18, 1)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
            Color(0.2, 0.45, 0.85, 0.35)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=1.4)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.add_widget(Label(
            text=card.title,
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True,
            size_hint=(1, None),
            height=30,
            halign='center',
            valign='middle',
            text_size=(160 - 24, None),
        ))
        self.add_widget(Label(
            text=f'{card.organism.type} • {card.organism.rarity}',
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            size_hint=(1, None),
            height=24,
            halign='center',
            valign='middle',
            text_size=(160 - 24, None),
        ))

    def update_graphics(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 20)

    def on_release(self):
        self.on_select(self.card)


class CardDetailView(ButtonBehavior, BoxLayout):
    def __init__(self, on_tap=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', 16)
        kwargs.setdefault('spacing', 10)
        super().__init__(**kwargs)
        self.on_tap = on_tap
        self.card = None
        self.last_touch_time = 0
        self.double_tap_threshold = 0.3
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
        self.details_label.text = f'{card.organism.description}\n\nMoves: {", ".join(card.selected_moves)}'
        self.stats_label.text = (
            f'Habitat: {card.selected_details["Habitat"]}\n'
            f'Size: {card.selected_details["Size"]}\n'
            f'Role: {card.organism.environment_role}\n'
            f'Notes: {card.organism.notes or "None"}'
        )

    def _close_fullscreen(self):
        app = App.get_running_app()
        if hasattr(app, 'fullscreen_popup') and app.fullscreen_popup:
            app.fullscreen_popup.dismiss()
            app.fullscreen_popup = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_pos = touch.pos
            return super().on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            # Check for swipe (>60px movement)
            if hasattr(self, 'touch_start_pos'):
                dx = touch.x - self.touch_start_pos[0]
                dy = touch.y - self.touch_start_pos[1]
                distance = (dx**2 + dy**2) ** 0.5
                if distance > 60:
                    self._close_fullscreen()
                    return True
        return super().on_touch_up(touch)

    def on_release(self):
        if self.card:
            current_time = time.time()
            if current_time - self.last_touch_time < self.double_tap_threshold:
                # Double tap - close fullscreen
                self._close_fullscreen()
            else:
                # Single tap - open fullscreen
                if self.on_tap:
                    self.on_tap(self.card)
            self.last_touch_time = current_time


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

        button_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=170, spacing=12)
        button_layout.add_widget(OutlineButton(
            text='Start Scan',
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
            text='Scan Now',
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
        preview = FloatLayout(size_hint=(0.9, None), height=220, pos_hint={'center_x': 0.5, 'center_y': 0.55}, opacity=0)
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
        card_box.add_widget(Label(
            text='Tap anywhere to add this card to your collection',
            color=(0.8, 0.9, 1, 1),
            font_size='14sp',
            size_hint=(1, None),
            height=28,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8 - 40, None),
        ))

        preview.add_widget(card_box)
        dismiss_area = Button(
            background_normal='',
            background_color=(0, 0, 0, 0),
            size_hint=(1, 1),
            on_release=lambda *_: self.dismiss_scan_preview(preview),
        )
        preview.add_widget(dismiss_area)
        self.add_widget(preview)

        Animation(opacity=1, d=0.35).start(preview)

    def dismiss_scan_preview(self, preview):
        def on_shrink_complete(*args):
            self.remove_widget(preview)
            app = App.get_running_app()
            app.home_screen.update_new_card_badge()
            app.home_screen.collection_button.flash()
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'home'

        shrink_anim = Animation(pos=(Window.width * 0.15, 32), size=(70, 40), opacity=0, d=0.35)
        shrink_anim.bind(on_complete=on_shrink_complete)
        shrink_anim.start(preview)

    def goto_home(self, _=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class CardBookScreen(Screen):
    cards = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(name='cardbook', **kwargs)
        self.current_view = 'stacks'  # 'stacks' or 'tiles'
        self.selected_card_index = 0

        root = FloatLayout()

        # Central card display panel
        self.main_panel = BoxLayout(orientation='vertical', size_hint=(0.74, 0.72), pos_hint={'center_x': 0.5, 'center_y': 0.5}, padding=20, spacing=12)
        styled_layout(self.main_panel)

        self.main_panel.add_widget(Label(
            text='Card Book',
            color=(1, 1, 1, 1),
            font_size='28sp',
            size_hint=(1, None),
            height=54,
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.7, None),
        ))

        self.new_stack_area = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, None), height=180)
        self.main_panel.add_widget(self.new_stack_area)

        self.collection_area = FloatLayout(size_hint=(1, 1))
        root.add_widget(self.main_panel)
        self.main_panel.add_widget(self.collection_area)

        self.stack_area = FloatLayout(size_hint=(None, None), size=(240, 340), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.collection_area.add_widget(self.stack_area)

        self.tiles_area = GridLayout(cols=2, spacing=16, size_hint=(1, None), padding=12)
        self.tiles_area.bind(minimum_height=self.tiles_area.setter('height'))
        self.tiles_scroll = ScrollView(size_hint=(1, 1))
        self.tiles_scroll.add_widget(self.tiles_area)

        # Outer edge controls
        top_controls = BoxLayout(size_hint=(0.92, None), height=64, spacing=12, pos_hint={'center_x': 0.5, 'top': 0.98})
        top_controls.add_widget(OutlineButton(
            text='Stacks',
            size_hint=(0.35, 1),
            on_release=self._switch_to_stacks,
        ))
        top_controls.add_widget(OutlineButton(
            text='Tiles',
            size_hint=(0.35, 1),
            on_release=self._switch_to_tiles,
        ))
        root.add_widget(top_controls)

        self.sort_panel = FloatingPanel(size_hint=(None, 0.14), width=160, pos_hint={'x': 0.02, 'center_y': 0.5})
        self.sort_panel.add_widget(OutlineButton(
            text='Sort by Type',
            size_hint=(1, 1),
            on_release=self.sort_by_type,
        ))
        root.add_widget(self.sort_panel)

        self.put_away_panel = FloatingPanel(size_hint=(None, 0.14), width=160, pos_hint={'right': 0.98, 'center_y': 0.5})
        self.put_away_panel.add_widget(OutlineButton(
            text='Put Away New',
            size_hint=(1, 1),
            on_release=self.put_away_cards,
        ))
        root.add_widget(self.put_away_panel)

        self.back_button = OutlineButton(
            text='Back to Home',
            font_size='20sp',
            size_hint=(0.9, None),
            height=72,
            pos_hint={'center_x': 0.5, 'y': 0.02},
            on_release=self.goto_home,
        )
        root.add_widget(self.back_button)

        self.add_widget(root)

    def _switch_to_stacks(self, _=None):
        self.current_view = 'stacks'
        self.collection_area.clear_widgets()
        self.collection_area.add_widget(self.stack_area)
        self.refresh_cards()

    def _switch_to_tiles(self, _=None):
        self.current_view = 'tiles'
        self.collection_area.clear_widgets()
        self.collection_area.add_widget(self.tiles_scroll)
        self.refresh_cards()

    def add_card(self, card):
        self.cards.append(card)
        self.selected_card_index = len(self.cards) - 1
        self.refresh_cards()

    def select_card(self, card):
        if card in self.cards:
            self.selected_card_index = self.cards.index(card)

    def open_fullscreen_card(self, card):
        content = BoxLayout(orientation='vertical', padding=20, spacing=14)
        detail = CardDetailView(size_hint=(1, 1))
        detail.set_card(card)
        content.add_widget(detail)
        popup = Popup(title=card.title, content=content, size_hint=(0.96, 0.96), auto_dismiss=True)
        popup.open()
        app = App.get_running_app()
        app.fullscreen_popup = popup

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
                halign='left',
                valign='middle',
                text_size=(Window.width - 40, None),
            ))
            preview_row = BoxLayout(spacing=10, size_hint=(1, None), height=120)
            for card in app.new_cards[-3:]:
                preview = BoxLayout(orientation='vertical', size_hint=(None, None), size=(Window.width * 0.3, 120), padding=10, spacing=8)
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
                    font_size='28sp',
                    size_hint=(1, None),
                    height=56,
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
                    halign='center',
                    valign='middle',
                    text_size=(preview.width, None),
                ))
                preview_row.add_widget(preview)
            self.new_stack_area.add_widget(preview_row)
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

        self.stack_area.clear_widgets()
        self.tiles_area.clear_widgets()
        
        if not self.cards:
            no_card = Label(
                text='No cards yet. Scan a creature to add cards to your collection.',
                color=(1, 1, 1, 1),
                font_size='16sp',
                halign='center',
                valign='middle',
                size_hint=(1, None),
                height=200,
                text_size=(Window.width - 40, None),
            )
            if self.current_view == 'stacks':
                self.stack_area.add_widget(no_card)
            else:
                self.tiles_area.add_widget(no_card)
            return

        # Populate stacks view
        for index, card in enumerate(reversed(self.cards)):
            preview = CardStackPreview(card, on_select=self.select_card)
            preview.pos = (index * 16, index * 12)
            self.stack_area.add_widget(preview)

        # Populate tiles view
        for card in self.cards:
            tile = BoxLayout(orientation='vertical', size_hint=(1, None), height=220, padding=10, spacing=8)
            with tile.canvas.before:
                Color(0.06, 0.1, 0.18, 1)
                RoundedRectangle(pos=tile.pos, size=tile.size, radius=[20])
                Color(0.2, 0.45, 0.85, 0.35)
                Line(rounded_rectangle=(tile.x, tile.y, tile.width, tile.height, 20), width=1.4)
            
            def update_tile(_, __):
                tile.canvas.before.clear()
                with tile.canvas.before:
                    Color(0.06, 0.1, 0.18, 1)
                    RoundedRectangle(pos=tile.pos, size=tile.size, radius=[20])
                    Color(0.2, 0.45, 0.85, 0.35)
                    Line(rounded_rectangle=(tile.x, tile.y, tile.width, tile.height, 20), width=1.4)
            
            tile.bind(pos=update_tile, size=update_tile)
            tile.add_widget(Label(
                text=card.title,
                color=(1, 1, 1, 1),
                font_size='14sp',
                bold=True,
                size_hint=(1, None),
                height=40,
                halign='center',
                valign='middle',
                text_size=(tile.width - 20, None),
            ))
            tile.add_widget(Label(
                text=card.card_art,
                color=(1, 1, 1, 1),
                font_size='32sp',
                size_hint=(1, None),
                height=80,
                halign='center',
                valign='middle',
                text_size=(tile.width, None),
            ))
            tile.add_widget(Label(
                text=f'{card.organism.type} • {card.organism.rarity}',
                color=(0.8, 0.9, 1, 1),
                font_size='12sp',
                size_hint=(1, None),
                height=30,
                halign='center',
                valign='middle',
                text_size=(tile.width - 20, None),
            ))
            self.tiles_area.add_widget(tile)

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
        # Disable Kivy Inspector (prevents red dots on right-click)
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_keyboard)
        
        Window.clearcolor = (0, 0, 0, 1)
        self.cards = []
        self.new_cards = []
        self.fullscreen_popup = None
        self.home_screen = HomeScreen()
        self.scan_screen = ScanScreen()
        self.card_book_screen = CardBookScreen()

        manager = ScreenManager()
        manager.add_widget(self.home_screen)
        manager.add_widget(self.scan_screen)
        manager.add_widget(self.card_book_screen)
        return manager
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        # Block F1 which opens the inspector and Ctrl+E
        if key == 282:  # F1
            return True
        if key == 101 and 'ctrl' in modifier:  # Ctrl+E
            return True
        return False


if __name__ == '__main__':
    VitaDexApp().run()
