"""SQLite persistence for the CommentScope experiment."""
import csv
import io
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class ParticipantLockedError(RuntimeError):
    pass


class ParticipantCompletedError(RuntimeError):
    pass


class DuplicateSubmissionError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    participant_id TEXT NOT NULL,
    mode TEXT NOT NULL CHECK(mode IN ('pilot', 'formal')),
    client_instance_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'reset')),
    current_stage TEXT NOT NULL,
    current_article_order INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    completed_at TEXT,
    reset_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_participant ON sessions(participant_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
CREATE TABLE IF NOT EXISTS article_sessions (
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    article_order INTEGER NOT NULL,
    article_id TEXT NOT NULL,
    condition TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'active', 'completed')),
    current_stage TEXT NOT NULL,
    reading_start_time TEXT,
    reading_end_time TEXT,
    initial_reading_time_ms INTEGER,
    document_height REAL,
    normalized_scroll_distance REAL,
    comment_interaction_count INTEGER NOT NULL DEFAULT 0,
    scroll_event_count INTEGER NOT NULL DEFAULT 0,
    total_scroll_distance_px REAL NOT NULL DEFAULT 0,
    max_scroll_y REAL NOT NULL DEFAULT 0,
    comment_click_count INTEGER NOT NULL DEFAULT 0,
    comment_open_count INTEGER NOT NULL DEFAULT 0,
    comment_close_count INTEGER NOT NULL DEFAULT 0,
    paragraph_toggle_count INTEGER NOT NULL DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    PRIMARY KEY(session_id, article_order)
);
CREATE TABLE IF NOT EXISTS events (
    event_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    article_id TEXT,
    article_order INTEGER,
    stage TEXT,
    question_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    client_occurred_at TEXT NOT NULL,
    received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, event_row_id);
CREATE TABLE IF NOT EXISTS responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    article_order INTEGER NOT NULL,
    article_id TEXT NOT NULL,
    question_type TEXT NOT NULL,
    question_id TEXT NOT NULL,
    selected_option TEXT NOT NULL,
    correct INTEGER NOT NULL CHECK(correct IN (0, 1)),
    item_start_time TEXT NOT NULL,
    submit_time TEXT NOT NULL,
    elapsed_ms INTEGER NOT NULL,
    option_click_count INTEGER NOT NULL DEFAULT 1,
    option_change_count INTEGER NOT NULL DEFAULT 0,
    scroll_event_count INTEGER NOT NULL DEFAULT 0,
    total_scroll_distance_px REAL NOT NULL DEFAULT 0,
    max_scroll_y REAL NOT NULL DEFAULT 0,
    UNIQUE(session_id, article_order, question_type, question_id)
);
CREATE TABLE IF NOT EXISTS workload_surveys (
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    article_order INTEGER NOT NULL,
    mental_demand INTEGER NOT NULL,
    physical_demand INTEGER NOT NULL,
    temporal_demand INTEGER NOT NULL,
    performance INTEGER NOT NULL,
    effort INTEGER NOT NULL,
    frustration INTEGER NOT NULL,
    reading_continuity INTEGER NOT NULL,
    comment_accessibility INTEGER NOT NULL,
    submitted_at TEXT NOT NULL,
    PRIMARY KEY(session_id, article_order)
);
CREATE TABLE IF NOT EXISTS preferences (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
    ranking_json TEXT NOT NULL,
    preferred_condition TEXT NOT NULL,
    reason TEXT NOT NULL,
    submitted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interviews (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
    answers_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    submitted_at TEXT NOT NULL
);
"""


class ExperimentDatabase:
    def __init__(self, path: Optional[os.PathLike] = None):
        self.path = Path(path or os.environ.get("EXPERIMENT_DB_PATH", Path(__file__).with_name("data") / "experiment.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(SCHEMA)
            self._migrate_interaction_metrics()
            self.conn.commit()

    def close(self):
        with self._lock:
            self.conn.close()

    def _migrate_interaction_metrics(self):
        migrations = {
            "article_sessions": {
                "scroll_event_count": "INTEGER NOT NULL DEFAULT 0",
                "total_scroll_distance_px": "REAL NOT NULL DEFAULT 0",
                "max_scroll_y": "REAL NOT NULL DEFAULT 0",
                "comment_click_count": "INTEGER NOT NULL DEFAULT 0",
                "comment_open_count": "INTEGER NOT NULL DEFAULT 0",
                "comment_close_count": "INTEGER NOT NULL DEFAULT 0",
                "paragraph_toggle_count": "INTEGER NOT NULL DEFAULT 0",
            },
            "events": {
                "article_order": "INTEGER",
                "stage": "TEXT",
                "question_id": "TEXT",
            },
            "responses": {
                "option_click_count": "INTEGER NOT NULL DEFAULT 1",
                "option_change_count": "INTEGER NOT NULL DEFAULT 0",
                "scroll_event_count": "INTEGER NOT NULL DEFAULT 0",
                "total_scroll_distance_px": "REAL NOT NULL DEFAULT 0",
                "max_scroll_y": "REAL NOT NULL DEFAULT 0",
            },
        }
        for table, columns in migrations.items():
            existing = {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for column, definition in columns.items():
                if column not in existing:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


    def _one(self, query, params=()):
        row = self.conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def _many(self, query, params=()):
        return [dict(row) for row in self.conn.execute(query, params).fetchall()]

    def get_session(self, session_id):
        return self._one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))

    def get_active_session_for_participant(self, participant_id):
        return self._one("SELECT * FROM sessions WHERE participant_id = ? AND status = 'active'", (participant_id,))

    def create_or_resume_session(self, participant_id, client_instance_id, mode, articles):
        now = utc_now()
        with self._lock:
            existing = self.get_active_session_for_participant(participant_id)
            if existing:
                if existing["client_instance_id"] != client_instance_id:
                    raise ParticipantLockedError(participant_id)
                self.conn.execute("UPDATE sessions SET last_seen_at = ? WHERE session_id = ?", (now, existing["session_id"]))
                self.conn.commit()
                return self.get_session(existing["session_id"])
            completed = self._one("SELECT 1 FROM sessions WHERE participant_id = ? AND mode = 'formal' AND status = 'completed' LIMIT 1", (participant_id,))
            if completed and mode == "formal":
                raise ParticipantCompletedError(participant_id)
            session_id = uuid.uuid4().hex
            self.conn.execute(
                "INSERT INTO sessions(session_id, participant_id, mode, client_instance_id, status, current_stage, started_at, last_seen_at) VALUES (?, ?, ?, ?, 'active', 'instruction', ?, ?)",
                (session_id, participant_id, mode, client_instance_id, now, now),
            )
            self.conn.executemany(
                "INSERT INTO article_sessions(session_id, article_order, article_id, condition, status, current_stage) VALUES (?, ?, ?, ?, 'pending', 'reading')",
                [(session_id, a["article_order"], a["article_id"], a["condition"]) for a in articles],
            )
            self.conn.commit()
            return self.get_session(session_id)

    def touch_session(self, session_id):
        with self._lock:
            self.conn.execute("UPDATE sessions SET last_seen_at = ? WHERE session_id = ? AND status = 'active'", (utc_now(), session_id))
            self.conn.commit()

    def update_progress(self, session_id, stage, article_order=0):
        with self._lock:
            self.conn.execute("UPDATE sessions SET current_stage = ?, current_article_order = ?, last_seen_at = ? WHERE session_id = ? AND status = 'active'", (stage, article_order, utc_now(), session_id))
            if article_order:
                self.conn.execute("UPDATE article_sessions SET current_stage = ?, status = CASE WHEN ? = 'reading' THEN 'active' ELSE status END, started_at = COALESCE(started_at, ?) WHERE session_id = ? AND article_order = ?", (stage, stage, utc_now(), session_id, article_order))
            self.conn.commit()

    def get_articles(self, session_id):
        return self._many("SELECT * FROM article_sessions WHERE session_id = ? ORDER BY article_order", (session_id,))

    def log_event(self, session_id, article_id, event_type, payload, occurred_at, event_id, article_order=None, stage=None):
        payload = payload or {}
        article_order = article_order if article_order is not None else payload.get("article_order")
        stage = stage if stage is not None else payload.get("stage")
        question_id = payload.get("question_id")
        with self._lock:
            try:
                self.conn.execute("INSERT INTO events(event_id, session_id, article_id, article_order, stage, question_id, event_type, payload_json, client_occurred_at, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (event_id, session_id, article_id, article_order, stage, question_id, event_type, json_text(payload), str(occurred_at), utc_now()))
                self.conn.commit()
            except sqlite3.IntegrityError:
                # Client retries are expected; return the original event as idempotent success.
                if self._one("SELECT event_id FROM events WHERE event_id = ?", (event_id,)):
                    return
                raise

    def list_events(self, session_id=None, mode=None):
        query = "SELECT e.*, s.participant_id, s.mode FROM events e JOIN sessions s ON s.session_id = e.session_id"
        params = []
        clauses = []
        if session_id:
            clauses.append("e.session_id = ?"); params.append(session_id)
        if mode:
            clauses.append("s.mode = ?"); params.append(mode)
        if clauses: query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY e.event_row_id"
        rows = self._many(query, params)
        for row in rows: row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def update_reading(self, session_id, article_order, article_id, start_ms, end_ms, document_height, normalized_scroll_distance, comment_interaction_count, scroll_event_count=0, total_scroll_distance_px=0, max_scroll_y=0, comment_counts=None):
        start_time, end_time = str(start_ms), str(end_ms)
        comment_counts = comment_counts or {}
        with self._lock:
            self.conn.execute("UPDATE article_sessions SET reading_start_time = ?, reading_end_time = ?, initial_reading_time_ms = ?, document_height = ?, normalized_scroll_distance = ?, comment_interaction_count = ?, scroll_event_count = ?, total_scroll_distance_px = ?, max_scroll_y = ?, comment_click_count = ?, comment_open_count = ?, comment_close_count = ?, paragraph_toggle_count = ?, status = 'completed', current_stage = 'reading', completed_at = ? WHERE session_id = ? AND article_order = ? AND article_id = ?", (start_time, end_time, int(end_ms - start_ms), float(document_height), float(normalized_scroll_distance), int(comment_interaction_count), int(scroll_event_count), float(total_scroll_distance_px), float(max_scroll_y), int(comment_counts.get("comment_click_count", 0)), int(comment_counts.get("comment_open_count", 0)), int(comment_counts.get("comment_close_count", 0)), int(comment_counts.get("paragraph_toggle_count", 0)), utc_now(), session_id, article_order, article_id))
            self.conn.commit()

    def insert_response(self, session_id, article_order, article_id, question_type, question_id, selected_option, correct, item_start_ms, submit_ms, option_click_count=1, option_change_count=0, scroll_event_count=0, total_scroll_distance_px=0, max_scroll_y=0):
        option_click_count = 1 if option_click_count is None else option_click_count
        option_change_count = 0 if option_change_count is None else option_change_count
        scroll_event_count = 0 if scroll_event_count is None else scroll_event_count
        total_scroll_distance_px = 0 if total_scroll_distance_px is None else total_scroll_distance_px
        max_scroll_y = 0 if max_scroll_y is None else max_scroll_y
        with self._lock:
            if self._one("SELECT response_id FROM responses WHERE session_id = ? AND article_order = ? AND question_type = ? AND question_id = ?", (session_id, article_order, question_type, question_id)):
                raise DuplicateSubmissionError(question_id)
            self.conn.execute("INSERT INTO responses(session_id, article_order, article_id, question_type, question_id, selected_option, correct, item_start_time, submit_time, elapsed_ms, option_click_count, option_change_count, scroll_event_count, total_scroll_distance_px, max_scroll_y) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (session_id, article_order, article_id, question_type, question_id, selected_option, int(bool(correct)), str(item_start_ms), str(submit_ms), int(submit_ms - item_start_ms), int(option_click_count), int(option_change_count), int(scroll_event_count), float(total_scroll_distance_px), float(max_scroll_y)))
            self.conn.commit()
            return self._one("SELECT * FROM responses WHERE session_id = ? AND article_order = ? AND question_type = ? AND question_id = ?", (session_id, article_order, question_type, question_id))

    def list_responses(self, session_id):
        return self._many("SELECT * FROM responses WHERE session_id = ? ORDER BY response_id", (session_id,))

    def insert_workload(self, session_id, article_order, values):
        with self._lock:
            if self._one("SELECT 1 FROM workload_surveys WHERE session_id = ? AND article_order = ?", (session_id, article_order)):
                raise DuplicateSubmissionError("workload survey already submitted")
            self.conn.execute("INSERT INTO workload_surveys(session_id, article_order, mental_demand, physical_demand, temporal_demand, performance, effort, frustration, reading_continuity, comment_accessibility, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (session_id, article_order, values["mental_demand"], values["physical_demand"], values["temporal_demand"], values["performance"], values["effort"], values["frustration"], values["reading_continuity"], values["comment_accessibility"], utc_now()))
            self.conn.commit()

    def insert_preference(self, session_id, ranking, preferred_condition, reason):
        with self._lock:
            if self._one("SELECT 1 FROM preferences WHERE session_id = ?", (session_id,)):
                raise DuplicateSubmissionError("preference already submitted")
            self.conn.execute("INSERT INTO preferences(session_id, ranking_json, preferred_condition, reason, submitted_at) VALUES (?, ?, ?, ?, ?)", (session_id, json_text(ranking), preferred_condition, reason, utc_now()))
            self.conn.commit()

    def insert_interview(self, session_id, answers, started_at):
        with self._lock:
            if self._one("SELECT 1 FROM interviews WHERE session_id = ?", (session_id,)):
                raise DuplicateSubmissionError("interview already submitted")
            self.conn.execute("INSERT INTO interviews(session_id, answers_json, started_at, submitted_at) VALUES (?, ?, ?, ?)", (session_id, json_text(answers), str(started_at), utc_now()))
            self.conn.commit()

    def finish_session(self, session_id):
        with self._lock:
            self.conn.execute("UPDATE sessions SET status = 'completed', current_stage = 'complete', completed_at = ?, last_seen_at = ? WHERE session_id = ? AND status = 'active'", (utc_now(), utc_now(), session_id))
            self.conn.commit()
            return self.get_session(session_id)

    def reset_participant(self, participant_id):
        with self._lock:
            self.conn.execute("UPDATE sessions SET status = 'reset', reset_at = ?, last_seen_at = ? WHERE participant_id = ? AND status IN ('active', 'completed')", (utc_now(), utc_now(), participant_id))
            self.conn.commit()

    def export_rows(self, mode=None):
        query = "SELECT s.*, a.article_order, a.article_id, a.condition, a.reading_start_time, a.reading_end_time, a.initial_reading_time_ms, a.document_height, a.normalized_scroll_distance, a.comment_interaction_count, a.scroll_event_count AS article_scroll_event_count, a.total_scroll_distance_px AS article_total_scroll_distance_px, a.max_scroll_y AS article_max_scroll_y, a.comment_click_count, a.comment_open_count, a.comment_close_count, a.paragraph_toggle_count, r.question_type, r.question_id, r.selected_option, r.correct, r.item_start_time, r.submit_time, r.elapsed_ms, r.option_click_count, r.option_change_count, r.scroll_event_count AS question_scroll_event_count, r.total_scroll_distance_px AS question_total_scroll_distance_px, r.max_scroll_y AS question_max_scroll_y, w.mental_demand, w.physical_demand, w.temporal_demand, w.performance, w.effort, w.frustration, w.reading_continuity, w.comment_accessibility, p.ranking_json, p.preferred_condition, p.reason, i.answers_json FROM sessions s LEFT JOIN article_sessions a ON a.session_id = s.session_id LEFT JOIN responses r ON r.session_id = s.session_id AND r.article_order = a.article_order LEFT JOIN workload_surveys w ON w.session_id = s.session_id AND w.article_order = a.article_order LEFT JOIN preferences p ON p.session_id = s.session_id LEFT JOIN interviews i ON i.session_id = s.session_id"
        params = []
        if mode: query += " WHERE s.mode = ?"; params.append(mode)
        query += " ORDER BY s.participant_id, a.article_order, r.response_id"
        return self._many(query, params)

    def export_event_rows(self, mode=None):
        query = "SELECT e.event_row_id, e.event_id, e.session_id, s.participant_id, s.mode, s.status AS session_status, e.article_id, e.article_order, e.stage, e.question_id, e.event_type, e.payload_json, e.client_occurred_at, e.received_at FROM events e JOIN sessions s ON s.session_id = e.session_id"
        params = []
        if mode:
            query += " WHERE s.mode = ?"
            params.append(mode)
        query += " ORDER BY e.event_row_id"
        return self._many(query, params)

    def export_events_csv(self, mode=None):
        rows = self.export_event_rows(mode)
        output = io.StringIO()
        fields = [
            "event_row_id", "event_id", "session_id", "participant_id", "mode",
            "session_status", "article_id", "article_order", "stage", "question_id",
            "event_type", "payload_json", "client_occurred_at", "received_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def export_csv(self, mode=None):
        rows = self.export_rows(mode)
        output = io.StringIO()
        default_fields = [
            "session_id", "participant_id", "mode", "status", "current_stage",
            "current_article_order", "started_at", "last_seen_at", "completed_at",
            "article_order", "article_id", "condition", "reading_start_time",
            "reading_end_time", "initial_reading_time_ms",
            "normalized_scroll_distance", "comment_interaction_count",
            "article_scroll_event_count", "article_total_scroll_distance_px",
            "article_max_scroll_y", "comment_click_count", "comment_open_count",
            "comment_close_count", "paragraph_toggle_count", "question_type",
            "question_id", "selected_option", "correct", "item_start_time", "submit_time",
            "elapsed_ms", "option_click_count", "option_change_count",
            "question_scroll_event_count", "question_total_scroll_distance_px",
            "question_max_scroll_y", "mental_demand", "physical_demand", "temporal_demand",
            "performance", "effort", "frustration", "reading_continuity",
            "comment_accessibility", "ranking_json", "preferred_condition", "reason",
            "answers_json",
        ]
        fields = sorted(set(default_fields) | {key for row in rows for key in row})
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)
        return output.getvalue()
