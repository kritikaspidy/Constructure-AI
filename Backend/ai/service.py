import os
from openai import OpenAI

# Groq is OpenAI-compatible. Use OpenAI SDK pointed to Groq.
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Good default Groq model (fast + solid quality)
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def summarize_email(body: str) -> str:
    if not body or not body.strip():
        return "Empty email content."

    prompt = (
        "Summarize this email in 2–3 sentences.\n"
        "Focus on the sender's intent, key details, and any action required.\n\n"
        f"Email:\n{body}"
    )

    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful email assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=160,
    )

    return resp.choices[0].message.content.strip()

def draft_reply(email_from: str, subject: str, body: str) -> str:
    prompt = (
        "Write a professional, concise reply to this email.\n"
        "Be polite, clear, and action-oriented.\n"
        "If the email asks a question, answer it.\n"
        "If details are missing, ask 1–2 clarifying questions.\n"
        "Do NOT include a subject line. Only write the email body.\n\n"
        f"From: {email_from}\n"
        f"Subject: {subject}\n\n"
        f"Email:\n{body}"
    )

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful email assistant that drafts replies."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=220,
    )

    return response.choices[0].message.content.strip()
