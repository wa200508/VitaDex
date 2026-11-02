"""VitaDex's local card journal interface."""
import math
import os
import webbrowser
from pathlib import Path

os.environ['KIVY_INSPECTOR'] = '0'

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Triangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from database import CARD_DB
from identification import DemoIdentificationService, IdentificationCandidate, IdentificationResult
from discovery import DiscoveryService, introduction
from narration import LocalSpeaker
from identity import organism_key
from uuid import uuid4
from journal import JournalError, JournalRepository, JournalSession

PAPER = (0.96, 0.95, 0.91, 1)
WHITE = (1, 0.995, 0.97, 1)
INK = (0.12, 0.23, 0.19, 1)
MUTED = (0.38, 0.45, 0.39, 1)
GREEN = (0.16, 0.36, 0.27, 1)
PALE = (0.87, 0.91, 0.84, 1)
BORDER = (0.82, 0.85, 0.78, 1)
GOLD = (0.76, 0.51, 0.19, 1)


def provenance_status(organism):
    return {'fictional': 'FICTIONAL / no factual sources',
            'unreviewed': 'UNREVIEWED / facts not verified',
            'source_checked': 'SOURCE CHECKED / human review pending',
            'reviewed': f'REVIEWED / {len(organism.sources)} references'}[organism.content_kind]


def claim_sources(organism, field):
    ids = [source['id'] for source in organism.sources if field in source['supports']]
    return ('  [' + ', '.join(ids) + ']') if ids else ''


def label(text='', size=16, color=INK, bold=False, **kwargs):
    """A wrapping label whose height follows its content."""
    widget = Label(text=text, font_size=dp(size), color=color, bold=bold,
                   halign='left', valign='middle', size_hint_y=None, **kwargs)
    widget.bind(width=lambda item, width: setattr(item, 'text_size', (max(1, width), None)))
    widget.bind(texture_size=lambda item, size: setattr(item, 'height', size[1] + dp(6)))
    return widget


def column(spacing=12, padding=0, **kwargs):
    box = BoxLayout(orientation='vertical', spacing=dp(spacing), padding=dp(padding),
                    size_hint_y=None, **kwargs)
    box.bind(minimum_height=box.setter('height'))
    return box


def surface(widget, color=WHITE, radius=20):
    with widget.canvas.before:
        Color(*color)
        background = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    def resize(*_):
        background.pos, background.size = widget.pos, widget.size
    widget.bind(pos=resize, size=resize)
    return widget


class Action(Button):
    def __init__(self, primary=False, **kwargs):
        super().__init__(background_normal='', background_down='',
                         background_color=(0, 0, 0, 0), color=WHITE if primary else GREEN,
                         font_size=dp(14), bold=True, disabled_color=MUTED,
                         size_hint_y=None, height=dp(46), **kwargs)
        self.primary = primary
        with self.canvas.before:
            self.fill = Color(*(GREEN if primary else PALE))
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw, disabled=self.redraw)

    def redraw(self, *_):
        self.shape.pos, self.shape.size = self.pos, self.size
        base = GREEN if self.primary else PALE
        self.fill.rgba = (*base[:3], 0.4 if self.disabled else (0.7 if self.state == 'down' else 1))
        self.text_size = (max(1, self.width - dp(12)), None)
        self.halign = 'center'


class CreatureArt(Widget):
    """Small original vector illustrations; no network or image dependencies."""
    def __init__(self, organism, style='emerald', **kwargs):
        super().__init__(**kwargs)
        self.organism, self.style = organism, style
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        cx, cy, unit = x + w * .5, y + h * .50, min(w, h) * .32
        colors = {'emerald': (.82, .88, .74, 1), 'blue': (.76, .88, .89, 1),
                  'gold': (.96, .88, .66, 1)}
        with self.canvas:
            Color(*colors.get(self.style, colors['emerald']))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
            Color(1, 1, .95, .38)
            Ellipse(pos=(cx - unit * 1.2, cy - unit * 1.1), size=(unit * 2.4, unit * 2.4))
            Color(.3, .48, .33, .18)
            for i in range(7):
                px = x + w * ((i * .173 + .11) % .9)
                py = y + h * ((i * .29 + .16) % .85)
                Ellipse(pos=(px, py), size=(dp(4), dp(4)))
            if self.organism.type == 'Mammal':
                is_cat = self.organism.scientific_name == 'Felis catus'
                Color(*((.74, .47, .23, 1) if not is_cat else (.55, .57, .55, 1)))
                Ellipse(pos=(cx-unit*.65, cy-unit*.65), size=(unit*1.3, unit*1.4))
                if is_cat:
                    Triangle(points=[cx-unit*.6, cy+unit*.2, cx-unit*.6, cy+unit,
                                     cx-unit*.1, cy+unit*.55])
                    Triangle(points=[cx+unit*.6, cy+unit*.2, cx+unit*.6, cy+unit,
                                     cx+unit*.1, cy+unit*.55])
                    Color(.91, .69, .62, 1)
                    Triangle(points=[cx-unit*.48, cy+unit*.4, cx-unit*.49, cy+unit*.77,
                                     cx-unit*.23, cy+unit*.52])
                    Triangle(points=[cx+unit*.48, cy+unit*.4, cx+unit*.49, cy+unit*.77,
                                     cx+unit*.23, cy+unit*.52])
                else:
                    Color(.43, .28, .17, 1)
                    Ellipse(pos=(cx-unit*.9, cy-unit*.1), size=(unit*.48, unit*1.0))
                    Ellipse(pos=(cx+unit*.42, cy-unit*.1), size=(unit*.48, unit*1.0))
                Color(.94, .86, .68, 1)
                Ellipse(pos=(cx-unit*.37, cy-unit*.5), size=(unit*.74, unit*.54))
                Color(*INK)
                for direction in (-1, 1):
                    Ellipse(pos=(cx+direction*unit*.27-unit*.065, cy+unit*.13),
                            size=(unit*.13, unit*.15))
                    if is_cat:
                        for offset in (-.1, .06, .2):
                            Line(points=[cx+direction*unit*.2, cy-unit*.24,
                                         cx+direction*unit*.85, cy+unit*(offset-.2)], width=1)
                Triangle(points=[cx-unit*.12, cy-unit*.12, cx+unit*.12, cy-unit*.12,
                                 cx, cy-unit*.27])
                Line(points=[cx, cy-unit*.27, cx, cy-unit*.39], width=1.4)
            elif self.organism.type == 'Tree':
                Color(.42, .29, .18, 1)
                RoundedRectangle(pos=(cx-unit*.1, cy-unit*1.05),
                                 size=(unit*.2, unit*1.3), radius=[unit*.03])
                for direction in (-1, 1):
                    Line(points=[cx, cy-unit*.2, cx+direction*unit*.55, cy+unit*.45], width=dp(3))
                # Original stylized lobed leaves, not diagnostic botanical drawings.
                leaf = [(0, 1), (.22, .45), (.65, .65), (.5, .12), (.9, .1),
                        (.48, -.3), (.1, -.55), (-.1, -.55), (-.48, -.3),
                        (-.9, .1), (-.5, .12), (-.65, .65), (-.22, .45)]
                for dx, dy, scale, tone in [(-.55, .3, .65, (.68, .35, .2, 1)),
                                           (.5, .35, .66, (.77, .43, .23, 1)),
                                           (0, .8, .7, (.87, .53, .25, 1))]:
                    Color(*tone)
                    px, py, size = cx+unit*dx, cy+unit*dy, unit*scale
                    for i, point in enumerate(leaf):
                        nxt = leaf[(i+1) % len(leaf)]
                        Triangle(points=[px, py, px+point[0]*size, py+point[1]*size,
                                         px+nxt[0]*size, py+nxt[1]*size])
                    Color(.98, .77, .48, 1)
                    Line(points=[px, py-size*.4, px, py+size*.65], width=1)
            elif self.organism.type == 'Grass':
                for i in range(11):
                    dx = (i-5)*.15
                    top = .2+((i*7) % 9)*.09
                    Color(.22+i*.012, .42+i*.012, .24, 1)
                    Triangle(points=[cx+unit*dx, cy-unit*.9,
                                     cx+unit*(dx+.12), cy-unit*.9,
                                     cx+unit*(dx*1.35), cy+unit*top])
                for direction in (-1, 1):
                    stem_x = cx+direction*unit*.35
                    Color(.36, .54, .29, 1)
                    Line(points=[stem_x, cy-unit*.8, stem_x, cy+unit*1.05], width=1.5)
                    for i in range(4):
                        height = cy+unit*(.35+i*.18)
                        reach = unit*(.35-i*.07)
                        for side in (-1, 1):
                            Line(points=[stem_x, height, stem_x+side*reach, height+unit*.15], width=1)
                            Ellipse(pos=(stem_x+side*reach, height+unit*.13), size=(unit*.09, unit*.12))
            elif self.organism.type == 'Bird':
                Color(.28, .32, .32, 1)
                Triangle(points=[cx-unit*.6, cy-unit*.25, cx-unit*1.15, cy-unit*.55,
                                 cx-unit*.95, cy+unit*.1])
                Ellipse(pos=(cx-unit*.65, cy-unit*.6), size=(unit*1.35, unit*1.25))
                Color(.72, .35, .2, 1)
                Ellipse(pos=(cx-unit*.05, cy-unit*.49), size=(unit*.8, unit*.95))
                Color(.23, .27, .27, 1)
                Ellipse(pos=(cx+unit*.14, cy+unit*.23), size=(unit*.73, unit*.73))
                Color(.36, .4, .39, 1)
                Ellipse(pos=(cx-unit*.52, cy-unit*.17), size=(unit*.72, unit*.51))
                Color(.89, .66, .19, 1)
                Triangle(points=[cx+unit*.78, cy+unit*.65, cx+unit*1.15, cy+unit*.48,
                                 cx+unit*.78, cy+unit*.42])
                Color(*INK)
                Ellipse(pos=(cx+unit*.61, cy+unit*.66), size=(unit*.1, unit*.1))
                for dx in (-.18, .28):
                    Line(points=[cx+unit*dx, cy-unit*.5, cx+unit*dx, cy-unit*.95,
                                 cx+unit*(dx+.25), cy-unit*.95], width=1.5)
            elif self.organism.type == 'Fish':
                Color(.15, .42, .46, 1)
                Triangle(points=[cx-unit*.55, cy, cx-unit*1.3, cy+unit*.65,
                                 cx-unit*1.3, cy-unit*.65])
                Color(.28, .62, .63, 1)
                Ellipse(pos=(cx-unit*.8, cy-unit*.48), size=(unit*1.8, unit*.96))
                Color(.9, .76, .36, 1)
                Triangle(points=[cx-unit*.2, cy-unit*.15, cx+unit*.3, cy-unit*.1,
                                 cx, cy-unit*.65])
                Color(*INK)
                Ellipse(pos=(cx+unit*.52, cy+unit*.05), size=(unit*.13, unit*.13))
                Color(1, 1, 1, .7)
                for i in range(3):
                    Line(circle=(cx+unit*(1.15+i*.2), cy+unit*(.4+i*.4), unit*.1), width=1.2)
            elif self.organism.type == 'Plant':
                Color(*GREEN)
                Line(points=[cx, cy-unit, cx, cy+unit*.35], width=dp(3))
                Ellipse(pos=(cx, cy-unit*.65), size=(unit*.7, unit*.3))
                Ellipse(pos=(cx-unit*.7, cy-unit*.3), size=(unit*.7, unit*.3))
                Color(.91, .64, .21, 1)
                for i in range(8):
                    angle = i * math.pi / 4
                    Ellipse(pos=(cx+math.cos(angle)*unit*.45-unit*.25,
                                 cy+unit*.4+math.sin(angle)*unit*.45-unit*.25),
                            size=(unit*.5, unit*.5))
                Color(.37, .29, .16, 1)
                Ellipse(pos=(cx-unit*.3, cy+unit*.1), size=(unit*.6, unit*.6))
            else:
                Color(*GREEN)
                for direction in (-1, 1):
                    for offset in (-.4, 0, .4):
                        Line(points=[cx+direction*unit*.3, cy+offset*unit,
                                     cx+direction*unit*.85, cy+(offset-.2)*unit], width=dp(2))
                    Line(points=[cx+direction*unit*.18, cy+unit*.6,
                                 cx+direction*unit*.4, cy+unit], width=dp(2))
                Ellipse(pos=(cx-unit*.28, cy+unit*.35), size=(unit*.56, unit*.55))
                Color(.3, .53, .29, 1)
                Ellipse(pos=(cx-unit*.52, cy-unit*.65), size=(unit*1.04, unit*1.25))
                Color(.72, .82, .35, 1)
                Line(points=[cx, cy-unit*.6, cx, cy+unit*.5], width=dp(2))
                for dx, dy in [(-.25, .2), (.25, -.1), (-.22, -.35)]:
                    Ellipse(pos=(cx+unit*dx-unit*.08, cy+unit*dy-unit*.08), size=(unit*.16, unit*.16))


class CardTile(ButtonBehavior, BoxLayout):
    def __init__(self, card, on_open, is_new=False, **kwargs):
        super().__init__(orientation='vertical', padding=dp(12), spacing=dp(8), **kwargs)
        self.card, self.on_open = card, on_open
        surface(self)
        self.add_widget(CreatureArt(card.organism, card.background.style))
        self.add_widget(label(('NEW  /  ' if is_new else '') + card.organism.type.upper(),
                              size=10, color=GREEN, bold=True))
        self.add_widget(label(card.title, size=18, bold=True))
        self.add_widget(label(f'{card.organism.rarity}  •  {card.background.name}', size=12, color=MUTED))
        self.add_widget(label(provenance_status(card.organism), size=10, color=GREEN))

    def on_release(self):
        self.on_open(self.card)


class Page(Screen):
    def __init__(self, name, title, subtitle, **kwargs):
        super().__init__(name=name, **kwargs)
        self.body = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        self.add_widget(self.body)
        self.body.add_widget(label(title, size=30, bold=True))
        self.body.add_widget(label(subtitle, size=14, color=MUTED))

    def scroll_content(self):
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        content = column(spacing=16)
        scroll.add_widget(content)
        self.body.add_widget(scroll)
        return content


class HomeScreen(Page):
    def __init__(self):
        super().__init__('home', 'A little closer to nature.', 'Your discoveries, all in one place.')
        content = self.scroll_content()
        hero = surface(column(padding=20, spacing=10), GREEN)
        hero.add_widget(label('YOUR NATURE COMPANION', size=11, color=(.78, .86, .65, 1), bold=True))
        hero.add_widget(label('Meet it. Hear its story.\nKeep the discovery.', size=28, color=WHITE, bold=True))
        hero.add_widget(label('VitaDex introduces each new creature aloud, then saves a card to revisit.',
                              size=15, color=(.85, .91, .82, 1)))
        hero.add_widget(Action(text='Try a discovery  >', on_release=lambda *_: App.get_running_app().navigate('scan')))
        content.add_widget(hero)
        voice = surface(column(padding=16), PALE)
        voice.add_widget(label('THE VITADEX VOICE', size=11, color=GREEN, bold=True))
        self.voice_status = label(size=14, color=MUTED)
        voice.add_widget(self.voice_status)
        self.voice_toggle = Action(on_release=lambda *_: App.get_running_app().toggle_voice())
        voice.add_widget(self.voice_toggle)
        content.add_widget(voice)
        stats = surface(column(padding=16))
        self.stats_label = label(size=19, bold=True)
        self.progress_label = label(size=14, color=MUTED)
        stats.add_widget(self.stats_label)
        stats.add_widget(self.progress_label)
        content.add_widget(stats)
        heading = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(12))
        heading.add_widget(label('Recently collected', size=20, bold=True))
        heading.add_widget(Action(text='View card book', size_hint_x=None, width=dp(142),
                                 on_release=lambda *_: App.get_running_app().navigate('cardbook')))
        content.add_widget(heading)
        self.recent = column()
        content.add_widget(self.recent)
        content.add_widget(label('Find sources and content status in every card. Your collection stays on this device.',
                                 size=12, color=MUTED))

    def refresh(self):
        app = App.get_running_app()
        self.voice_toggle.text = 'Auto voice: ON' if app.voice_enabled else 'Auto voice: OFF'
        self.voice_status.text = app.voice_status
        unique = len(app.journal_session.by_key)
        self.stats_label.text = f'{len(app.cards)} cards  /  {unique} creatures collected'
        catalog_count = len({organism_key(x) for x in CARD_DB.organisms.values()}
                            & app.journal_session.by_key.keys())
        self.progress_label.text = f'{catalog_count} of {len(CARD_DB.organisms)} catalog creatures  •  {app.new_count} new cards'
        last = app.cards[-1] if app.cards else None
        recent_state = (id(last), app.is_new(last) if last else False)
        if getattr(self, '_recent_state', None) == recent_state:
            return
        self._recent_state = recent_state
        self.recent.clear_widgets()
        if app.cards:
            card = app.cards[-1]
            self.recent.add_widget(CardTile(card, app.open_card, app.is_new(card),
                                           size_hint_y=None, height=dp(290)))
        else:
            empty = surface(column(padding=20), PALE)
            empty.add_widget(label('Your first chapter starts here.', size=19, bold=True))
            empty.add_widget(label('Choose a creature in Explore to start your card book.', color=MUTED))
            empty.add_widget(Action(text='Find your first creature', primary=True,
                                   on_release=lambda *_: app.navigate('scan')))
            self.recent.add_widget(empty)

    def update_new_card_badge(self):
        self.refresh()


class ScanScreen(Page):
    def __init__(self):
        super().__init__('scan', 'Meet the small wonders.', 'Ohio starter collection. Try an encounter and hear its story.')
        content = self.scroll_content()
        content.add_widget(label('SIMULATED ENCOUNTERS / REAL ORGANISMS', size=11, color=GREEN, bold=True))
        for organism in CARD_DB.organisms.values():
            panel = surface(column(padding=16))
            style = CARD_DB.select_background_for(organism).style
            panel.add_widget(CreatureArt(organism, style, size_hint_y=None, height=dp(155)))
            panel.add_widget(label(f'{organism.type.upper()}  /  {organism.rarity.upper()}', size=11, color=GREEN, bold=True))
            panel.add_widget(label(organism.name, size=23, bold=True))
            panel.add_widget(label(provenance_status(organism), size=11, color=GREEN))
            panel.add_widget(label(organism.description, size=15, color=MUTED))
            panel.add_widget(Action(text='Discover this creature', primary=True,
                                    on_release=lambda *_, item=organism: self.collect(item)))
            content.add_widget(panel)
        content.add_widget(Action(text='Surprise me', on_release=self.perform_scan))

    def collect(self, organism):
        result = IdentificationResult(
            candidates=(IdentificationCandidate(organism, 1.0),), source='manual-demo'
        )
        App.get_running_app().handle_encounter(result, show_known=True)

    def perform_scan(self, *_):
        app = App.get_running_app()
        app.handle_encounter(app.identification_service.identify(), show_known=True)


class CardBookScreen(Page):
    def __init__(self):
        super().__init__('cardbook', 'Your card book.', 'A collection of the things that caught your curiosity.')
        self.search = TextInput(hint_text='Search name, habitat, or type...', multiline=False,
                                size_hint_y=None, height=dp(46), font_size=dp(15),
                                padding=(dp(12), dp(12)), background_normal='',
                                background_active='', background_color=WHITE,
                                foreground_color=INK, cursor_color=GREEN)
        self.body.add_widget(self.search)
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.type_filter = Spinner(text='All types', values=tuple(['All types'] + sorted(
                                   {organism.type for organism in CARD_DB.organisms.values()}
                                   | {card.organism.type for card in App.get_running_app().cards})),
                                   background_normal='', background_color=GREEN, color=WHITE,
                                   font_size=dp(13))
        self.sort_control = Spinner(text='Newest first', values=('Newest first', 'Name A–Z', 'Type'),
                                    background_normal='', background_color=GREEN, color=WHITE,
                                    font_size=dp(13))
        controls.add_widget(self.type_filter)
        controls.add_widget(self.sort_control)
        self.body.add_widget(controls)
        status_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.collection_status = label(size=13, color=MUTED)
        status_row.add_widget(self.collection_status)
        self.mark_seen_button = Action(text='Mark all seen', size_hint_x=None, width=dp(122),
                                       on_release=self.put_away_cards)
        status_row.add_widget(self.mark_seen_button)
        self.body.add_widget(status_row)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.tiles_area = GridLayout(cols=2, spacing=dp(14), size_hint_y=None,
                                     row_default_height=dp(298), row_force_default=True)
        self.tiles_area.bind(minimum_height=self.tiles_area.setter('height'), width=self.resize_grid)
        scroll.add_widget(self.tiles_area)
        self.body.add_widget(scroll)
        self.page = 0
        self.page_size = 12
        self._render_state = None
        self.search_trigger = Clock.create_trigger(self.refresh_cards, .15)
        self.search.bind(text=lambda *_: self.search_trigger())
        self.type_filter.bind(text=self.refresh_cards)
        self.sort_control.bind(text=self.refresh_cards)
        pager = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.previous_page = Action(text='Previous', on_release=lambda *_: self.change_page(-1))
        self.page_status = label(size=12, color=MUTED)
        self.next_page = Action(text='Next', on_release=lambda *_: self.change_page(1))
        for widget in (self.previous_page, self.page_status, self.next_page):
            pager.add_widget(widget)
        self.body.add_widget(pager)

    @property
    def cards(self):
        return App.get_running_app().cards

    def resize_grid(self, _, width):
        self.tiles_area.cols = max(1, int(width / dp(240)))

    def change_page(self, direction):
        self.page += direction
        self.refresh_cards()

    def on_pre_enter(self, *_):
        self.refresh_cards()

    def refresh_cards(self, *_):
        app = App.get_running_app()
        if not self.manager or self.manager.current != 'cardbook':
            return
        state = (app.journal_session.revision, self.search.text, self.type_filter.text,
                 self.sort_control.text, self.page)
        if self._render_state == state:
            return
        if self._render_state and self._render_state[1:4] != state[1:4]:
            self.page = 0
        self.tiles_area.clear_widgets()
        query = self.search.text.strip().casefold()
        cards = [card for card in self.cards if
                 (self.type_filter.text == 'All types' or card.organism.type == self.type_filter.text)
                 and query in ' '.join((card.title, card.organism.type, card.organism.habitat,
                                       card.organism.rarity)).casefold()]
        if self.sort_control.text == 'Name A–Z':
            cards.sort(key=lambda card: card.title.casefold())
        elif self.sort_control.text == 'Type':
            cards.sort(key=lambda card: (card.organism.type, card.title))
        else:
            cards.reverse()
        self.visible_cards = cards
        self.collection_status.text = f'{len(cards)} of {len(self.cards)} cards  •  {app.new_count} new'
        self.mark_seen_button.disabled = not app.new_count
        if not cards:
            empty = surface(column(padding=20), PALE)
            empty.add_widget(label('No matches yet.' if self.cards else 'A fresh page.', size=22, bold=True))
            empty.add_widget(label('Try another search or clear your filters.' if self.cards
                                    else 'Explore the catalog to collect your first card.', color=MUTED))
            empty.add_widget(Action(text='Clear filters' if self.cards else 'Explore creatures',
                                    on_release=self.reset_or_explore))
            self.tiles_area.add_widget(empty)
        pages = max(1, math.ceil(len(cards) / self.page_size))
        self.page = max(0, min(self.page, pages - 1))
        self.page_status.text = f'{self.page + 1} / {pages}'
        self.previous_page.disabled = self.page == 0
        self.next_page.disabled = self.page == pages - 1
        self._render_state = (app.journal_session.revision, self.search.text, self.type_filter.text,
                              self.sort_control.text, self.page)
        for card in cards[self.page * self.page_size:(self.page + 1) * self.page_size]:
            self.tiles_area.add_widget(CardTile(card, app.open_card, app.is_new(card)))

    def reset_or_explore(self, *_):
        if self.cards:
            self.search.text, self.type_filter.text = '', 'All types'
        else:
            App.get_running_app().navigate('scan')

    def put_away_cards(self, *_):
        app = App.get_running_app()
        try:
            app.journal_session.mark_seen()
        except JournalError as error:
            app.show_storage_error(str(error))
            return
        app.refresh()

    def open_fullscreen_card(self, card):
        App.get_running_app().open_card(card)


class VitaDexApp(App):
    title = 'VitaDex · Field journal'

    @property
    def cards(self):
        return self.journal_session.cards

    @property
    def new_cards(self):
        return self.journal_session.new_cards

    @property
    def new_count(self):
        return self.journal_session.new_count

    def is_new(self, card):
        return self.journal_session.is_new(card)

    def build(self):
        self.foreground = True
        Window.clearcolor = PAPER
        Window.bind(on_keyboard=self._on_keyboard)
        self.journal_repository = JournalRepository(Path(self.user_data_dir) / 'journal.sqlite3',
                                                    Path(self.user_data_dir) / 'journal.json')
        self.journal_session = JournalSession(self.journal_repository)
        self.identification_service = DemoIdentificationService(CARD_DB)
        self.discovery_service = DiscoveryService(CARD_DB, self.journal_session)
        self.voice_status = 'First discoveries are introduced aloud. You can replay any card.'
        try:
            self.voice_enabled = self.journal_repository.load_voice_enabled()
        except JournalError:
            self.voice_enabled = False
            self.voice_status = 'Voice settings could not be loaded; automatic narration is off.'
        if not hasattr(self, 'speaker'):
            from kivy.utils import platform
            self.speaker = LocalSpeaker(platform=platform if platform in ('android', 'ios') else None)
        self.fullscreen_popup = None
        root = surface(BoxLayout(orientation='vertical'), PAPER, radius=0)
        header = surface(BoxLayout(padding=(dp(20), dp(10)), spacing=dp(12),
                                    size_hint_y=None, height=dp(66)), WHITE, radius=0)
        header.add_widget(label('VitaDex', size=25, color=GREEN, bold=True))
        header.add_widget(label('FIELD NOTES & SMALL WONDERS', size=10, color=MUTED))
        root.add_widget(header)
        self.manager = ScreenManager(transition=NoTransition())
        self.home_screen, self.scan_screen, self.card_book_screen = HomeScreen(), ScanScreen(), CardBookScreen()
        for screen in (self.home_screen, self.scan_screen, self.card_book_screen):
            self.manager.add_widget(screen)
        root.add_widget(self.manager)
        nav = surface(BoxLayout(padding=dp(10), spacing=dp(8), size_hint_y=None, height=dp(66)), WHITE, radius=0)
        self.nav_buttons = {}
        for name, title in [('home', 'Journal'), ('scan', 'Discover'), ('cardbook', 'Card book')]:
            button = Action(text=title, on_release=lambda *_, target=name: self.navigate(target))
            nav.add_widget(button)
            self.nav_buttons[name] = button
        root.add_widget(nav)
        self.navigate('home')
        if self.journal_session.load_error:
            Clock.schedule_once(lambda _: self.show_storage_error(str(self.journal_session.load_error)), 0)
        return root

    def navigate(self, name):
        self.manager.current = name
        for key, button in self.nav_buttons.items():
            button.primary = key == name
            button.color = WHITE if key == name else GREEN
            button.redraw()
        self.refresh()

    def refresh(self):
        self.home_screen.refresh()
        self.card_book_screen.refresh_cards()

    def handle_encounter(self, result, show_known=False):
        if not self.foreground:
            return
        from threading import current_thread, main_thread
        if current_thread() is not main_thread():
            Clock.schedule_once(lambda _: self.handle_encounter(result, show_known), 0)
            return
        try:
            discovery = self.discovery_service.encounter(result)
        except JournalError as error:
            self.show_storage_error(str(error))
            return
        except ValueError as error:
            self.message('Sources need review', str(error))
            return
        if discovery is None:
            if show_known:
                self.message('Keep observing', result.safety_message)
            return
        if discovery.is_first:
            self.refresh()
            self.open_card(discovery.card, saved=True)
            if self.voice_enabled:
                self.read_card(discovery.card)
        elif show_known:
            self.open_card(discovery.card)
        return discovery

    def read_card(self, card):
        if not self.foreground:
            return
        key = organism_key(card.organism)
        uid = uuid4().hex
        self.latest_utterance = uid
        target = self.card_voice_status if getattr(self, 'open_card_key', None) == key else None
        def event(event):
            def update(_):
                text = {'requested': 'Introduction queued.', 'started': 'Playing introduction.',
                        'completed': 'Introduction finished.', 'cancelled': 'Introduction stopped.',
                        'failed': 'Voice unavailable: ' + event.message}.get(event.state, event.state)
                if self.latest_utterance == event.utterance_id:
                    self.voice_status = text
                    self.home_screen.refresh()
                if (target is not None and target is getattr(self, 'card_voice_status', None)
                        and self.latest_utterance == event.utterance_id):
                    target.text = text
            Clock.schedule_once(update, 0)
        try:
            self.speaker.speak(introduction(card), card_id=key, utterance_id=uid, on_event=event)
        except Exception as error:
            from narration import SpeechEvent
            event(SpeechEvent(uid, key, 'failed', str(error)))

    def toggle_voice(self):
        if self.journal_session.load_error:
            self.show_storage_error(str(self.journal_session.load_error))
            return
        enabled = not self.voice_enabled
        try:
            self.journal_repository.save_setting('voice_enabled', int(enabled))
        except JournalError as error:
            self.show_storage_error(str(error))
            return
        self.voice_enabled = enabled
        if not enabled:
            self.speaker.stop()
        self.voice_status = ('First discoveries are introduced aloud.' if enabled else
                             'Automatic voice is off. Read aloud is still available in each card.')
        self.refresh()

    def on_stop(self):
        self.foreground = False
        if hasattr(self, 'speaker'):
            self.speaker.close()

    def on_pause(self):
        self.foreground = False
        self.speaker.pause()
        return True

    def on_resume(self):
        self.speaker.resume()
        self.foreground = True

    def open_card(self, card, saved=False):
        self.open_card_key = organism_key(card.organism)
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(8))
        scroll = ScrollView(do_scroll_x=False)
        detail = column(spacing=14, padding=12)
        detail.add_widget(CreatureArt(card.organism, card.background.style,
                                      size_hint_y=None, height=dp(210)))
        detail.add_widget(label(f'{card.organism.type.upper()}  /  {card.organism.rarity.upper()}',
                                size=12, color=GREEN, bold=True))
        detail.add_widget(label(card.title, size=28, bold=True))
        if saved:
            detail.add_widget(label('FIRST DISCOVERY', size=12, color=GREEN, bold=True))
        self.card_voice_status = label(
            'Read the introduction or listen with your system voice.', size=13, color=MUTED)
        detail.add_widget(self.card_voice_status)
        detail.add_widget(Action(text='Read aloud / replay introduction',
                                 on_release=lambda *_: self.read_card(card)))
        detail.add_widget(Action(text='Stop reading', on_release=lambda *_: self.speaker.stop()))
        detail.add_widget(label(provenance_status(card.organism), size=12, color=GREEN, bold=True))
        detail.add_widget(label('Stylized illustration; not an identification photograph.', size=12, color=MUTED))
        detail.add_widget(label(card.organism.description + claim_sources(card.organism, 'description'), size=16))
        for heading, text, field in [
            ('HABITAT', card.selected_details['Habitat'],
             'habitat_type' if card.organism.habitat_type else 'habitat'),
            ('SIZE', card.selected_details['Size'], 'physical_dimensions'),
            ('IN OUR WORLD', card.organism.environment_role, 'environment_role'),
            ('COLLECTION RARITY / GAME MECHANIC', card.organism.rarity, None),
            ('MOVES / GAME MECHANIC', '  •  '.join(card.selected_moves) or 'None yet', None),
            ('FIELD NOTES', card.organism.notes or 'No notes yet.', 'notes'),
            ('CARD EDITION / GAME MECHANIC', card.background.name, None),
        ]:
            if heading.startswith('MOVES') and not card.selected_moves:
                continue
            if heading == 'SIZE' and not card.organism.physical_dimensions:
                continue
            detail.add_widget(label(heading, size=11, color=GREEN, bold=True))
            detail.add_widget(label(text + (claim_sources(card.organism, field) if field else ''),
                                    size=15, color=MUTED))
        detail.add_widget(label('SOURCES & INFORMATION', size=13, color=GREEN, bold=True))
        if card.organism.content_kind == 'fictional':
            detail.add_widget(label(
                'Original VitaDex fiction. Descriptions, sizes, and roles are invented for the demo; '
                'they are not verified wildlife facts. Rarity and moves are game mechanics.',
                size=14, color=MUTED))
        elif card.organism.content_kind == 'unreviewed':
            detail.add_widget(label(
                'This saved card predates source review or has not been reviewed. '
                'Its factual claims are not verified.', size=14, color=MUTED))
        else:
            detail.add_widget(label(card.organism.scientific_name, size=17, bold=True))
            detail.add_widget(label(
                f'Content review: {card.organism.reviewed_by} · {card.organism.reviewed_on}',
                size=13, color=MUTED))
        if card.organism.content_kind == 'source_checked':
            detail.add_widget(label(
                'Facts compared against the references by an AI assistant. '
                'Independent human review is still pending.', size=13, color=MUTED))
        for source in card.organism.sources:
            detail.add_widget(label(f"[{source['id']}] {source['title']}", size=16, bold=True))
            detail.add_widget(label(
                f"{source['publisher']} · Accessed {source['accessed_on']}\n"
                f"Supports: {', '.join(source['supports'])}\n"
                f"License: {source['license']}\n{source['attribution']}", size=13, color=MUTED))
            if source.get('evidence'):
                evidence = source['evidence']
                detail.add_widget(label(
                    f"Source excerpt: {evidence['excerpt']}\nWhere: {evidence['location']}",
                    size=13, color=MUTED))
            detail.add_widget(label(source.get('revision_url') or source['url'], size=12, color=MUTED))
            detail.add_widget(Action(text='Open reference in browser', on_release=
                lambda *_, url=source.get('revision_url') or source['url']: webbrowser.open(url)))
        detail.add_widget(label('Sources document factual content; they do not verify an encounter identification.',
                                size=12, color=MUTED))
        scroll.add_widget(detail)
        content.add_widget(scroll)
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        close = Action(text='Keep exploring' if saved else 'Close', primary=True)
        controls.add_widget(close)
        if saved:
            view = Action(text='View card book')
            controls.add_widget(view)
        content.add_widget(controls)
        popup = Popup(title='New discovery · Card saved' if saved else 'Creature card', content=content,
                      size_hint=(.94, .92), background='', background_color=PAPER,
                      title_color=GREEN, separator_color=BORDER)
        close.bind(on_release=popup.dismiss)
        if saved:
            view.bind(on_release=lambda *_: (popup.dismiss(), self.navigate('cardbook')))
        popup.bind(on_dismiss=lambda *_: setattr(self, 'fullscreen_popup', None))
        self.fullscreen_popup = popup
        popup.open()

    def message(self, title, text):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        body = column()
        body.add_widget(label(text, size=15))
        scroll.add_widget(body)
        content.add_widget(scroll)
        close = Action(text='Close', primary=True)
        content.add_widget(close)
        popup = Popup(title=title, content=content, size_hint=(.94, .7),
                      background='', background_color=PAPER, title_color=GREEN,
                      separator_color=BORDER)
        close.bind(on_release=popup.dismiss)
        popup.open()

    def show_storage_error(self, text):
        self.message('Journal storage problem', 'Your collection was not changed. ' + text)

    def _on_keyboard(self, window, key, *args):
        if key == 27:
            if self.fullscreen_popup:
                self.fullscreen_popup.dismiss()
            else:
                self.navigate('home')
            return True
        return False


if __name__ == '__main__':
    VitaDexApp().run()
