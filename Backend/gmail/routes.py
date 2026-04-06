import re
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, EmailStr

from core.session import require_auth_header
from ai.service import draft_reply, summarize_email
from demo.store import list_demo_messages, get_demo_message_metadata, read_demo_message_with_body
from gmail.service import (
    fetch_gmail_profile,
    list_messages,
    get_message_metadata,
    delete_message,
    send_email,
    normalize_message_summary,
    fetch_last_email_summaries,
    read_message_with_body,
    fetch_last_with_ai_summaries,
)

router = APIRouter(prefix="/gmail")
VALID_MODES = {"demo", "real"}


def _resolve_mode(mode: str) -> str:
    value = (mode or "real").strip().lower()
    if value not in VALID_MODES:
        raise HTTPException(status_code=400, detail="mode must be demo or real")
    return value


def _extract_to_email(value: str) -> str:
    if not value:
        return ""
    m = re.search(r"<([^>]+)>", value)
    return m.group(1) if m else value.strip()


def _demo_last(n: int):
    data = list_demo_messages(max_results=n)
    out = []
    for item in data.get("messages", []):
        msg = get_demo_message_metadata(item["id"])
        if msg:
            out.append(msg)
    return out


class SendEmailBody(BaseModel):
    to: EmailStr
    subject: str
    body: str


class SendReplyBody(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    confirm: bool = False


@router.get("/profile")
def gmail_profile(mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        return {"emailAddress": "demo@constructure.ai", "source": "demo"}
    user = require_auth_header(authorization)
    return fetch_gmail_profile(user["access_token"])


@router.get("/messages")
def gmail_messages(max_results: int = 5, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        data = list_demo_messages(max_results=max_results)
    else:
        user = require_auth_header(authorization)
        data = list_messages(user["access_token"], max_results=max_results)
    return {
        "resultSizeEstimate": data.get("resultSizeEstimate", 0),
        "messages": data.get("messages", []),
    }


@router.get("/message/{message_id}")
def gmail_message(message_id: str, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        msg = get_demo_message_metadata(message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Demo message not found")
        return msg

    user = require_auth_header(authorization)
    msg = get_message_metadata(user["access_token"], message_id)

    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return normalize_message_summary(msg)


@router.delete("/message/{message_id}")
def gmail_delete(message_id: str, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        return {"status": "disabled_in_demo_mode", "id": message_id}

    user = require_auth_header(authorization)
    result = delete_message(user["access_token"], message_id)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result)

    return result


@router.post("/send")
def gmail_send(payload: SendEmailBody, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        return {"status": "disabled_in_demo_mode"}

    user = require_auth_header(authorization)
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
def gmail_last(n: int = 5, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        return {"emails": _demo_last(n)}
    user = require_auth_header(authorization)
    return {"emails": fetch_last_email_summaries(user["access_token"], max_results=n)}


@router.get("/message/{message_id}/full")
def gmail_message_full(message_id: str, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        msg = read_demo_message_with_body(message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Demo message not found")
        return msg

    user = require_auth_header(authorization)
    msg = read_message_with_body(user["access_token"], message_id)

    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return msg


@router.get("/last_with_summaries")
def gmail_last_with_summaries(n: int = 5, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        results = []
        for idx, msg in enumerate(_demo_last(n), start=1):
            full_msg = read_demo_message_with_body(msg["id"])
            if not full_msg:
                continue
            results.append(
                {
                    "index": idx,
                    "id": full_msg["id"],
                    "from": full_msg.get("from"),
                    "subject": full_msg.get("subject"),
                    "ai_summary": summarize_email(full_msg.get("body", "")),
                }
            )
        return {"emails": results}

    user = require_auth_header(authorization)
    return {"emails": fetch_last_with_ai_summaries(user["access_token"], max_results=n)}


@router.get("/last_with_replies")
def gmail_last_with_replies(n: int = 5, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    results = []

    if resolved_mode == "demo":
        messages = _demo_last(n)
        for idx, msg in enumerate(messages, start=1):
            full_msg = read_demo_message_with_body(msg["id"])
            if not full_msg:
                continue
            body = full_msg.get("body") or ""
            summary = summarize_email(body)
            reply = draft_reply(full_msg.get("from") or "", full_msg.get("subject") or "", body)
            results.append(
                {
                    "index": idx,
                    "id": full_msg["id"],
                    "from": full_msg.get("from"),
                    "to_email": _extract_to_email(full_msg.get("from") or ""),
                    "subject": full_msg.get("subject"),
                    "ai_summary": summary,
                    "ai_reply_draft": reply,
                }
            )
        return {"emails": results}

    user = require_auth_header(authorization)
    base = list_messages(user["access_token"], max_results=n)
    ids = [m["id"] for m in base.get("messages", [])]

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
            "to_email": _extract_to_email(msg.get("from") or ""),
            "subject": msg.get("subject"),
            "ai_summary": summary,
            "ai_reply_draft": reply
        })

    return {"emails": results}


@router.post("/send_reply")
def gmail_send_reply(payload: SendReplyBody, mode: str = Query("real"), authorization: str = Header(None)):
    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "demo":
        return {"status": "disabled_in_demo_mode"}

    user = require_auth_header(authorization)

    if not payload.confirm:
        return {
            "status": "needs_confirmation",
            "message": "Confirm sending reply",
            "to": payload.to_email,
            "subject": payload.subject,
        }

    subject = payload.subject or ""
    if subject and not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    result = send_email(
        user["access_token"],
        to=payload.to_email,
        subject=subject,
        body=payload.body,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return {
        "status": "sent",
        "to": payload.to_email,
        "subject": subject,
        "id": result.get("id"),
        "threadId": result.get("threadId"),
        "labelIds": result.get("labelIds"),
    }
