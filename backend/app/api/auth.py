import base64
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.database import get_db, User as UserModel, Session as SessionModel, Message as MessageModel
from app.models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, SessionResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback"

# In-memory OAuth state store (dev only — single-process)
_oauth_states: dict[str, datetime] = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/google/login")
async def google_login():
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc) + timedelta(minutes=10)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
    }
    return RedirectResponse(url="https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@router.get("/google/callback")
async def google_callback(code: str, state: str, error: str = None, db: Session = Depends(get_db)):
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}?error={error}")

    if state not in _oauth_states:
        return RedirectResponse(url=f"{FRONTEND_URL}?error=invalid_state")
    _oauth_states.pop(state, None)

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}?error=token_exchange_failed")

        tokens = token_res.json()
        access_token = tokens.get("access_token")

        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}?error=userinfo_failed")

        google_user = userinfo_res.json()

    google_id = str(google_user["id"])
    email = google_user.get("email", "")
    name = google_user.get("name", email.split("@")[0] if email else "user")

    user = db.query(UserModel).filter(
        (UserModel.google_id == google_id) | (UserModel.email == email)
    ).first()

    if user:
        if not user.google_id:
            user.google_id = google_id
            db.commit()
    else:
        base_username = email.split("@")[0] if email else "google_user"
        username = base_username
        suffix = 1
        while db.query(UserModel).filter(UserModel.username == username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        user = UserModel(
            username=username,
            email=email,
            google_id=google_id,
            password_hash=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    user_data = base64.urlsafe_b64encode(
        json.dumps({"id": user.id, "username": user.username, "email": user.email}).encode()
    ).decode()

    return RedirectResponse(url=f"{FRONTEND_URL}?token={token}&user={user_data}")


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(
        (UserModel.username == user_data.username) | (UserModel.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(400, "Username or email already taken")

    user = UserModel(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(id=user.id, username=user.username, email=user.email),
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(
        (UserModel.username == login_data.username) | (UserModel.email == login_data.username)
    ).first()

    if not user or not user.password_hash or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(id=user.id, username=user.username, email=user.email),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.updated_at.desc()).all()
    return sessions


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = SessionModel(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title="New Chat",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    messages = db.query(MessageModel).filter(
        MessageModel.session_id == session_id,
    ).order_by(MessageModel.timestamp).all()
    return messages
