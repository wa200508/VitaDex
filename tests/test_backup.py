import io
import json
import sqlite3

import pytest

import backup
from backup import JournalBackup
from database import CARD_DB
from documents import copy_document
from editorial import digest
from identity import organism_key
from journal import JournalError, JournalRepository, JournalSession


def repository(tmp_path, name="journal"):
    result = JournalRepository(tmp_path / (name + ".sqlite3"))
    result.load_cards()
    return result


def cards():
    return [CARD_DB.build_card(organism) for organism in CARD_DB.organisms.values()]


def contents(repo, path):
    JournalBackup(repo).export(path)
    return json.loads(path.read_text())["payload"]


def test_round_trip_preserves_sources_history_settings_and_first_discovery(tmp_path):
    source = repository(tmp_path, "source")
    dog, cat = cards()[:2]
    source.save_cards([dog, cat, dog])  # Historical duplicate cards remain representable.
    source.save_seen_count(1)
    source.save_setting("voice_enabled", 0)
    source.save_setting("never_export_this", 999)
    source.update_card(dog, dog)
    path = tmp_path / "portable.json"
    payload = contents(source, path)
    assert "never_export_this" not in path.read_text()
    assert payload["history"][0]["card"]["organism"]["sources"] == dog.organism.sources

    target = repository(tmp_path, "target")
    service = JournalBackup(target)
    preview = service.preview(path, "replace")
    assert (preview.added, preview.total) == (3, 3)
    assert not target.load_cards()  # Preview is read-only for saved data.
    safety = service.restore(preview, tmp_path / "safety")
    assert json.loads(safety.read_text())["payload"]["cards"] == []
    assert contents(target, tmp_path / "round-trip.json") == payload
    session = JournalSession(target)
    assert session.cards == [dog, cat, dog]
    assert session.seen_count == 1 and not target.load_voice_enabled()
    saved, first = session.discover_card(dog)
    assert not first and saved == dog and len(session.cards) == 3


def test_merge_keeps_existing_snapshot_settings_and_deduplicates(tmp_path):
    from copy import deepcopy

    target, source = repository(tmp_path, "target"), repository(tmp_path, "source")
    dog, cat = cards()[:2]
    target.save_cards([dog])
    target.save_seen_count(1)
    target.save_setting("voice_enabled", 0)
    alternate = deepcopy(dog)
    alternate.selected_moves = ["Backup edition"]
    source.save_cards([alternate, cat, cat])
    source.update_card(cat, cat)
    path = tmp_path / "portable.json"
    contents(source, path)
    service = JournalBackup(target)
    preview = service.preview(path)
    assert (preview.added, preview.skipped, preview.total) == (1, 2, 2)
    service.restore(preview, tmp_path / "safety")
    session = JournalSession(target)
    assert session.cards == [dog, cat] and session.seen_count == 1
    assert not target.load_voice_enabled()
    again = service.preview(path)
    assert again.added == 0 and again.skipped == 3
    service.restore(again, tmp_path / "safety")
    payload = contents(target, tmp_path / "again.json")
    assert len(payload["history"]) == 1


@pytest.mark.parametrize(
    "change", ["version", "checksum", "identity", "settings", "position", "card", "history"]
)
def test_invalid_backup_never_changes_saved_data(tmp_path, change):
    repo = repository(tmp_path)
    repo.save_cards(cards()[:1])
    path = tmp_path / "portable.json"
    original = contents(repo, path)
    data = json.loads(path.read_text())
    if change == "version":
        data["version"] = 99
    elif change == "checksum":
        data["sha256"] = "wrong"
    else:
        payload = data["payload"]
        if change == "identity":
            payload["discoveries"] = {"invented": 0}
        elif change == "settings":
            payload["settings"]["voice_enabled"] = True
        elif change == "position":
            payload["cards"][0]["position"] = -1
        elif change == "card":
            payload["cards"][0]["card"]["selected_details"]["Habitat"] = (
                "Invented unsupported claim"
            )
        elif change == "history":
            payload["history"] = [
                {
                    "organism_key": "invented",
                    "card": payload["cards"][0]["card"],
                    "archived_on": "today",
                }
            ]
        data["sha256"] = digest(payload)
    path.write_text(json.dumps(data))
    with pytest.raises(JournalError):
        JournalBackup(repo).preview(path)
    assert contents(repo, tmp_path / "after.json") == original


@pytest.mark.parametrize("changed", ["file", "journal"])
def test_stale_confirmation_is_rejected(tmp_path, changed):
    repo = repository(tmp_path)
    repo.save_cards(cards()[:1])
    path = tmp_path / "portable.json"
    contents(repo, path)
    service = JournalBackup(repo)
    preview = service.preview(path, "replace")
    if changed == "file":
        path.write_text(path.read_text() + "\n")
    else:
        repo.append_card(cards()[1])
    expected = repo.load_cards()
    with pytest.raises(JournalError, match="changed"):
        service.restore(preview, tmp_path / "safety")
    assert repo.load_cards() == expected


def test_safety_copy_failure_aborts_before_writes(tmp_path, monkeypatch):
    repo = repository(tmp_path)
    repo.save_cards(cards()[:1])
    path = tmp_path / "portable.json"
    contents(repo, path)
    service = JournalBackup(repo)
    preview = service.preview(path, "replace")

    def fail(*_):
        raise OSError("Disk full")

    monkeypatch.setattr(backup, "atomic_json", fail)
    with pytest.raises(JournalError, match="Disk full"):
        service.restore(preview, tmp_path / "safety")
    assert repo.load_cards() == cards()[:1]


def test_mid_restore_failure_rolls_back_and_keeps_safety_copy(tmp_path, monkeypatch):
    source, target = repository(tmp_path, "source"), repository(tmp_path, "target")
    source.save_cards(cards()[:1])
    target.save_cards(cards()[1:2])
    path = tmp_path / "portable.json"
    contents(source, path)
    original = contents(target, tmp_path / "original.json")
    service = JournalBackup(target)
    preview = service.preview(path, "replace")

    def interrupted(connection, payload):
        connection.execute("DELETE FROM cards")
        raise sqlite3.OperationalError("interrupted")

    monkeypatch.setattr(service, "_replace", interrupted)
    with pytest.raises(JournalError, match="interrupted"):
        service.restore(preview, tmp_path / "safety")
    assert contents(target, tmp_path / "after.json") == original
    (safety,) = (tmp_path / "safety").glob("*.json")
    assert json.loads(safety.read_text())["payload"] == original


def test_import_bounds_and_failed_copy_preserve_destination(tmp_path, monkeypatch):
    import documents

    destination = tmp_path / "file.json"
    destination.write_bytes(b"keep me")
    monkeypatch.setattr(documents, "MAX_BYTES", 4)
    with pytest.raises(ValueError, match="limit"):
        copy_document(io.BytesIO(b"too large"), destination)
    assert destination.read_bytes() == b"keep me"
    assert list(tmp_path.iterdir()) == [destination]
    copy_document(io.BytesIO(b"ok"), destination)
    assert destination.read_bytes() == b"ok"
    repo = repository(tmp_path)
    monkeypatch.setattr(backup, "MAX_BYTES", 4)
    with pytest.raises(JournalError):
        JournalBackup(repo).preview(destination)


def test_discovery_index_cannot_reference_a_different_species(tmp_path):
    repo = repository(tmp_path)
    repo.save_cards(cards()[:2])
    with sqlite3.connect(repo.path) as connection:
        connection.execute(
            "UPDATE discoveries SET card_position=1 WHERE organism_key=?",
            (organism_key(cards()[0].organism),),
        )
    with pytest.raises(JournalError, match="identities"):
        JournalBackup(repo).export(tmp_path / "bad.json")
