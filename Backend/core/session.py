# core/session.py
from fastapi import HTTPException
from typing import Optional

def require_auth_header(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    return {"access_token": token}
