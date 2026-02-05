import os
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import requests
from core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    SCOPES,
)

router = APIRouter(prefix="/auth")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")



@router.get("/login")
def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = GOOGLE_REDIRECT_URI

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return RedirectResponse(auth_url)

@router.get("/callback")
def auth_callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        return RedirectResponse("/auth/error?reason=missing_code")

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )

    tokens = token_response.json()

    if "access_token" not in tokens:
        return RedirectResponse("/auth/error?reason=token_failed")

    request.session["user"] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
    }

    return RedirectResponse(
    url=f"{FRONTEND_URL}/dashboard",
    status_code=302
)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}
