# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import create_token, verify_token
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from .chatbot import generate_response
from .database import (
    init_db,
    register_user,
    authenticate_user,
    save_chat,
    add_message_to_chat,
    get_user_chats,
)

app = FastAPI()
security = HTTPBearer()


class UserCredentials(BaseModel):
    username: str
    password: str


# backend/main.py - update ChatMessage model
class ChatMessage(BaseModel):
    username: str
    chat_id: Optional[int]
    message: str
    title: Optional[str]
    messages: Optional[List[Dict[str, str]]] = []  # Add this field


@app.on_event("startup")
def startup_event():
    init_db()


@app.post("/register")
def register(credentials: UserCredentials):
    if register_user(credentials.username, credentials.password):
        return {"message": "Registration successful"}
    raise HTTPException(status_code=400, detail="Username already exists")


@app.post("/login")
def login(credentials: UserCredentials):
    if authenticate_user(credentials.username, credentials.password):
        return create_token(credentials.username)
    raise HTTPException(status_code=401)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


@app.post("/verify")
def verify(username: str = Depends(get_current_user)):
    return {"username": username}


@app.post("/chat")
async def chat(message: ChatMessage, current_user: str = Depends(get_current_user)):
    if message.username != current_user:
        raise HTTPException(status_code=403)

    # Pass full message history to generate_response
    response = generate_response(
        session_id=message.username,
        user_input=message.message,
        message_history=message.messages,
    )

    if message.chat_id:
        add_message_to_chat(message.chat_id, message.message, response)
    else:
        title = message.title or message.message[:30] + "..."
        message.chat_id = save_chat(message.username, title, message.message, response)

    return {"response": response, "chat_id": message.chat_id}


@app.get("/chats/{username}")
def get_chats(username: str, current_user: str = Depends(get_current_user)):
    if username != current_user:
        raise HTTPException(status_code=403)
    return get_user_chats(username)
