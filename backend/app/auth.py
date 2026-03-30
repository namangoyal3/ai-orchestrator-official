import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.config import settings
from app.database import get_db
from app.models import APIKey, Organization

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    return f"gw-{secrets.token_urlsafe(32)}"


async def validate_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> tuple[APIKey, Organization]:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Pass X-API-Key header.")

    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    db_key = result.scalar_one_or_none()

    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")

    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key has expired.")

    # Load organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == db_key.org_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found.")

    # Update last used
    db_key.last_used_at = datetime.utcnow()
    await db.commit()

    return db_key, org


def create_admin_token(org_id: str) -> str:
    payload = {
        "org_id": org_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "admin",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_admin_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
