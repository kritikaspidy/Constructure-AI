# Constructure-AI
AI Gmail assistant: OAuth login + chatbot UI + read/summarize, draft/send replies, and delete emails. Built with FastAPI + Next.js. Vercel-ready.

## Live Demo (Vercel)
**Frontend:** https://your-app-name.vercel.app

## Features
-  Google Login (OAuth 2.0)
-  AI chatbot-style dashboard for email help
-  Email summarization (2–3 sentence summaries)
-  AI-drafted replies (professional + concise)
-  Gmail actions (read / draft reply / delete) *(as implemented)*
-  Deployed frontend on Vercel

---

## Tech Stack
**Frontend**
- React / Next.js
- Axios (API calls)
- (Any UI library you used: Tailwind, ShadCN, etc.)

**Backend**
- FastAPI
- Google APIs (Gmail + OAuth)
- OpenAI-compatible SDK pointed to **Groq** (AI provider)

**AI Provider**
- Groq (OpenAI-compatible endpoint)
- Default model: `llama-3.1-8b-instant` (configurable)


## Setup Instructions

### Clone the repository
```bash
git clone https://github.com/kritikaspidy/Constructure-AI.git
cd Backend



cd backend
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

