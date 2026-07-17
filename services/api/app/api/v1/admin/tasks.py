import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.database import TZ_SHANGHAI
from app.core.deps import DbSession, require_role
from app.core.errors import BadRequest, NotFound
from app.models.base import AuditLog, Task

router = APIRouter()


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    task_type: str = Field(alias="taskType", min_length=1, max_length=64)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    assigned_to: str | None = Field(default=None, alias="assignedTo")
    due_at: datetime | None = Field(default=None, alias="dueAt")

    model_config = {"populate_by_name": True}


class UpdateTaskRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = Field(default=None, alias="assignedTo")
    description: str | None = None

    model_config = {"populate_by_name": True}


def _task_to_dict(task: Task) -> dict:
    """Convert a Task ORM instance to an API response dict."""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "taskType": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "assignedTo": str(task.assigned_to) if task.assigned_to else None,
        "dueAt": task.due_at.isoformat() if task.due_at else None,
        "completedAt": task.completed_at.isoformat() if task.completed_at else None,
        "createdAt": task.created_at.isoformat(),
        "updatedAt": task.updated_at.isoformat(),
    }


@router.post("/tasks")
async def create_task(
    body: CreateTaskRequest,
    request: Request,
    db: DbSession,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        assigned = uuid.UUID(body.assigned_to) if body.assigned_to else None
    except ValueError:
        raise BadRequest("Invalid UUID for assignedTo", request_id=request_id)

    task = Task(
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        priority=body.priority,
        assigned_to=assigned,
        due_at=body.due_at,
    )
    db.add(task)

    audit = AuditLog(
        actor_id=uuid.UUID(user["id"]),
        action="create_task",
        resource_type="task",
        resource_id=task.id,
        details={
            "title": body.title,
            "taskType": body.task_type,
            "priority": body.priority,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(task)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _task_to_dict(task),
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    request: Request,
    db: DbSession,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise NotFound(f"Task {task_id} not found", request_id=request_id)

    result = await db.execute(select(Task).where(Task.id == tid))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFound(f"Task {task_id} not found", request_id=request_id)

    changes: dict = {}
    if body.status is not None:
        valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
        if body.status not in valid_statuses:
            raise BadRequest(
                f"Invalid status '{body.status}'. Must be one of: {', '.join(sorted(valid_statuses))}",
                request_id=request_id,
            )
        task.status = body.status
        changes["status"] = body.status
        if body.status == "completed":
            task.completed_at = now
            changes["completedAt"] = now.isoformat()
    if body.priority is not None:
        task.priority = body.priority
        changes["priority"] = body.priority
    if body.assigned_to is not None:
        try:
            task.assigned_to = uuid.UUID(body.assigned_to)
        except ValueError:
            raise BadRequest("Invalid UUID for assignedTo", request_id=request_id)
        changes["assignedTo"] = body.assigned_to
    if body.description is not None:
        task.description = body.description
        changes["description"] = body.description

    audit = AuditLog(
        actor_id=uuid.UUID(user["id"]),
        action="update_task",
        resource_type="task",
        resource_id=tid,
        details=changes,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(task)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _task_to_dict(task),
    }


@router.get("/tasks")
async def list_tasks(
    request: Request,
    db: DbSession,
    status: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)

    if status:
        stmt = stmt.where(Task.status == status)
        count_stmt = count_stmt.where(Task.status == status)

    stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    total = (await db.execute(count_stmt)).scalar() or 0

    items = [_task_to_dict(t) for t in tasks]
    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasNext": offset + limit < total,
        },
    }
