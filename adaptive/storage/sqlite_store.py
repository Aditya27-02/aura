from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from adaptive.types import ConceptState, Event, GapHypothesis, MemoryPatch, SessionSummary

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    session_key TEXT,
    subject TEXT,
    started_at TEXT,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS learning_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    subject TEXT,
    concepts TEXT,
    activity TEXT,
    input_mode TEXT,
    response TEXT,
    evaluation TEXT,
    evidence TEXT,
    intervention_id TEXT,
    outcome TEXT
);

CREATE TABLE IF NOT EXISTS concept_state (
    concept_id TEXT PRIMARY KEY,
    mastery_belief REAL,
    state_confidence TEXT,
    last_observed_at TEXT,
    evidence_count INTEGER,
    current_status TEXT,
    recurrence_count INTEGER,
    active_gap_state TEXT,
    recovery_state TEXT
);

CREATE TABLE IF NOT EXISTS gap_hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    concept_id TEXT,
    kind TEXT,
    prior REAL,
    posterior REAL,
    evidence_links TEXT,
    recurrence_count INTEGER
);

CREATE TABLE IF NOT EXISTS session_summaries (
    session_id TEXT PRIMARY KEY,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS compacted_history (
    history_key TEXT PRIMARY KEY,
    subject TEXT,
    payload_json TEXT
);

CREATE TABLE IF NOT EXISTS learning_gaps (
    gap_id TEXT PRIMARY KEY,
    concept_id TEXT,
    misconception_class TEXT,
    hypothesis_probability REAL,
    evidence_count INTEGER,
    recurrence_count INTEGER,
    prerequisites_affected TEXT,
    evidence_ids TEXT,
    first_detected TEXT,
    last_confirmed TEXT,
    status TEXT,
    intervention_ids TEXT,
    reassessment_result TEXT,
    transfer_verified INTEGER,
    recovery_confidence REAL
);
"""


class MemoryStore:
    """Indexed local relational persistence (SQLite) for the learner-memory system."""

    def __init__(self, path: str = ":memory:", check_same_thread: bool = False) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=check_same_thread)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # --- sessions ---

    def create_session(self, session_id: str, session_key: str, subject: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, session_key, subject, started_at) VALUES (?, ?, ?, datetime('now'))",
            (session_id, session_key, subject),
        )
        self.conn.commit()

    def end_session(self, session_id: str) -> None:
        self.conn.execute("UPDATE sessions SET ended_at = datetime('now') WHERE session_id = ?", (session_id,))
        self.conn.commit()

    # --- events ---

    def append_event(self, event: Event) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO learning_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.session_id,
                event.timestamp,
                event.subject,
                json.dumps(event.concepts),
                event.activity,
                event.input_mode,
                json.dumps(event.response) if event.response is not None else None,
                json.dumps(event.evaluation),
                json.dumps(event.evidence),
                event.intervention_id,
                event.outcome,
            ),
        )
        self.conn.commit()

    def query_events(
        self,
        subject: Optional[str] = None,
        concepts: Optional[list[str]] = None,
        since: Optional[str] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Event]:
        sql = "SELECT * FROM learning_events WHERE 1=1"
        args: list[Any] = []
        if subject:
            sql += " AND subject = ?"
            args.append(subject)
        if concepts:
            placeholders = " OR ".join(["concepts LIKE ?"] * len(concepts))
            sql += f" AND ({placeholders})"
            args.extend([f'%"{c}"%' for c in concepts])
        if since:
            sql += " AND timestamp >= ?"
            args.append(since)
        if before:
            sql += " AND timestamp <= ?"
            args.append(before)
        sql += " ORDER BY timestamp ASC"
        if limit:
            sql += " LIMIT ?"
            args.append(limit)
        rows = self.conn.execute(sql, args).fetchall()
        return [self._row_to_event(r) for r in rows]

    def count_pattern(self, marker: str, exclude_event: Optional[str] = None) -> int:
        sql = "SELECT COUNT(*) FROM learning_events WHERE (evidence LIKE ? OR evidence LIKE ? OR evaluation LIKE ?)"
        args: list[Any] = [f'%"{marker}"%', f"%{marker}%", f'%"{marker}"%']
        if exclude_event:
            sql += " AND event_id != ?"
            args.append(exclude_event)
        row = self.conn.execute(sql, args).fetchone()
        return int(row[0])

    @staticmethod
    def _row_to_event(r: sqlite3.Row) -> Event:
        return Event(
            event_id=r["event_id"],
            session_id=r["session_id"],
            timestamp=r["timestamp"],
            subject=r["subject"],
            concepts=json.loads(r["concepts"] or "[]"),
            activity=r["activity"],
            input_mode=r["input_mode"],
            response=json.loads(r["response"]) if r["response"] else None,
            evaluation=json.loads(r["evaluation"] or "{}"),
            evidence=json.loads(r["evidence"] or "{}"),
            intervention_id=r["intervention_id"],
            outcome=r["outcome"],
        )

    # --- concept state ---

    def upsert_concept_state(self, st: ConceptState) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO concept_state VALUES (?,?,?,?,?,?,?,?,?)",
            (
                st.concept_id,
                st.mastery_belief,
                st.state_confidence,
                st.last_observed_at,
                st.evidence_count,
                st.current_status,
                st.recurrence_count,
                st.active_gap_state,
                st.recovery_state,
            ),
        )
        self.conn.commit()

    def get_concept_state(self, cid: str) -> Optional[ConceptState]:
        row = self.conn.execute("SELECT * FROM concept_state WHERE concept_id = ?", (cid,)).fetchone()
        if row is None:
            return None
        return ConceptState(
            concept_id=row["concept_id"],
            mastery_belief=row["mastery_belief"],
            state_confidence=row["state_confidence"],
            last_observed_at=row["last_observed_at"],
            evidence_count=row["evidence_count"],
            current_status=row["current_status"],
            recurrence_count=row["recurrence_count"],
            active_gap_state=row["active_gap_state"],
            recovery_state=row["recovery_state"],
        )

    # --- gap hypotheses ---

    def upsert_gap_hypothesis(self, h: GapHypothesis, hypothesis_id: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO gap_hypotheses VALUES (?,?,?,?,?,?,?)",
            (
                hypothesis_id,
                h.concept_id,
                h.kind,
                h.prior,
                h.posterior,
                json.dumps(h.evidence_links),
                h.recurrence_count,
            ),
        )
        self.conn.commit()

    def get_gap_hypothesis(self, hypothesis_id: str) -> Optional[GapHypothesis]:
        row = self.conn.execute("SELECT * FROM gap_hypotheses WHERE hypothesis_id = ?", (hypothesis_id,)).fetchone()
        if row is None:
            return None
        return GapHypothesis(
            concept_id=row["concept_id"],
            kind=row["kind"],
            prior=row["prior"],
            posterior=row["posterior"],
            evidence_links=json.loads(row["evidence_links"] or "[]"),
            recurrence_count=row["recurrence_count"],
        )

    # --- summaries ---

    def save_summary(self, summary: SessionSummary) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO session_summaries VALUES (?,?)",
            (summary.session_id, json.dumps(summary.__dict__, default=str)),
        )
        self.conn.commit()

    def get_summaries(self, subject: Optional[str] = None, limit: int = 10) -> list[SessionSummary]:
        sql = "SELECT * FROM session_summaries"
        args: list[Any] = []
        if subject:
            sql += " WHERE summary_json LIKE ?"
            args.append(f'%"{subject}"%')
        sql += " ORDER BY rowid DESC LIMIT ?"
        args.append(limit)
        rows = self.conn.execute(sql, args).fetchall()
        out = []
        for r in rows:
            data = json.loads(r["summary_json"])
            out.append(SessionSummary(**data))
        return out

    # --- learning gaps ---

    def upsert_gap(self, gap) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO learning_gaps VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                gap.gap_id,
                gap.concept_id,
                gap.misconception_class,
                gap.hypothesis_probability,
                gap.evidence_count,
                gap.recurrence_count,
                json.dumps(gap.prerequisites_affected),
                json.dumps(gap.evidence_ids),
                gap.first_detected,
                gap.last_confirmed,
                gap.status,
                json.dumps(gap.intervention_ids),
                json.dumps(gap.reassessment_result) if gap.reassessment_result else None,
                1 if gap.transfer_verified else 0,
                gap.recovery_confidence,
            ),
        )
        self.conn.commit()

    def get_gap(self, concept_id: str, misconception_class: str):
        row = self.conn.execute(
            "SELECT * FROM learning_gaps WHERE concept_id = ? AND misconception_class = ?",
            (concept_id, misconception_class),
        ).fetchone()
        return self._row_to_gap(row) if row else None

    def get_gaps(self, concept_id: Optional[str] = None, status: Optional[str] = None) -> list:
        sql = "SELECT * FROM learning_gaps"
        args: list[Any] = []
        if concept_id:
            sql += " WHERE concept_id = ?"
            args.append(concept_id)
        if status:
            sql += " AND status = ?" if not concept_id else " AND status = ?"
            args.append(status)
        rows = self.conn.execute(sql, args).fetchall()
        return [g for g in (self._row_to_gap(r) for r in rows) if g is not None]

    @staticmethod
    def _row_to_gap(r: sqlite3.Row):
        from adaptive.types import LearningGap

        if r is None:
            return None
        return LearningGap(
            gap_id=r["gap_id"],
            concept_id=r["concept_id"],
            misconception_class=r["misconception_class"],
            hypothesis_probability=r["hypothesis_probability"],
            evidence_count=r["evidence_count"],
            recurrence_count=r["recurrence_count"],
            prerequisites_affected=json.loads(r["prerequisites_affected"] or "[]"),
            evidence_ids=json.loads(r["evidence_ids"] or "[]"),
            first_detected=r["first_detected"],
            last_confirmed=r["last_confirmed"],
            status=r["status"],
            intervention_ids=json.loads(r["intervention_ids"] or "[]"),
            reassessment_result=json.loads(r["reassessment_result"]) if r["reassessment_result"] else None,
            transfer_verified=bool(r["transfer_verified"]),
            recovery_confidence=r["recovery_confidence"],
        )

    # --- deterministic commit of a MemoryPatch ---

    def validate_and_commit(self, patch: MemoryPatch) -> None:
        if not isinstance(patch, MemoryPatch):
            raise TypeError("memory curator proposals must be MemoryPatch objects")
        try:
            for st in patch.concept_state_updates.values():
                self.upsert_concept_state(st)
            for hid, h in patch.gap_hypothesis_updates.items():
                self.upsert_gap_hypothesis(h, hid)
            for gap in patch.gap_updates.values():
                self.upsert_gap(gap)
            for ev in patch.new_events:
                self.append_event(ev)
            if patch.new_summary is not None:
                self.save_summary(patch.new_summary)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise