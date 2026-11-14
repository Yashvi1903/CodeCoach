import sqlite3
import time

from app.editorial.schema import EditorialSection
from app.hints.schema import HintSet

EMPTY_ROUND_RETRY_SECONDS = 24 * 3600

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    contest_id INTEGER PRIMARY KEY, fetched_at REAL NOT NULL, n_sections INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS editorial_sections (
    contest_id INTEGER NOT NULL, idx TEXT NOT NULL, json TEXT NOT NULL,
    PRIMARY KEY (contest_id, idx));
CREATE TABLE IF NOT EXISTS hint_sets (
    contest_id INTEGER NOT NULL, idx TEXT NOT NULL, json TEXT NOT NULL,
    PRIMARY KEY (contest_id, idx));
CREATE TABLE IF NOT EXISTS unlock_state (
    user_id TEXT NOT NULL, contest_id INTEGER NOT NULL, idx TEXT NOT NULL, level INTEGER NOT NULL,
    PRIMARY KEY (user_id, contest_id, idx));
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.executescript(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    # --- rounds / editorial sections ---
    def needs_editorial(self, contest_id: int) -> bool:
        row = self._db.execute(
            "SELECT fetched_at, n_sections FROM rounds WHERE contest_id=?", (contest_id,)
        ).fetchone()
        if row is None:
            return True
        fetched_at, n_sections = row
        return n_sections == 0 and time.time() - fetched_at > EMPTY_ROUND_RETRY_SECONDS

    def save_round(self, contest_id: int, sections: list[EditorialSection]) -> None:
        with self._db:
            self._db.execute("DELETE FROM editorial_sections WHERE contest_id=?", (contest_id,))
            self._db.executemany(
                "INSERT INTO editorial_sections (contest_id, idx, json) VALUES (?,?,?)",
                [(contest_id, s.index, s.model_dump_json()) for s in sections],
            )
            self._db.execute(
                "INSERT OR REPLACE INTO rounds (contest_id, fetched_at, n_sections) VALUES (?,?,?)",
                (contest_id, time.time(), len(sections)),
            )

    def get_section(self, contest_id: int, index: str) -> EditorialSection | None:
        row = self._db.execute(
            "SELECT json FROM editorial_sections WHERE contest_id=? AND idx=?", (contest_id, index)
        ).fetchone()
        return EditorialSection.model_validate_json(row[0]) if row else None

    # --- hint sets ---
    def save_hint_set(self, hs: HintSet) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO hint_sets (contest_id, idx, json) VALUES (?,?,?)",
                (hs.contest_id, hs.index, hs.model_dump_json()),
            )

    def get_hint_set(self, contest_id: int, index: str) -> HintSet | None:
        row = self._db.execute(
            "SELECT json FROM hint_sets WHERE contest_id=? AND idx=?", (contest_id, index)
        ).fetchone()
        return HintSet.model_validate_json(row[0]) if row else None

    # --- unlock state ---
    def get_unlocked(self, user_id: str, contest_id: int, index: str) -> int:
        row = self._db.execute(
            "SELECT level FROM unlock_state WHERE user_id=? AND contest_id=? AND idx=?",
            (user_id, contest_id, index),
        ).fetchone()
        return row[0] if row else 0

    def set_unlocked(self, user_id: str, contest_id: int, index: str, level: int) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO unlock_state (user_id, contest_id, idx, level) VALUES (?,?,?,?)",
                (user_id, contest_id, index, level),
            )