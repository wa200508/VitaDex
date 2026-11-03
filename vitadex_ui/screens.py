"""Journal, discovery, and bounded card-book views."""

import math
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from database import CARD_DB
from identity import organism_key
from identification import IdentificationCandidate, IdentificationResult
from journal import JournalError
from .art import CreatureArt
from .widgets import (
    Action,
    label,
    column,
    surface,
    INK,
    MUTED,
    GREEN,
    WHITE,
    PALE,
    provenance_status,
)


class CardTile(ButtonBehavior, BoxLayout):
    def __init__(self, card, on_open, is_new=False, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(8), **kwargs)
        self.card, self.on_open = card, on_open
        surface(self)
        self.add_widget(CreatureArt(card.organism, card.background.style))
        self.add_widget(
            label(
                ("NEW  /  " if is_new else "") + card.organism.type.upper(),
                size=10,
                color=GREEN,
                bold=True,
            )
        )
        self.add_widget(label(card.title, size=18, bold=True))
        self.add_widget(
            label(f"{card.organism.rarity}  •  {card.background.name}", size=12, color=MUTED)
        )
        self.add_widget(label(provenance_status(card.organism), size=10, color=GREEN))

    def on_release(self):
        self.on_open(self.card)


class Page(Screen):
    def __init__(self, name, title, subtitle, **kwargs):
        super().__init__(name=name, **kwargs)
        self.body = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
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
        super().__init__(
            "home", "A little closer to nature.", "Your discoveries, all in one place."
        )
        content = self.scroll_content()
        hero = surface(column(padding=20, spacing=10), GREEN)
        hero.add_widget(
            label("YOUR NATURE COMPANION", size=11, color=(0.78, 0.86, 0.65, 1), bold=True)
        )
        hero.add_widget(
            label("Meet it. Hear its story.\nKeep the discovery.", size=28, color=WHITE, bold=True)
        )
        hero.add_widget(
            label(
                "VitaDex introduces each new creature aloud, then saves a card to revisit.",
                size=15,
                color=(0.85, 0.91, 0.82, 1),
            )
        )
        hero.add_widget(
            Action(
                text="Try a discovery  >",
                on_release=lambda *_: App.get_running_app().navigate("scan"),
            )
        )
        content.add_widget(hero)
        voice = surface(column(padding=16), PALE)
        voice.add_widget(label("THE VITADEX VOICE", size=11, color=GREEN, bold=True))
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
        heading.add_widget(label("Recently collected", size=20, bold=True))
        heading.add_widget(
            Action(
                text="View card book",
                size_hint_x=None,
                width=dp(142),
                on_release=lambda *_: App.get_running_app().navigate("cardbook"),
            )
        )
        content.add_widget(heading)
        self.recent = column()
        content.add_widget(self.recent)
        content.add_widget(
            label(
                "Find sources and content status in every card. Your collection stays on this device.",
                size=12,
                color=MUTED,
            )
        )
        content.add_widget(
            Action(
                text="Journal backups", on_release=lambda *_: App.get_running_app().backups.open()
            )
        )

    def refresh(self):
        app = App.get_running_app()
        self.voice_toggle.text = "Auto voice: ON" if app.voice_enabled else "Auto voice: OFF"
        self.voice_status.text = app.voice_status
        unique = len(app.journal_session.by_key)
        self.stats_label.text = f"{len(app.cards)} cards  /  {unique} creatures collected"
        catalog_count = len(
            {organism_key(x) for x in CARD_DB.organisms.values()}
            & app.journal_session.by_key.keys()
        )
        self.progress_label.text = f"{catalog_count} of {len(CARD_DB.organisms)} catalog creatures  •  {app.new_count} new cards"
        last = app.cards[-1] if app.cards else None
        recent_state = (id(last), app.is_new(last) if last else False)
        if getattr(self, "_recent_state", None) == recent_state:
            return
        self._recent_state = recent_state
        self.recent.clear_widgets()
        if app.cards:
            card = app.cards[-1]
            self.recent.add_widget(
                CardTile(card, app.open_card, app.is_new(card), size_hint_y=None, height=dp(290))
            )
        else:
            empty = surface(column(padding=20), PALE)
            empty.add_widget(label("Your first chapter starts here.", size=19, bold=True))
            empty.add_widget(
                label("Choose a creature in Explore to start your card book.", color=MUTED)
            )
            empty.add_widget(
                Action(
                    text="Find your first creature",
                    primary=True,
                    on_release=lambda *_: app.navigate("scan"),
                )
            )
            self.recent.add_widget(empty)

    def update_new_card_badge(self):
        self.refresh()


class ScanScreen(Page):
    def __init__(self):
        super().__init__(
            "scan",
            "Meet the small wonders.",
            "Ohio starter collection. Try an encounter and hear its story.",
        )
        content = self.scroll_content()
        content.add_widget(
            label("SIMULATED ENCOUNTERS / REAL ORGANISMS", size=11, color=GREEN, bold=True)
        )
        for organism in CARD_DB.organisms.values():
            panel = surface(column(padding=16))
            style = CARD_DB.select_background_for(organism).style
            panel.add_widget(CreatureArt(organism, style, size_hint_y=None, height=dp(155)))
            panel.add_widget(
                label(
                    f"{organism.type.upper()}  /  {organism.rarity.upper()}",
                    size=11,
                    color=GREEN,
                    bold=True,
                )
            )
            panel.add_widget(label(organism.name, size=23, bold=True))
            panel.add_widget(label(provenance_status(organism), size=11, color=GREEN))
            panel.add_widget(label(organism.description, size=15, color=MUTED))
            panel.add_widget(
                Action(
                    text="Discover this creature",
                    primary=True,
                    on_release=lambda *_, item=organism: self.collect(item),
                )
            )
            content.add_widget(panel)
        content.add_widget(Action(text="Surprise me", on_release=self.perform_scan))

    def collect(self, organism):
        result = IdentificationResult(
            candidates=(IdentificationCandidate(organism, 1.0),), source="manual-demo"
        )
        App.get_running_app().handle_encounter(result, show_known=True)

    def perform_scan(self, *_):
        app = App.get_running_app()
        app.handle_encounter(app.identification_service.identify(), show_known=True)


class CardBookScreen(Page):
    def __init__(self):
        super().__init__(
            "cardbook", "Your card book.", "A collection of the things that caught your curiosity."
        )
        self.search = TextInput(
            hint_text="Search name, habitat, or type...",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
            font_size=dp(15),
            padding=(dp(12), dp(12)),
            background_normal="",
            background_active="",
            background_color=WHITE,
            foreground_color=INK,
            cursor_color=GREEN,
        )
        self.body.add_widget(self.search)
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.type_filter = Spinner(
            text="All types",
            values=tuple(
                ["All types"]
                + sorted(
                    {organism.type for organism in CARD_DB.organisms.values()}
                    | {card.organism.type for card in App.get_running_app().cards}
                )
            ),
            background_normal="",
            background_color=GREEN,
            color=WHITE,
            font_size=dp(13),
        )
        self.sort_control = Spinner(
            text="Newest first",
            values=("Newest first", "Name A–Z", "Type"),
            background_normal="",
            background_color=GREEN,
            color=WHITE,
            font_size=dp(13),
        )
        controls.add_widget(self.type_filter)
        controls.add_widget(self.sort_control)
        self.body.add_widget(controls)
        status_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.collection_status = label(size=13, color=MUTED)
        status_row.add_widget(self.collection_status)
        self.mark_seen_button = Action(
            text="Mark all seen", size_hint_x=None, width=dp(122), on_release=self.put_away_cards
        )
        status_row.add_widget(self.mark_seen_button)
        self.body.add_widget(status_row)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.tiles_area = GridLayout(
            cols=2,
            spacing=dp(14),
            size_hint_y=None,
            row_default_height=dp(298),
            row_force_default=True,
        )
        self.tiles_area.bind(
            minimum_height=self.tiles_area.setter("height"), width=self.resize_grid
        )
        scroll.add_widget(self.tiles_area)
        self.body.add_widget(scroll)
        self.page = 0
        self.page_size = 12
        self._render_state = None
        self.search_trigger = Clock.create_trigger(self.refresh_cards, 0.15)
        self.search.bind(text=lambda *_: self.search_trigger())
        self.type_filter.bind(text=self.refresh_cards)
        self.sort_control.bind(text=self.refresh_cards)
        pager = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.previous_page = Action(text="Previous", on_release=lambda *_: self.change_page(-1))
        self.page_status = label(size=12, color=MUTED)
        self.next_page = Action(text="Next", on_release=lambda *_: self.change_page(1))
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
        if not self.manager or self.manager.current != "cardbook":
            return
        state = (
            app.journal_session.revision,
            self.search.text,
            self.type_filter.text,
            self.sort_control.text,
            self.page,
        )
        if self._render_state == state:
            return
        if self._render_state and self._render_state[1:4] != state[1:4]:
            self.page = 0
        self.tiles_area.clear_widgets()
        query = self.search.text.strip().casefold()
        cards = [
            card
            for card in self.cards
            if (self.type_filter.text == "All types" or card.organism.type == self.type_filter.text)
            and query
            in " ".join(
                (card.title, card.organism.type, card.organism.habitat, card.organism.rarity)
            ).casefold()
        ]
        if self.sort_control.text == "Name A–Z":
            cards.sort(key=lambda card: card.title.casefold())
        elif self.sort_control.text == "Type":
            cards.sort(key=lambda card: (card.organism.type, card.title))
        else:
            cards.reverse()
        self.visible_cards = cards
        self.collection_status.text = (
            f"{len(cards)} of {len(self.cards)} cards  •  {app.new_count} new"
        )
        self.mark_seen_button.disabled = not app.new_count
        if not cards:
            empty = surface(column(padding=20), PALE)
            empty.add_widget(
                label("No matches yet." if self.cards else "A fresh page.", size=22, bold=True)
            )
            empty.add_widget(
                label(
                    "Try another search or clear your filters."
                    if self.cards
                    else "Explore the catalog to collect your first card.",
                    color=MUTED,
                )
            )
            empty.add_widget(
                Action(
                    text="Clear filters" if self.cards else "Explore creatures",
                    on_release=self.reset_or_explore,
                )
            )
            self.tiles_area.add_widget(empty)
        pages = max(1, math.ceil(len(cards) / self.page_size))
        self.page = max(0, min(self.page, pages - 1))
        self.page_status.text = f"{self.page + 1} / {pages}"
        self.previous_page.disabled = self.page == 0
        self.next_page.disabled = self.page == pages - 1
        self._render_state = (
            app.journal_session.revision,
            self.search.text,
            self.type_filter.text,
            self.sort_control.text,
            self.page,
        )
        for card in cards[self.page * self.page_size : (self.page + 1) * self.page_size]:
            self.tiles_area.add_widget(CardTile(card, app.open_card, app.is_new(card)))

    def reset_or_explore(self, *_):
        if self.cards:
            self.search.text, self.type_filter.text = "", "All types"
        else:
            App.get_running_app().navigate("scan")

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
