import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.storage import store
from app.utils.auth import hash_password, verify_password, create_access_token, require_user

router = APIRouter()


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(data: UserRegister):
    existing = store.list("users", filter_fn=lambda u: u.get("username") == data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = {
        "id": str(uuid.uuid4()),
        "username": data.username,
        "password_hash": hash_password(data.password),
        "target_band": None,
        "native_language": "vi",
        "llm_config": None,
    }
    store.save("users", user)
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "id": user["id"], "username": user["username"], "target_band": user["target_band"], "native_language": user["native_language"]}


@router.post("/login")
async def login(data: UserLogin):
    existing = store.list("users", filter_fn=lambda u: u.get("username") == data.username)
    if not existing or not verify_password(data.password, existing[0].get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(existing[0]["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh(user: dict = Depends(require_user)):
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}
