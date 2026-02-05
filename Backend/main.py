from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os
from fastapi.middleware.cors import CORSMiddleware

from auth.routes import router as auth_router
from gmail.routes import router as gmail_router

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
IS_PROD = FRONTEND_URL.startswith("https://")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret"),
    https_only=IS_PROD,        # True on Render
    same_site="none" if IS_PROD else "lax",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(gmail_router)

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/dashboard")
def dashboard():
    return {
        "message": "Logged in successfully",
        "available_actions": [
            "GET /gmail/profile",
            "GET /gmail/messages",
            "POST /auth/logout"
        ]
    }
