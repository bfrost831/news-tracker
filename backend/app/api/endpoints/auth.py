from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from pydantic import BaseModel, EmailStr
import jwt
import uuid
from datetime import datetime, timedelta

router = APIRouter()


class MagicLinkRequest(BaseModel):
    email: EmailStr


class TokenVerify(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_magic_link_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "magic_link",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_session_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours),
        "type": "session",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@router.post("/magic-link")
async def request_magic_link(data: MagicLinkRequest, db: AsyncSession = Depends(get_db)):
    """Send a magic link email to the user."""
    token = create_magic_link_token(data.email)
    magic_link = f"https://news-tracker.vercel.app/auth/verify?token={token}"

    # TODO: Send email via Resend
    # import resend
    # resend.api_key = settings.resend_api_key
    # resend.Emails.send({...})

    return {"message": "Check your email for a login link"}


@router.post("/verify", response_model=AuthResponse)
async def verify_magic_link(data: TokenVerify, db: AsyncSession = Depends(get_db)):
    """Verify magic link token and create session."""
    try:
        payload = jwt.decode(data.token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "magic_link":
            raise HTTPException(status_code=400, detail="Invalid token type")

        email = payload["email"]

        # Get or create user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email=email, last_login_at=datetime.utcnow())
            db.add(user)
        else:
            user.last_login_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        session_token = create_session_token(user.id, user.email)
        return AuthResponse(access_token=session_token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
