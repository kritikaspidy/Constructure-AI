import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent / "demo_emails.sqlite3"

SEED_EMAILS = [
    {
        "id": "demo-1",
        "thread_id": "demo-t-1",
        "from_email": "Sarah Kim <sarah@northwindlabs.com>",
        "to_email": "you@demo.local",
        "subject": "Quick sync on onboarding rollout",
        "date": "Mon, 01 Apr 2026 10:14:00 +0000",
        "snippet": "Can we align on timeline and owner mapping for onboarding rollout?",
        "body": "Hi team,\n\nCan we do a quick sync tomorrow on the onboarding rollout? I want to align on the final timeline and owner mapping before we share this with customer success.\n\nThanks,\nSarah",
    },
    {
        "id": "demo-2",
        "thread_id": "demo-t-2",
        "from_email": "Billing Desk <billing@acme-payments.com>",
        "to_email": "you@demo.local",
        "subject": "Invoice INV-4821 is due this Friday",
        "date": "Mon, 01 Apr 2026 07:32:00 +0000",
        "snippet": "Reminder: invoice INV-4821 for $1,240 is due.",
        "body": "Hello,\n\nThis is a reminder that invoice INV-4821 for $1,240 is due this Friday. Let us know if you need a revised copy or PO details.\n\nRegards,\nBilling Desk",
    },
    {
        "id": "demo-3",
        "thread_id": "demo-t-3",
        "from_email": "Ravi Patel <ravi@talentbridge.io>",
        "to_email": "you@demo.local",
        "subject": "Candidate profile for backend role",
        "date": "Sun, 31 Mar 2026 15:05:00 +0000",
        "snippet": "Sharing a candidate profile with 6 years of Python/FastAPI experience.",
        "body": "Hi,\n\nSharing a strong backend candidate profile with 6 years of Python/FastAPI experience and recent work on large-scale API integrations. If interested, I can schedule a screening slot this week.\n\nBest,\nRavi",
    },
]


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_demo_store() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                from_email TEXT,
                to_email TEXT,
                subject TEXT,
                date TEXT,
                snippet TEXT,
                body TEXT
            )
            """
        )

        count = conn.execute("SELECT COUNT(*) AS c FROM demo_emails").fetchone()["c"]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO demo_emails
                (id, thread_id, from_email, to_email, subject, date, snippet, body)
                VALUES
                (:id, :thread_id, :from_email, :to_email, :subject, :date, :snippet, :body)
                """,
                SEED_EMAILS,
            )
        conn.commit()


def _as_summary(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "threadId": row["thread_id"],
        "from": row["from_email"],
        "to": row["to_email"],
        "subject": row["subject"],
        "date": row["date"],
        "snippet": row["snippet"],
    }


def list_demo_messages(max_results: int = 5) -> Dict[str, Any]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT id FROM demo_emails
            ORDER BY date DESC
            LIMIT ?
            """,
            (max_results,),
        ).fetchall()
    return {"resultSizeEstimate": len(rows), "messages": [{"id": r["id"]} for r in rows]}


def get_demo_message_metadata(message_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM demo_emails WHERE id = ?", (message_id,)).fetchone()
    return _as_summary(row) if row else None


def read_demo_message_with_body(message_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM demo_emails WHERE id = ?", (message_id,)).fetchone()
    if not row:
        return None
    out = _as_summary(row)
    out["body"] = row["body"]
    return out

