from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, EmailStr
from gmail.service import fetch_last_email_summaries
from gmail.service import read_message_with_body
from gmail.service import fetch_last_with_ai_summaries
from ai.service import draft_reply, summarize_email
from gmail.service import fetch_last_email_summaries, read_message_with_body
import re
from gmail.service import send_email
from gmail.service import refresh_access_token_if_needed


from core.session import require_auth
from gmail.service import (
    fetch_gmail_profile,
    list_messages,
    get_message_metadata,
    delete_message,
    send_email,
    normalize_message_summary,
)

router = APIRouter(prefix="/gmail")

class SendReplyBody(BaseModel):
    email_index: int
    body: str
    confirm: bool = False


@router.get("/profile")
def gmail_profile(request: Request):
    user = require_auth(request)
    return fetch_gmail_profile(user["access_token"])


@router.get("/messages")
def gmail_messages(request: Request, max_results: int = 5):
    user = require_auth(request)
    data = list_messages(user["access_token"], max_results=max_results)

    # data looks like: { "messages": [{id, threadId}, ...], "resultSizeEstimate": n }
    # We keep it simple first, just return IDs.
    return {
        "resultSizeEstimate": data.get("resultSizeEstimate", 0),
        "messages": data.get("messages", []),
    }


@router.get("/message/{message_id}")
def gmail_message(request: Request, message_id: str):
    user = require_auth(request)
    msg = get_message_metadata(user["access_token"], message_id)

    # If Google returns error JSON, surface it cleanly
    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return normalize_message_summary(msg)


@router.delete("/message/{message_id}")
def gmail_delete(request: Request, message_id: str):
    user = require_auth(request)
    result = delete_message(user["access_token"], message_id)

    # If deletion fails, show error details
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result)

    return result


class SendEmailBody(BaseModel):
    to: EmailStr
    subject: str
    body: str


@router.post("/send")
def gmail_send(request: Request, payload: SendEmailBody):
    user = require_auth(request)
    result = send_email(
        user["access_token"],
        to=payload.to,
        subject=payload.subject,
        body=payload.body,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return {
        "status": "sent",
        "id": result.get("id"),
        "threadId": result.get("threadId"),
        "labelIds": result.get("labelIds"),
    }

@router.get("/last")
def gmail_last(request: Request, n: int = 5):
    user = require_auth(request)
    return {"emails": fetch_last_email_summaries(user["access_token"], max_results=n)}


@router.get("/message/{message_id}/full")
def gmail_message_full(request: Request, message_id: str):
    user = require_auth(request)
    msg = read_message_with_body(user["access_token"], message_id)

    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return msg


@router.get("/last_with_summaries")
def gmail_last_with_summaries(request: Request, n: int = 5):
    user = require_auth(request)
    return {
        "emails": fetch_last_with_ai_summaries(user["access_token"], max_results=n)
    }

@router.get("/last_with_replies")
def gmail_last_with_replies(request: Request, n: int = 5):
    user = require_auth(request)

    # Get last N IDs
    base = list_messages(user["access_token"], max_results=n)
    ids = [m["id"] for m in base.get("messages", [])]

    results = []
    session_map = []

    for idx, mid in enumerate(ids, start=1):
        msg = read_message_with_body(user["access_token"], mid)
        if "error" in msg:
            continue

        summary = summarize_email(msg["body"])
        reply = draft_reply(msg.get("from") or "", msg.get("subject") or "", msg["body"])

        results.append({
            "index": idx,
            "id": msg["id"],
            "from": msg.get("from"),
            "subject": msg.get("subject"),
            "ai_summary": summary,
            "ai_reply_draft": reply
        })

        session_map.append({
            "index": idx,
            "id": msg["id"],
            "from": msg.get("from"),
            "subject": msg.get("subject"),
        })

    # Store map so user can say "send reply to email 2"
    request.session["last_emails"] = session_map

    return {"emails": results}

@router.post("/send_reply")
def gmail_send_reply(request: Request, payload: SendReplyBody):
    user = require_auth(request)
    access_token = refresh_access_token_if_needed(user)
    request.session["user"] = user  # persist refreshed token


    # last_emails is stored by /gmail/last_with_replies
    last_emails = request.session.get("last_emails") or []

    match = next((e for e in last_emails if e.get("index") == payload.email_index), None)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid email index. Call GET /gmail/last_with_replies?n=5 first."
        )

    # confirmation gate
    if not payload.confirm:
        return {
            "status": "needs_confirmation",
            "message": f"Confirm sending reply to email #{payload.email_index}",
            "to": match.get("from"),
            "subject": match.get("subject"),
        }

    from_header = match.get("from") or ""
    subject = match.get("subject") or ""

    # Extract email address from: 'Name <email@domain>'
    m = re.search(r"<([^>]+)>", from_header)
    to_email = m.group(1) if m else from_header.strip()

    if not to_email or "@" not in to_email:
        raise HTTPException(status_code=400, detail=f"Could not extract recipient email from: {from_header}")

    if subject and not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    result = send_email(
    access_token,
    to=to_email,
    subject=subject,
    body=payload.body
)


    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return {
        "status": "sent",
        "to": to_email,
        "subject": subject,
        "id": result.get("id"),
        "threadId": result.get("threadId"),
        "labelIds": result.get("labelIds"),
    }


@router.get("/debug/session")
def debug_session(request: Request):
    return {
        "has_user": "user" in request.session,
        "user_keys": list((request.session.get("user") or {}).keys()),
        "has_refresh_token": bool((request.session.get("user") or {}).get("refresh_token")),
    }
