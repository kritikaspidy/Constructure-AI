# Constructure-AI
AI Gmail assistant: OAuth login + chatbot UI + read/summarize, draft/send replies, and delete emails. Built with FastAPI + Next.js. Vercel-ready.

## Live Demo (Vercel)
**Frontend:** https://constructure-ai-cyan.vercel.app

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
```

## Backend Setup (FastAPI)
```bash
cd backend  
python -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  

Create .env file in backend

Run backend:
uvicorn main:app --reload --port 8000  
```
---

## Frontend Setup (React / Next.js)
```bash
cd frontend  
npm install  
npm run dev  

Create .env.local

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000  
```
---

## Google OAuth Configuration

- Create project in Google Cloud Console
- Enable Gmail API
- Configure OAuth Consent Screen
- Create OAuth Client ID (Web Application)  

#Add redirect URI:  
http://localhost:8000/auth/callback  

#For production:  
https://constructure-ai-zbhw.onrender.com/auth/callback

#Add frontend origins:  
http://localhost:3000  
https://constructure-ai-cyan.vercel.app

- Add required test users in OAuth settings  

---

## Required Environment Variables

#Backend  

GOOGLE_CLIENT_ID=Google OAuth client ID  
GOOGLE_CLIENT_SECRET=Google OAuth secret  
GOOGLE_REDIRECT_URI=OAuth callback URL  
GROQ_API_KEY=AI provider API key  
GROQ_MODEL=AI model name  
FRONTEND_URL=Frontend base URL  

#Frontend  

NEXT_PUBLIC_API_BASE_URL=Backend API URL  

---

## Deployment

- Frontend is deployed on Vercel.
- Backend is deployed on Render.

---

## Assumptions & Limitations

- Gmail API permissions determine available actions
- AI-generated replies may require user review
- Some Gmail scopes may require OAuth verification
- Rate limits apply for Gmail API and AI provider
- Automation limited to implemented features  



