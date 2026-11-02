"""Exercise real Kivy screens with isolated data. Requires a graphical display.

Run from the repository root: python scripts/check_ui.py
Optional screenshots: python scripts/check_ui.py --screenshots /tmp/vitadex-preview
"""
import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kivy.clock import Clock
from kivy.core.window import Window

from database import CARD_DB
from journal import JournalError, JournalSession
from main import VitaDexApp

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--screenshots', type=Path)
args = parser.parse_args()
if args.screenshots:
    args.screenshots.mkdir(parents=True, exist_ok=True)

class SilentSpeaker:
    def __init__(self):
        self.messages = []
        self.callbacks = []

    def speak(self, text, **kwargs):
        self.messages.append(text)
        self.callbacks.append(kwargs)

    def stop(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def close(self):
        pass


app = VitaDexApp()
app.speaker = SilentSpeaker()
workspace = tempfile.TemporaryDirectory(prefix='vitadex-ui-')
app._user_data_dir = workspace.name
Window.size = (1000, 820)
errors = []
count = len(CARD_DB.organisms)


def capture(name, widget=None):
    if args.screenshots:
        (widget or app.root).export_to_png(str(args.screenshots / f'{name}.png'))


def guard(callback):
    def run(_):
        try:
            callback()
        except Exception as error:
            errors.append(error)
            app.stop()
    return run


def desktop():
    capture('journal-empty')
    for organism in CARD_DB.organisms.values():
        app.scan_screen.collect(organism)
        app.fullscreen_popup.dismiss(animation=False)
    assert len(app.cards) == count
    assert len(app.speaker.messages) == count
    assert len(JournalSession(app.journal_repository).new_cards) == count
    app.navigate('cardbook')
    Clock.schedule_once(guard(collection), .3)


def collection():
    capture('card-book')
    book = app.card_book_screen
    assert len(book.visible_cards) == count
    book.search.text = 'robin'
    book.refresh_cards()
    assert [card.title for card in book.visible_cards] == ['American Robin']
    book.search.text = ''
    book.type_filter.text = 'Tree'
    assert [card.title for card in book.visible_cards] == ['Red Maple']
    book.type_filter.text = 'All types'
    book.sort_control.text = 'Name A–Z'
    assert [card.title for card in book.visible_cards] == sorted(card.title for card in app.cards)
    # Sorting the displayed list must not change durable order or the unseen boundary.
    assert app.cards[-1].title == 'American Robin'
    book.search.text = 'no such creature'
    book.refresh_cards()
    assert not book.visible_cards and len(book.tiles_area.children) == 1
    book.reset_or_explore()
    book.put_away_cards()
    assert not JournalSession(app.journal_repository).new_cards
    # Failed saves must never show a new-card popup or modify the collection.
    original = app.journal_repository.append_card
    def fail(_, **kwargs):
        raise JournalError('Simulated full disk')
    app.journal_repository.append_card = fail
    original_message = app.show_storage_error
    messages = []
    app.show_storage_error = messages.append
    from dataclasses import replace
    unknown = replace(next(iter(CARD_DB.organisms.values())), name='Unsaved test organism', scientific_name='Test unsaved organism', organism_id='taxon:test-unsaved')
    app.scan_screen.collect(unknown)
    assert len(app.cards) == count and messages and app.fullscreen_popup is None
    app.show_storage_error = original_message
    app.journal_repository.append_card = original
    from identification import IdentificationCandidate, IdentificationResult
    known = app.cards[0].organism
    result = IdentificationResult((IdentificationCandidate(known, 1.0),), source='test-sensor')
    assert not app.handle_encounter(result).is_first
    assert app.fullscreen_popup is None and len(app.speaker.messages) == count
    app.read_card(app.cards[0])
    assert len(app.speaker.messages) == count + 1
    app.open_card(app.cards[0])
    Clock.schedule_once(guard(details), .3)


def details():
    capture('card-detail', app.fullscreen_popup)
    app.fullscreen_popup.dismiss(animation=False)
    Window.size = (360, 640)
    app.navigate('cardbook')
    Clock.schedule_once(guard(narrow), .3)


def narrow():
    assert app.card_book_screen.tiles_area.cols == 1
    capture('card-book-narrow')
    app.navigate('scan')
    Clock.schedule_once(guard(explore), .3)


def explore():
    capture('explore-narrow')
    # Hidden lists and recent-card widgets must not rebuild for voice/status events.
    app.navigate('cardbook')
    before = tuple(app.card_book_screen.tiles_area.children)
    recent = tuple(app.home_screen.recent.children)
    app.voice_status = 'A status-only update'
    app.refresh()
    assert tuple(app.card_book_screen.tiles_area.children) == before
    assert tuple(app.home_screen.recent.children) == recent
    app.navigate('home')
    for _ in range(30):
        clone = app.journal_repository._card_from_dict(app.journal_repository._card_to_dict(app.cards[0]))
        app.journal_session.add_card(clone)
    app.refresh()
    assert tuple(app.card_book_screen.tiles_area.children) == before
    app.navigate('cardbook')
    assert len(app.card_book_screen.tiles_area.children) == app.card_book_screen.page_size
    app.card_book_screen.change_page(1)
    assert app.card_book_screen.page == 1
    assert len(app.card_book_screen.tiles_area.children) <= app.card_book_screen.page_size
    # A late failure belongs only to the utterance/card that requested it.
    app.open_card(app.cards[0])
    app.read_card(app.cards[0])
    old = app.speaker.callbacks[-1]
    old_label = app.card_voice_status
    app.fullscreen_popup.dismiss(animation=False)
    app.open_card(app.cards[1])
    app.read_card(app.cards[1])
    new_label = app.card_voice_status
    from narration import SpeechEvent
    old['on_event'](SpeechEvent(old['utterance_id'], old['card_id'], 'failed', 'Old error'))
    Clock.schedule_once(guard(lambda: finish_checks(old_label, new_label)), .1)


def finish_checks(old_label, new_label):
    assert new_label is not old_label and 'Old error' not in new_label.text
    app.fullscreen_popup.dismiss(animation=False)
    from dataclasses import replace
    original = app.cards[0]
    current = replace(original.organism, description=original.organism.description + ' Updated test edition.')
    count_before, speech_before = len(app.cards), len(app.speaker.messages)
    preview = app.preview_update(original, current)
    confirm = next(widget for widget in preview.content.children if getattr(widget, 'text', '') == 'Update saved facts')
    confirm.dispatch('on_release')
    assert len(app.cards) == count_before and len(app.speaker.messages) == speech_before
    assert app.cards[0].organism.description == current.description
    app.fullscreen_popup.dismiss(animation=False)
    app.on_pause()
    from identification import IdentificationResult
    assert app.handle_encounter(IdentificationResult((), source='background')) is None
    app.on_resume()
    assert app.foreground
    print('UI checks passed: discovery, filters, persistence, errors, paging, hidden-view reuse, stale speech events, lifecycle, resize.')
    app.stop()


Clock.schedule_once(guard(desktop), .5)
app.run()
workspace.cleanup()
if errors:
    raise errors[0]
