"""Card, citation, update, and message dialogs with explicit ownership."""

from dataclasses import asdict
import webbrowser
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from database import CARD_DB
from identity import organism_key
from editorial import changed_fields
from journal import JournalError
from .art import CreatureArt
from .widgets import (
    Action,
    label,
    column,
    MUTED,
    GREEN,
    PAPER,
    BORDER,
    provenance_status,
    claim_sources,
)


class CardDialogs:
    def __init__(self, app):
        self.app = app
        self.card_popup = self.overlay = None
        self.card_key = None
        self.voice_label = None

    def _clear(self, name, popup):
        if getattr(self, name) is popup:
            setattr(self, name, None)

    def dismiss_current(self):
        popup = self.overlay or self.card_popup
        if popup:
            popup.dismiss()

    def open_card(self, card, saved=False):
        self.card_key = organism_key(card.organism)
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(8))
        scroll = ScrollView(do_scroll_x=False)
        detail = column(spacing=14, padding=12)
        detail.add_widget(label(card.title, size=28, bold=True))
        if saved:
            detail.add_widget(label("FIRST DISCOVERY", size=12, color=GREEN, bold=True))
        self.voice_label = label("Listen or read the introduction.", size=13, color=MUTED)
        detail.add_widget(self.voice_label)
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        row.add_widget(Action(text="Read aloud", on_release=lambda *_: self.app.read_card(card)))
        row.add_widget(Action(text="Stop reading", on_release=lambda *_: self.app.speaker.stop()))
        detail.add_widget(row)
        detail.add_widget(label(card.organism.description, size=17))
        detail.add_widget(
            CreatureArt(card.organism, card.background.style, size_hint_y=None, height=dp(155))
        )
        detail.add_widget(label(provenance_status(card.organism), size=12, color=GREEN))
        detail.add_widget(
            Action(
                text="Ask VitaDex about this organism",
                primary=True,
                on_release=lambda *_: self.app.open_question(card),
            )
        )
        for heading, text, field in [
            (
                "HABITAT",
                card.selected_details["Habitat"],
                "habitat_type" if card.organism.habitat_type else "habitat",
            ),
            ("SIZE", card.selected_details["Size"], "physical_dimensions"),
            ("IN OUR WORLD", card.organism.environment_role, "environment_role"),
            ("COLLECTION RARITY / GAME MECHANIC", card.organism.rarity, None),
            ("MOVES / GAME MECHANIC", "  •  ".join(card.selected_moves) or "None yet", None),
            ("FIELD NOTES", card.organism.notes or "No notes yet.", "notes"),
            ("CARD EDITION / GAME MECHANIC", card.background.name, None),
        ]:
            if heading.startswith("MOVES") and not card.selected_moves:
                continue
            if heading == "SIZE" and not card.organism.physical_dimensions:
                continue
            detail.add_widget(label(heading, size=11, color=GREEN, bold=True))
            detail.add_widget(
                label(
                    text + (claim_sources(card.organism, field) if field else ""),
                    size=15,
                    color=MUTED,
                )
            )
        current = next(
            (
                entry
                for entry in CARD_DB.organisms.values()
                if organism_key(entry) == organism_key(card.organism)
            ),
            None,
        )
        if current is not None and asdict(current) != asdict(card.organism):
            detail.add_widget(
                Action(
                    text="Review available fact update",
                    on_release=lambda *_: self.preview_update(card, current),
                )
            )
        detail.add_widget(
            Action(text="Sources & review details", on_release=lambda *_: self.open_sources(card))
        )
        scroll.add_widget(detail)
        content.add_widget(scroll)
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        close = Action(text="Keep exploring" if saved else "Close", primary=True)
        controls.add_widget(close)
        if saved:
            view = Action(text="View card book")
            controls.add_widget(view)
        content.add_widget(controls)
        popup = Popup(
            title="New discovery · Card saved" if saved else "Creature card",
            content=content,
            size_hint=(0.94, 0.92),
            background="",
            background_color=PAPER,
            title_color=GREEN,
            separator_color=BORDER,
        )
        close.bind(on_release=popup.dismiss)
        if saved:
            view.bind(on_release=lambda *_: (popup.dismiss(), self.app.navigate("cardbook")))
        popup.bind(on_dismiss=lambda *_: self._clear("card_popup", popup))
        self.card_popup = popup
        popup.open()

    def open_sources(self, card):
        scroll = ScrollView(do_scroll_x=False)
        body = column(padding=16)
        body.add_widget(label("SOURCES & INFORMATION", size=13, color=GREEN, bold=True))
        if card.organism.content_kind == "fictional":
            body.add_widget(
                label(
                    "Original VitaDex fiction. Descriptions, sizes, and roles are invented for the demo; "
                    "they are not verified wildlife facts. Rarity and moves are game mechanics.",
                    size=14,
                    color=MUTED,
                )
            )
        elif card.organism.content_kind == "unreviewed":
            body.add_widget(
                label(
                    "This saved card predates source review or has not been reviewed. "
                    "Its factual claims are not verified.",
                    size=14,
                    color=MUTED,
                )
            )
        else:
            body.add_widget(label(card.organism.scientific_name, size=17, bold=True))
            body.add_widget(
                label(
                    f"Content review: {card.organism.reviewed_by} · {card.organism.reviewed_on}",
                    size=13,
                    color=MUTED,
                )
            )
        if card.organism.content_kind == "source_checked":
            body.add_widget(
                label(
                    "Facts compared against the references by an AI assistant. "
                    "Independent human review is still pending.",
                    size=13,
                    color=MUTED,
                )
            )
        for source in card.organism.sources:
            body.add_widget(label(f"[{source['id']}] {source['title']}", size=16, bold=True))
            body.add_widget(
                label(
                    f"{source['publisher']} · Accessed {source['accessed_on']}\n"
                    f"Supports: {', '.join(source['supports'])}\n"
                    f"License: {source['license']}\n{source['attribution']}",
                    size=13,
                    color=MUTED,
                )
            )
            if source.get("evidence"):
                evidence = source["evidence"]
                body.add_widget(
                    label(
                        f"Source excerpt: {evidence['excerpt']}\nWhere: {evidence['location']}",
                        size=13,
                        color=MUTED,
                    )
                )
            body.add_widget(
                label(source.get("revision_url") or source["url"], size=12, color=MUTED)
            )
            body.add_widget(
                Action(
                    text="Open reference in browser",
                    on_release=lambda *_, url=source.get("revision_url") or source["url"]: (
                        webbrowser.open(url)
                    ),
                )
            )
        body.add_widget(
            label(
                "Sources document factual content; they do not verify an encounter identification.",
                size=12,
                color=MUTED,
            )
        )
        body.add_widget(
            label("Stylized illustration; not an identification photograph.", size=12, color=MUTED)
        )
        scroll.add_widget(body)
        content = BoxLayout(orientation="vertical", spacing=dp(12))
        content.add_widget(scroll)
        close = Action(text="Back to card", primary=True)
        content.add_widget(close)
        popup = Popup(
            title="Sources & information",
            content=content,
            size_hint=(0.94, 0.92),
            background="",
            background_color=PAPER,
            title_color=GREEN,
        )
        close.bind(on_release=popup.dismiss)
        self.overlay = popup
        popup.bind(on_dismiss=lambda *_: self._clear("overlay", popup))
        popup.open()
        return popup

    def preview_update(self, card, organism):
        changes = changed_fields(asdict(card.organism), asdict(organism))
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        body = column()
        body.add_widget(label("Changed: " + ", ".join(changes), size=15))
        body.add_widget(label("Current catalog introduction:\n" + organism.description, size=16))
        body.add_widget(
            label(
                "The original saved facts and references will be archived. "
                "This updates the fact sheet without another first-discovery announcement.\n"
                + provenance_status(organism),
                size=14,
                color=MUTED,
            )
        )
        for source in organism.sources:
            body.add_widget(label(source["title"] + "\n" + source["url"], size=13, color=MUTED))
        scroll.add_widget(body)
        content.add_widget(scroll)
        cancel = Action(text="Keep saved version")
        confirm = Action(text="Update saved facts", primary=True)
        content.add_widget(cancel)
        content.add_widget(confirm)
        popup = Popup(
            title="Review fact update",
            content=content,
            size_hint=(0.94, 0.9),
            background="",
            background_color=PAPER,
            title_color=GREEN,
        )
        cancel.bind(on_release=popup.dismiss)

        def apply(*_):
            try:
                replacement = CARD_DB.build_card(organism)
                replacement.background, replacement.art_asset = card.background, card.art_asset
                self.app.journal_session.update_card(card, replacement)
            except (JournalError, ValueError) as error:
                popup.dismiss()
                self.app.show_storage_error(str(error))
                return
            popup.dismiss()
            if self.card_popup:
                self.card_popup.dismiss(animation=False)
            self.app.refresh()
            self.open_card(replacement)

        confirm.bind(on_release=apply)
        popup.open()
        return popup

    def message(self, title, text):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        body = column()
        body.add_widget(label(text, size=15))
        scroll.add_widget(body)
        content.add_widget(scroll)
        close = Action(text="Close", primary=True)
        content.add_widget(close)
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.94, 0.7),
            background="",
            background_color=PAPER,
            title_color=GREEN,
            separator_color=BORDER,
        )
        close.bind(on_release=popup.dismiss)
        popup.open()
