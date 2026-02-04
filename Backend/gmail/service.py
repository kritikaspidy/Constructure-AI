import base64
from email.mime.text import MIMEText
import re
from typing import Any, Dict, List, Optional, Tuple
from ai.service import summarize_email


import requests


GMAIL_BASE = "https://www.googleapis.com/gmail/v1/users/me"


def _headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def fetch_gmail_profile(access_token: str) -> Dict[str, Any]:
    r = requests.get(f"{GMAIL_BASE}/profile", headers=_headers(access_token))
    return r.json()


def list_messages(access_token: str, max_results: int = 10) -> Dict[str, Any]:
    # labelIds=INBOX ensures inbox only. q can be added later.
    params = {"maxResults": max_results, "labelIds": "INBOX"}
    r = requests.get(f"{GMAIL_BASE}/messages", headers=_headers(access_token), params=params)
    return r.json()


def get_message_metadata(access_token: str, message_id: str) -> Dict[str, Any]:
    params = {
        "format": "metadata",
        "metadataHeaders": ["From", "To", "Subject", "Date"],
    }
    r = requests.get(
        f"{GMAIL_BASE}/messages/{message_id}",
        headers=_headers(access_token),
        params=params,
    )
    return r.json()


def delete_message(access_token: str, message_id: str) -> Dict[str, Any]:
    r = requests.delete(
        f"{GMAIL_BASE}/messages/{message_id}",
        headers=_headers(access_token),
    )
    # Gmail delete returns empty body on success
    if r.status_code in (200, 204):
        return {"status": "deleted", "id": message_id}
    try:
        return r.json()
    except Exception:
        return {"error": "delete_failed", "status_code": r.status_code, "text": r.text}


def send_email(access_token: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    payload = {"raw": raw}
    r = requests.post(
        f"{GMAIL_BASE}/messages/send",
        headers={**_headers(access_token), "Content-Type": "application/json"},
        json=payload,
    )
    return r.json()


def extract_headers(msg: Dict[str, Any]) -> Dict[str, str]:
    # Gmail returns headers in msg["payload"]["headers"]
    headers_list = (msg.get("payload") or {}).get("headers") or []
    out: Dict[str, str] = {}
    for h in headers_list:
        name = h.get("name")
        value = h.get("value")
        if name and value:
            out[name] = value
    return out


def normalize_message_summary(msg: Dict[str, Any]) -> Dict[str, Any]:
    headers = extract_headers(msg)
    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "from": headers.get("From"),
        "to": headers.get("To"),
        "subject": headers.get("Subject"),
        "date": headers.get("Date"),
        "snippet": msg.get("snippet"),
    }

def fetch_last_email_summaries(access_token: str, max_results: int = 5):
    data = list_messages(access_token, max_results=max_results)
    ids = [m["id"] for m in data.get("messages", [])]

    summaries = []
    for mid in ids:
        msg = get_message_metadata(access_token, mid)
        if "error" in msg:
            continue
        summaries.append(normalize_message_summary(msg))

    return summaries

def _b64url_decode(data: str) -> str:
    # Gmail uses base64url without padding
    if not data:
        return ""
    padding = "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode((data + padding).encode("utf-8"))
    return decoded.decode("utf-8", errors="replace")


def get_message_full(access_token: str, message_id: str) -> Dict[str, Any]:
    params = {"format": "full"}
    r = requests.get(
        f"{GMAIL_BASE}/messages/{message_id}",
        headers=_headers(access_token),
        params=params,
    )
    return r.json()


def _walk_parts(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (text_plain, text_html) from a Gmail payload by walking MIME parts.
    """
    mime_type = payload.get("mimeType")
    body = (payload.get("body") or {}).get("data")

    text_plain = None
    text_html = None

    if mime_type == "text/plain" and body:
        text_plain = _b64url_decode(body)
        return text_plain, None

    if mime_type == "text/html" and body:
        text_html = _b64url_decode(body)
        return None, text_html

    # multipart/*
    for part in payload.get("parts", []) or []:
        p_plain, p_html = _walk_parts(part)

        if p_plain and not text_plain:
            text_plain = p_plain
        if p_html and not text_html:
            text_html = p_html

        if text_plain and text_html:
            break

    return text_plain, text_html


def strip_html(html: str) -> str:
    # Very basic HTML-to-text (good enough for MVP). We'll improve later if needed.
    if not html:
        return ""
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n\s+\n", "\n\n", html)
    return html.strip()


def extract_message_body(full_message: Dict[str, Any]) -> str:
    payload = full_message.get("payload") or {}
    text_plain, text_html = _walk_parts(payload)

    if text_plain and text_plain.strip():
        return text_plain.strip()

    if text_html and text_html.strip():
        return strip_html(text_html)

    # fallback: sometimes body isn't in payload, but snippet exists
    return (full_message.get("snippet") or "").strip()


def read_message_with_body(access_token: str, message_id: str) -> Dict[str, Any]:
    full_msg = get_message_full(access_token, message_id)
    if "error" in full_msg:
        return full_msg

    summary = normalize_message_summary(full_msg)
    summary["body"] = extract_message_body(full_msg)
    return summary

def fetch_last_with_ai_summaries(access_token: str, max_results: int = 5):
    data = list_messages(access_token, max_results=max_results)
    ids = [m["id"] for m in data.get("messages", [])]

    output = []

    for mid in ids:
        msg = read_message_with_body(access_token, mid)
        if "error" in msg:
            continue

        summary = summarize_email(msg["body"])

        output.append({
            "id": msg["id"],
            "from": msg["from"],
            "subject": msg["subject"],
            "ai_summary": summary,
        })

    return output

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SCOPES

def refresh_access_token_if_needed(user_session: dict) -> str:
    """
    Refreshes access token using refresh_token if expired.
    Updates user_session in-place.
    Returns a valid access token.
    """
    creds = Credentials(
        token=user_session.get("access_token"),
        refresh_token=user_session.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    # If Google marks it expired, refresh it
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        user_session["access_token"] = creds.token

    return user_session.get("access_token")
