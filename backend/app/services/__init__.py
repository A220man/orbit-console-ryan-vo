"""Service layer."""

from .user import get_user_by_email, create_user_from_oidc, update_user_roles
from .actor import (
    create_actor,
    get_actor,
    get_actor_by_uid,
    list_actors,
    update_actor,
    delete_actor,
    transition_actor_state,
    commit_actor,
    pause_actor,
    resume_actor,
    revert_actor,
    dump_actor,
    get_actor_stats,
)
from .snapshot import create_snapshot, get_snapshot, list_snapshots, validate_snapshot
from .telemetry import (
    record_actor_metric,
    record_actor_telemetry,
    get_template_metrics,
    get_actor_telemetry,
    get_actor_count_by_status,
    get_crash_count,
)

__all__ = [
    "get_user_by_email",
    "create_user_from_oidc",
    "update_user_roles",
    "create_actor",
    "get_actor",
    "get_actor_by_uid",
    "list_actors",
    "update_actor",
    "delete_actor",
    "transition_actor_state",
    "commit_actor",
    "pause_actor",
    "resume_actor",
    "revert_actor",
    "dump_actor",
    "get_actor_stats",
    "create_snapshot",
    "get_snapshot",
    "list_snapshots",
    "validate_snapshot",
    "record_actor_metric",
    "record_actor_telemetry",
    "get_template_metrics",
    "get_actor_telemetry",
    "get_actor_count_by_status",
    "get_crash_count",
]