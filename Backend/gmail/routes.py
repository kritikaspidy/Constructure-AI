import re
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr

from core.session import require_auth_header
from ai.service import draft_reply, summarize_email
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
def gmail_profile(authorization: str = Header(None)):
    user = require_auth_header(authorization)
    return fetch_gmail_profile(user["access_token"])


@router.get("/messages")
def gmail_messages(max_results: int = 5, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    data = list_messages(user["access_token"], max_results=max_results)
    return {
        "resultSizeEstimate": data.get("resultSizeEstimate", 0),
        "messages": data.get("messages", []),
    }


@router.get("/message/{message_id}")
def gmail_message(message_id: str, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    msg = get_message_metadata(user["access_token"], message_id)

    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return normalize_message_summary(msg)


@router.delete("/message/{message_id}")
def gmail_delete(message_id: str, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    result = delete_message(user["access_token"], message_id)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result)

    return result


@router.post("/send")
def gmail_send(payload: SendEmailBody, authorization: str = Header(None)):
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
def gmail_last(n: int = 5, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    return {"emails": fetch_last_email_summaries(user["access_token"], max_results=n)}


@router.get("/message/{message_id}/full")
def gmail_message_full(message_id: str, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    msg = read_message_with_body(user["access_token"], message_id)

    if "error" in msg:
        raise HTTPException(status_code=400, detail=msg)

    return msg


@router.get("/last_with_summaries")
def gmail_last_with_summaries(n: int = 5, authorization: str = Header(None)):
    user = require_auth_header(authorization)
    return {"emails": fetch_last_with_ai_summaries(user["access_token"], max_results=n)}


@router.get("/last_with_replies")
def gmail_last_with_replies(n: int = 5, authorization: str = Header(None)):
    user = require_auth_header(authorization)

    base = list_messages(user["access_token"], max_results=n)
    ids = [m["id"] for m in base.get("messages", [])]

    results = []
    for idx, mid in enumerate(ids, start=1):
        msg = read_message_with_body(user["access_token"], mid)
        if "error" in msg:
            continue

        summary = summarize_email(msg["body"])
        reply = draft_reply(msg.get("from") or "", msg.get("subject") or "", msg["body"])

        # extract recipient email
        from_header = msg.get("from") or ""
        m = re.search(r"<([^>]+)>", from_header)
        to_email = m.group(1) if m else from_header.strip()

        results.append({
            "index": idx,
            "id": msg["id"],
            "from": msg.get("from"),
            "to_email": to_email,
            "subject": msg.get("subject"),
            "ai_summary": summary,
            "ai_reply_draft": reply
        })

    return {"emails": results}


@router.post("/send_reply")
def gmail_send_reply(payload: SendReplyBody, authorization: str = Header(None)):
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
        subject=sub
