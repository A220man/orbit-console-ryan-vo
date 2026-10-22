from pydantic import BaseModel, Field, ConfigDict, model_validator

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from ..core.database import get_db
from ..core.auth import get_current_active_user, require_roles, ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN
from ..models.actor import Actor, ActorStatus, SnapshotScope
from ..models.snapshot import Snapshot, SnapshotType
from ..services.actor import (
    create_actor,
    get_actor,
    get_actor_by_uid,
    list_actors,
    update_actor,
    delete_actor,
    transition_actor_state,
    pause_actor,
    resume_actor,
    commit_actor,
    revert_actor,
    dump_actor,
    get_actor_stats,
)
from ..services.snapshot import list_snapshots

router = APIRouter()


# Request/Response models
class ActorCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    atespace: str = Field(..., min_length=1, max_length=255)
    template_namespace: str = Field(..., min_length=1, max_length=255)
    template_name: str = Field(..., min_length=1, max_length=255)
    container_name: str = Field(default="main", min_length=1, max_length=255)
    snapshot_scope: SnapshotScope = Field(default=SnapshotScope.DATA)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)


class ActorUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    labels: Optional[dict[str, str]] = None
    annotations: Optional[dict[str, str]] = None
    snapshot_scope: Optional[SnapshotScope] = None


class ActorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: str
    name: str
    atespace: str
    template_namespace: str
    template_name: str
    container_name: str
    status: ActorStatus
    snapshot_scope: SnapshotScope
    node_id: Optional[str] = None
    worker_id: Optional[str] = None
    labels: dict[str, str]
    annotations: dict[str, str]
    created_at: str
    updated_at: str
    last_transition_at: str
    resumed_at: Optional[str] = None
    paused_at: Optional[str] = None
    suspended_at: Optional[str] = None
    crashed_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def convert_datetimes(cls, data):
        if hasattr(data, '__dict__'):
            for field in ['created_at', 'updated_at', 'last_transition_at',
                          'resumed_at', 'paused_at', 'suspended_at', 'crashed_at']:
                if hasattr(data, field) and getattr(data, field) is not None:
                    val = getattr(data, field)
                    if hasattr(val, 'isoformat'):
                        data.__dict__[field] = val.isoformat()
            # Handle snapshots relationship if loaded
            if hasattr(data, 'snapshots') and data.snapshots:
                for snap in data.snapshots:
                    if hasattr(snap, '__dict__'):
                        for sfield in ['created_at', 'expires_at']:
                            if hasattr(snap, sfield) and getattr(snap, sfield) is not None:
                                val = getattr(snap, sfield)
                                if hasattr(val, 'isoformat'):
                                    snap.__dict__[sfield] = val.isoformat()
                            snap.__dict__['metadata'] = {} if snap.metadata is None else (dict(snap.metadata) if hasattr(snap.metadata, '__iter__') and not isinstance(snap.metadata, (str, dict)) else snap.metadata)
        return data


class ActorListResponse(BaseModel):
    actors: List[ActorResponse]
    total: int
    skip: int
    limit: int


class StateTransitionRequest(BaseModel):
    force: bool = False


class PauseRequest(BaseModel):
    timer_seconds: Optional[int] = Field(None, ge=0)
    snapshot_scope: Optional[SnapshotScope] = None


class CommitRequest(BaseModel):
    tag: Optional[str] = Field(None, min_length=1, max_length=255)
    snapshot_scope: Optional[SnapshotScope] = None


class RevertRequest(BaseModel):
    tag: Optional[str] = Field(None, min_length=1, max_length=255)
    snapshot_id: Optional[int] = None


class DumpRequest(BaseModel):
    tag: str = Field(..., min_length=1, max_length=255)


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


# Actor CRUD
@router.post("", response_model=ActorResponse, status_code=status.HTTP_201_CREATED)
async def create_actor_endpoint(
    actor_data: ActorCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Create a new actor."""
    # Check if UID already exists
    existing = await get_actor_by_uid(db, actor_data.uid)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Actor with UID '{actor_data.uid}' already exists",
        )

    actor = await create_actor(
        db,
        uid=actor_data.uid,
        name=actor_data.name,
        atespace=actor_data.atespace,
        template_namespace=actor_data.template_namespace,
        template_name=actor_data.template_name,
        container_name=actor_data.container_name,
        snapshot_scope=actor_data.snapshot_scope,
        labels=actor_data.labels,
        annotations=actor_data.annotations,
    )
    return actor


@router.get("", response_model=ActorListResponse)
async def list_actors_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ActorStatus] = None,
    atespace: Optional[str] = None,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    node_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> ActorListResponse:
    """List actors with filtering and pagination."""
    actors, total = await list_actors(
        db,
        skip=skip,
        limit=limit,
        status=status,
        atespace=atespace,
        template_namespace=template_namespace,
        template_name=template_name,
        node_id=node_id,
    )
    return ActorListResponse(
        actors=actors,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats")
async def get_actor_stats_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> dict:
    """Get aggregate actor statistics."""
    return await get_actor_stats(db)


@router.get("/{actor_id}", response_model=ActorResponse)
async def get_actor_endpoint(
    actor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Get actor by ID."""
    actor = await get_actor(db, actor_id)
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor {actor_id} not found",
        )
    return actor


@router.get("/uid/{uid}", response_model=ActorResponse)
async def get_actor_by_uid_endpoint(
    uid: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Get actor by UID."""
    actor = await get_actor_by_uid(db, uid)
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor with UID '{uid}' not found",
        )
    return actor


@router.patch("/{actor_id}", response_model=ActorResponse)
async def update_actor_endpoint(
    actor_id: int,
    actor_data: ActorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Update actor metadata."""
    actor = await update_actor(
        db,
        actor_id,
        name=actor_data.name,
        labels=actor_data.labels,
        annotations=actor_data.annotations,
        snapshot_scope=actor_data.snapshot_scope,
    )
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor {actor_id} not found",
        )
    return actor


@router.delete("/{actor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_actor_endpoint(
    actor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_ADMIN)),
) -> None:
    """Delete an actor."""
    try:
        success = await delete_actor(db, actor_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Actor {actor_id} not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# State transitions
@router.post("/{actor_id}/pause", response_model=ActorResponse)
async def pause_actor_endpoint(
    actor_id: int,
    request: PauseRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Pause actor (RUNNING -> PAUSED)."""
    try:
        actor = await pause_actor(
            db,
            actor_id,
            timer_seconds=request.timer_seconds,
            snapshot_scope=request.snapshot_scope,
        )
        return actor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{actor_id}/resume", response_model=ActorResponse)
async def resume_actor_endpoint(
    actor_id: int,
    node_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Resume actor (PAUSED/SUSPENDED -> RUNNING)."""
    try:
        actor = await resume_actor(db, actor_id, node_id=node_id, worker_id=worker_id)
        return actor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{actor_id}/commit", response_model=ActorResponse)
async def commit_actor_endpoint(
    actor_id: int,
    request: CommitRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Commit actor (RUNNING/PAUSED -> SUSPENDED)."""
    try:
        actor = await commit_actor(
            db,
            actor_id,
            tag=request.tag,
            snapshot_scope=request.snapshot_scope,
        )
        return actor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{actor_id}/revert", response_model=ActorResponse)
async def revert_actor_endpoint(
    actor_id: int,
    request: RevertRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Revert actor to a previous snapshot."""
    try:
        actor = await revert_actor(
            db,
            actor_id,
            tag=request.tag,
            snapshot_id=request.snapshot_id,
        )
        return actor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{actor_id}/dump", response_model=ActorResponse)
async def dump_actor_endpoint(
    actor_id: int,
    request: DumpRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_OPERATOR, ROLE_ADMIN)),
) -> Actor:
    """Dump crashed actor (CRASHED -> SUSPENDED)."""
    try:
        actor = await dump_actor(db, actor_id, tag=request.tag)
        return actor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Snapshots for an actor
@router.get("/{actor_id}/snapshots", response_model=List[SnapshotResponse])
async def list_actor_snapshots(
    actor_id: int,
    snapshot_type: Optional[SnapshotType] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> List[SnapshotResponse]:
    """List snapshots for an actor."""
    snapshots, _ = await list_snapshots(
        db,
        actor_id=actor_id,
        snapshot_type=snapshot_type,
        tag=tag,
        skip=skip,
        limit=limit,
    )
    # Convert to response models to trigger validators
    result = []
    for snap in snapshots:
        data = {
            "id": snap.id,
            "actor_id": snap.actor_id,
            "actor_uid": snap.actor_uid,
            "snapshot_type": snap.snapshot_type,
            "scope": snap.scope,
            "tag": snap.tag,
            "storage_path": snap.storage_path,
            "size_bytes": snap.size_bytes,
            "checksum": snap.checksum,
            "oci_image_digest": snap.oci_image_digest,
            "gvisor_version": snap.gvisor_version,
            "metadata": dict(snap.snapshot_metadata) if snap.snapshot_metadata else {},
            "is_valid": snap.is_valid,
            "validation_error": snap.validation_error,
            "created_at": snap.created_at.isoformat() if snap.created_at else None,
            "expires_at": snap.expires_at.isoformat() if snap.expires_at else None,
        }
        result.append(SnapshotResponse(**data))
    return result