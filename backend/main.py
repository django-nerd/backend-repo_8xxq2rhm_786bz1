import os
import hashlib
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Character

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def to_str_id(doc: Dict[str, Any]):
    if not doc:
        return doc
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    return d


# Request models
class AuthPayload(BaseModel):
    email: str
    password: str
    username: Optional[str] = None

class CharacterPayload(BaseModel):
    prompt: str
    settings: Dict[str, Any] = {}

class PlanPayload(BaseModel):
    user_id: str
    plan: str


@app.get("/")
async def root():
    return {"message": "Character Creator API"}


@app.post("/api/auth/signup")
async def signup(payload: AuthPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    existing = db["user"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    username = payload.username or payload.email.split("@")[0]
    user = User(email=payload.email, username=username, password_hash=hash_password(payload.password), plan="free")
    user_id = create_document("user", user)
    doc = db["user"].find_one({"_id": ObjectId(user_id)})
    return to_str_id(doc)


@app.post("/api/auth/login")
async def login(payload: AuthPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user = db["user"].find_one({"email": payload.email, "password_hash": hash_password(payload.password)})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return to_str_id(user)


@app.get("/api/me")
async def me(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        user = db["user"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return to_str_id(user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")


@app.post("/api/characters/generate")
async def generate_character(payload: CharacterPayload, user_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # Simulated generation. In a full build, call your AI pipeline here.
    preview = "https://images.unsplash.com/photo-1542272604-787c3835535d?q=80&w=1200&auto=format&fit=crop"  # placeholder render

    char = Character(
        user_id=user_id or "guest",
        prompt=payload.prompt,
        settings=payload.settings,
        preview_url=preview,
    )
    char_id = create_document("character", char)
    doc = db["character"].find_one({"_id": ObjectId(char_id)})
    return to_str_id(doc)


@app.get("/api/characters")
async def list_characters(user_id: str, limit: int = 20):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    docs = get_documents("character", {"user_id": user_id}, limit)
    return [to_str_id(d) for d in docs]


@app.post("/api/user/plan")
async def update_plan(payload: PlanPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    if payload.plan not in {"free", "plus", "pro"}:
        raise HTTPException(status_code=400, detail="Invalid plan")
    try:
        res = db["user"].update_one({"_id": ObjectId(payload.user_id)}, {"$set": {"plan": payload.plan}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        doc = db["user"].find_one({"_id": ObjectId(payload.user_id)})
        return to_str_id(doc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")


@app.get("/test")
async def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
    }
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
