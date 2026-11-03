"""Portable journal snapshots with previewed, transactional restore.

Checksums detect accidental changes, not authenticity or editorial approval.
Only journal data is exported; provider credentials never enter this format.
"""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from editorial import atomic_json, digest
from identity import organism_key
from journal import JournalError

MAX_BYTES = 32 * 1024 * 1024
MAX_CARDS = 10000
MAX_HISTORY = 20000
FORMAT = "vitadex-journal"


@dataclass(frozen=True)
class RestorePreview:
    path: Path
    file_hash: str
    current_hash: str
    mode: str
    added: int
    skipped: int
    total: int


class JournalBackup:
    def __init__(self, repository):
        self.repository = repository

    def _snapshot(self, connection):
        cards = [
            {"position": row[0], "card": json.loads(row[1])}
            for row in connection.execute("SELECT position, card_json FROM cards ORDER BY position")
        ]
        settings = dict(
            connection.execute(
                "SELECT key, value FROM journal_settings WHERE key IN ('seen_count', 'voice_enabled')"
            )
        )
        settings.setdefault("seen_count", len(cards))
        settings.setdefault("voice_enabled", 1)
        # Older journals can have a stale badge count after explicit collection replacement.
        settings["seen_count"] = min(len(cards), max(0, settings["seen_count"]))
        history = []
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='card_history'"
        ).fetchone():
            history = [
                {"organism_key": row[0], "card": json.loads(row[1]), "archived_on": row[2]}
                for row in connection.execute(
                    "SELECT organism_key, card_json, archived_on FROM card_history ORDER BY id"
                )
            ]
        payload = {
            "cards": cards,
            "settings": settings,
            "history": history,
            "discoveries": dict(
                connection.execute("SELECT organism_key, card_position FROM discoveries")
            ),
        }
        self._validate(payload)
        return payload

    def _validate(self, payload):
        if not isinstance(payload, dict) or set(payload) != {
            "cards",
            "settings",
            "history",
            "discoveries",
        }:
            raise JournalError("Backup contents are incomplete or unsupported.")
        cards, history = payload["cards"], payload["history"]
        if not isinstance(cards, list) or len(cards) > MAX_CARDS:
            raise JournalError("Backup card count is unsupported.")
        if not isinstance(history, list) or len(history) > MAX_HISTORY:
            raise JournalError("Backup history count is unsupported.")
        expected, positions = {}, []

        def card_key(snapshot):
            if not isinstance(snapshot, dict) or set(snapshot) != {
                "organism",
                "background",
                "art_asset",
                "selected_moves",
                "selected_details",
            }:
                raise JournalError("Backup card fields are unsupported.")
            return organism_key(self.repository._card_from_dict(snapshot).organism)

        for row in cards:
            if not isinstance(row, dict) or set(row) != {"position", "card"}:
                raise JournalError("Invalid backup card row.")
            position = row["position"]
            if type(position) is not int or not 0 <= position < 2**63 - 1:
                raise JournalError("Invalid card position.")
            positions.append(position)
            expected.setdefault(card_key(row["card"]), position)
        if positions != sorted(set(positions)):
            raise JournalError("Card positions must be unique and ordered.")
        discoveries = payload["discoveries"]
        if (
            not isinstance(discoveries, dict)
            or discoveries != expected
            or any(type(value) is not int for value in discoveries.values())
        ):
            raise JournalError("Backup discovery identities do not match its cards.")
        settings = payload["settings"]
        if (
            not isinstance(settings, dict)
            or set(settings) != {"seen_count", "voice_enabled"}
            or any(type(value) is not int for value in settings.values())
            or not 0 <= settings["seen_count"] <= len(cards)
            or settings["voice_enabled"] not in (0, 1)
        ):
            raise JournalError("Invalid backup settings.")
        for row in history:
            if (
                not isinstance(row, dict)
                or set(row) != {"organism_key", "card", "archived_on"}
                or not isinstance(row["archived_on"], str)
                or not 1 <= len(row["archived_on"]) <= 100
                or row["organism_key"] != card_key(row["card"])
            ):
                raise JournalError("Invalid archived fact snapshot.")

    @staticmethod
    def _envelope(payload):
        return {
            "format": FORMAT,
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "sha256": digest(payload),
        }

    def _write(self, path, payload):
        envelope = self._envelope(payload)
        if len(json.dumps(envelope, indent=2, ensure_ascii=False).encode()) + 1 > MAX_BYTES:
            raise JournalError("Backup exceeds the 32 MiB limit.")
        atomic_json(path, envelope)

    def export(self, path):
        """Write one consistent snapshot. The caller owns the destination choice."""
        try:
            with closing(self.repository._connect()) as connection, connection:
                connection.execute("BEGIN")
                self.repository._initialize(connection)
                payload = self._snapshot(connection)
            self._write(path, payload)
            return Path(path)
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as error:
            raise JournalError(f"Could not export journal: {error}") from error

    def _read(self, path):
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise JournalError("Backup exceeds the 32 MiB limit.")
        data = json.loads(raw)
        if (
            not isinstance(data, dict)
            or set(data) != {"format", "version", "created_at", "payload", "sha256"}
            or data["format"] != FORMAT
            or type(data["version"]) is not int
            or data["version"] != 1
            or not isinstance(data["created_at"], str)
            or len(data["created_at"]) > 100
        ):
            raise JournalError("Unsupported backup format or version.")
        payload = data["payload"]
        if data["sha256"] != digest(payload):
            raise JournalError("Backup checksum does not match; the file may be damaged.")
        self._validate(payload)
        return payload, sha256(raw).hexdigest()

    def preview(self, path, mode="merge"):
        """Validate without replacing data; bind confirmation to both file and journal."""
        if mode not in ("merge", "replace"):
            raise JournalError("Choose merge or replace.")
        try:
            incoming, file_hash = self._read(path)
            with closing(self.repository._connect()) as connection, connection:
                connection.execute("BEGIN")
                self.repository._initialize(connection)
                current = self._snapshot(connection)
            new_keys = set(incoming["discoveries"]) - current["discoveries"].keys()
            added = len(new_keys) if mode == "merge" else len(incoming["cards"])
            skipped = len(incoming["cards"]) - added if mode == "merge" else 0
            return RestorePreview(
                Path(path),
                file_hash,
                digest(current),
                mode,
                added,
                skipped,
                len(current["cards"]) + added if mode == "merge" else added,
            )
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RecursionError) as error:
            raise JournalError(f"Could not preview backup: {error}") from error

    def restore(self, preview, safety_directory):
        """Commit a confirmed restore after a durable safety copy; never narrate cards."""
        try:
            incoming, file_hash = self._read(preview.path)
            if file_hash != preview.file_hash:
                raise JournalError("Backup changed; preview it again.")
            if preview.mode not in ("merge", "replace"):
                raise JournalError("Choose merge or replace.")
            with closing(self.repository._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                self.repository._initialize(connection)
                current = self._snapshot(connection)
                if digest(current) != preview.current_hash:
                    raise JournalError("Journal changed; preview the restore again.")
                safety = Path(safety_directory) / ("before-restore-" + uuid4().hex + ".json")
                self._write(safety, current)
                if preview.mode == "replace":
                    result = incoming
                else:
                    result = self._merge(current, incoming)
                self._replace(connection, result)
            return safety
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RecursionError) as error:
            raise JournalError(
                f"Could not restore journal; saved cards were not changed: {error}"
            ) from error

    @staticmethod
    def _merge(current, incoming):
        position = max((row["position"] for row in current["cards"]), default=-1) + 1
        for row in incoming["cards"]:
            # Keep existing snapshots; accepting revised facts is a separate explicit action.
            key = organism_key_from_snapshot(row["card"])
            if key not in current["discoveries"]:
                current["cards"].append({"position": position, "card": row["card"]})
                current["discoveries"][key] = position
                position += 1
        histories = {digest(row) for row in current["history"]}
        for row in incoming["history"]:
            if digest(row) not in histories:
                current["history"].append(row)
                histories.add(digest(row))
        return current

    def _replace(self, connection, payload):
        self._validate(payload)
        connection.execute("DELETE FROM discoveries")
        connection.execute("DELETE FROM cards")
        connection.executemany(
            "INSERT INTO cards VALUES (?, ?)",
            (
                (row["position"], json.dumps(row["card"], ensure_ascii=False))
                for row in payload["cards"]
            ),
        )
        connection.executemany(
            "INSERT INTO discoveries VALUES (?, ?)", payload["discoveries"].items()
        )
        settings = dict(payload["settings"], migration_complete=1)
        connection.executemany(
            "INSERT OR REPLACE INTO journal_settings VALUES (?, ?)", settings.items()
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS card_history ("
            "id INTEGER PRIMARY KEY, organism_key TEXT NOT NULL, card_json TEXT NOT NULL, archived_on TEXT NOT NULL)"
        )
        connection.execute("DELETE FROM card_history")
        connection.executemany(
            "INSERT INTO card_history(organism_key, card_json, archived_on) VALUES (?, ?, ?)",
            (
                (
                    row["organism_key"],
                    json.dumps(row["card"], ensure_ascii=False),
                    row["archived_on"],
                )
                for row in payload["history"]
            ),
        )


def organism_key_from_snapshot(snapshot):
    from catalog import OrganismEntry

    return organism_key(OrganismEntry(**snapshot["organism"]))
