from pydantic import BaseModel, ConfigDict, model_validator

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from ..core.database import get_db
from ..core.auth import get_current_active_user, require_roles, ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN
from ..models.snapshot import Snapshot, SnapshotType
from ..services.snapshot import get_snapshot, list_snapshots, validate_snapshot

router = APIRouter()


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    actor_uid: str
    snapshot_type: SnapshotType
    scope: str
    tag: Optional[str] = None
    storage_path: str
    size_bytes: int
    checksum: Optional[str] = None
    oci_image_digest: Optional[str] = None
    gvisor_version: Optional[str] = None
    metadata: dict
    is_valid: bool
    validation_error: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def convert_datetimes(cls, data):
        if hasattr(data, '__dict__'):
            for field in ['created_at', 'expires_at']:
                if hasattr(data, field) and getattr(data, field) is not None:
                    val = getattr(data, field)
                    if hasattr(val, 'isoformat'):
                        data.__dict__[field] = val.isoformat()
            # Handle SQLAlchemy MetaData object
            if hasattr(data, 'metadata') and not isinstance(data.metadata, dict):
                from sqlalchemy import MetaData
                if isinstance(data.metadata, MetaData):
                    data.__dict__['metadata'] = {}
                else:
                    try:
                        data.__dict__['metadata'] = dict(data.metadata) if data.metadata else {}
                    except (TypeError, ValueError):
                        data.__dict__['metadata'] = {}
        return data


class SnapshotListResponse(BaseModel):
    snapshots: List[SnapshotResponse]
    total: int
    skip: int
    limit: int


@router.get("/snapshots", response_model=SnapshotListResponse)
async def list_all_snapshots(
    actor_id: Optional[int] = None,
    actor_uid: Optional[str] = None,
    snapshot_type: Optional[SnapshotType] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> SnapshotListResponse:
    """List all snapshots with filtering."""
    snapshots, total = await list_snapshots(
        db,
        actor_id=actor_id,
        actor_uid=actor_uid,
        snapshot_type=snapshot_type,
        tag=tag,
        skip=skip,
        limit=limit,
    )
    return SnapshotListResponse(
        snapshots=snapshots,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot_endpoint(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> Snapshot:
    """Get snapshot by ID."""
    snapshot = await get_snapshot(db, snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    return snapshot


@router.post("/snapshots/{snapshot_id}/validate")
async def validate_snapshot_endpoint(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> dict:
    """Validate snapshot integrity."""
    is_valid, error = await validate_snapshot(db, snapshot_id)
    return {
        "snapshot_id": snapshot_id,
        "is_valid": is_valid,
        "error": error,
    }