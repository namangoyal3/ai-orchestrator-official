"""
API Key Management endpoints (admin/dashboard use).
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import generate_api_key, hash_api_key
from app.database import get_db
from app.models import APIKey, Organization

router = APIRouter(prefix="/admin", tags=["API Keys"])


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$')
    plan: str = Field("starter", pattern=r'^(starter|pro|enterprise)$')


class CreateKeyRequest(BaseModel):
    org_id: str
    name: str = Field(..., min_length=2, max_length=255)
    permissions: list[str] = Field(default=["read", "write"])
    rate_limit_rpm: int = Field(60, ge=1, le=10000)
    rate_limit_daily: int = Field(10000, ge=1, le=1000000)
    expires_days: Optional[int] = Field(None, ge=1, le=3650)


@router.post("/organizations", summary="Create a new organization")
async def create_organization(
    request: CreateOrgRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant organization."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Organization).where(Organization.slug == request.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Slug '{request.slug}' already taken.")

    org = Organization(name=request.name, slug=request.slug, plan=request.plan)
    db.add(org)
    await db.commit()
    await db.refresh(org)

    return {"id": org.id, "name": org.name, "slug": org.slug, "plan": org.plan, "created_at": org.created_at}


@router.get("/organizations", summary="List all organizations")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
    orgs = result.scalars().all()
    return {"organizations": [{"id": o.id, "name": o.name, "slug": o.slug, "plan": o.plan} for o in orgs]}


@router.post("/api-keys", summary="Create an API key")
async def create_api_key(
    request: CreateKeyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key for an organization.
    The full key is returned ONCE — store it securely.
    """
    # Verify org exists
    org_result = await db.execute(select(Organization).where(Organization.id == request.org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    raw_key = generate_api_key()
    expires_at = None
    if request.expires_days:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)

    key = APIKey(
        org_id=request.org_id,
        name=request.name,
        key_hash=hash_api_key(raw_key),
        key_prefix=raw_key[:12],
        permissions=request.permissions,
        rate_limit_rpm=request.rate_limit_rpm,
        rate_limit_daily=request.rate_limit_daily,
        expires_at=expires_at,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return {
        "id": key.id,
        "key": raw_key,  # Only shown once
        "prefix": key.key_prefix,
        "name": key.name,
        "permissions": key.permissions,
        "org_id": org.id,
        "org_name": org.name,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "created_at": key.created_at.isoformat() if key.created_at else None,
        "message": "Save this key securely — it will not be shown again.",
    }


@router.get("/api-keys/{org_id}", summary="List API keys for an organization")
async def list_api_keys(org_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(APIKey).where(APIKey.org_id == org_id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "prefix": k.key_prefix + "...",
                "is_active": k.is_active,
                "permissions": k.permissions,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in keys
        ]
    }


@router.delete("/api-keys/{key_id}", summary="Revoke an API key")
async def revoke_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found.")
    key.is_active = False
    await db.commit()
    return {"message": f"API key '{key.name}' has been revoked."}
