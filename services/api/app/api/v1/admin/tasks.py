import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.deps import require_role
from app.core.errors import NotFound

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


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
    due_at: datetime | None = Field(default=None, alias="dueAt")

    model_config = {"populate_by_name": True}


@router.post("/tasks")
async def create_task(
    body: CreateTaskRequest,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    task_id = uuid.uuid4()

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": str(task_id),
            "title": body.title,
            "description": body.description,
            "taskType": body.task_type,
            "status": "pending",
            "priority": body.priority,
            "assignedTo": body.assigned_to,
            "dueAt": body.due_at.isoformat() if body.due_at else None,
            "createdAt": now.isoformat(),
        },
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(task_id)
    except ValueError:
        raise NotFound(f"Task {task_id} not found", request_id=request_id)

    completed_at = None
    if body.status == "completed":
        completed_at = now.isoformat()

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": task_id,
            "title": "Deploy sandbags to riverbank",
            "description": "Coordinate with logistics to deploy 500 sandbags.",
            "taskType": "response",
            "status": body.status or "in_progress",
            "priority": body.priority or "high",
            "assignedTo": body.assigned_to or user["id"],
            "dueAt": body.due_at.isoformat() if body.due_at else None,
            "completedAt": completed_at,
            "updatedAt": now.isoformat(),
        },
    }
