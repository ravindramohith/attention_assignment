import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "your-secure-secret-key"  # In production use env var
ALGORITHM = "HS256"


def create_token(username: str) -> dict:
    expires = datetime.utcnow() + timedelta(days=7)
    token = jwt.encode(
        {"username": username, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer", "username": username}


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["username"]
    except:
        return None
