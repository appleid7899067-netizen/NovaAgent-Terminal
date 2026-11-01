import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import field_validator

DB_PATH = os.environ.get("TASKS_DB_PATH", ":memory:")

app = FastAPI(title="Tasks API", version="1.0.0")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('todo', 'doing', 'done')),
            due_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


@contextmanager
def get_db():
    """Yield a SQLite connection, ensuring the schema exists on every connection."""
    conn = get_db_connection()
    try:
        init_db(conn)
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
TitleStr = Annotated[str, Field(min_length=1, max_length=200)]
StatusStr = Annotated[str, Field(pattern=r"^(todo|doing|done)$")]


class TaskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: TitleStr
    status: StatusStr
    due_date: Optional[date] = None

    @field_validator("due_date")
    @classmethod
    def _due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[TitleStr] = None
    status: Optional[StatusStr] = None
    due_date: Optional[date] = None

    @field_validator("due_date")
    @classmethod
    def _due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskResponse(TaskBase):
    id: str
    created_at: str


# ---------------------------------------------------------------------------
# Error handling – one consistent JSON shape everywhere
# ---------------------------------------------------------------------------
class APIError(BaseModel):
    error: dict


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "status": status_code}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "error")
        message = exc.detail.get("message", str(exc.detail))
    else:
        code = "error"
        message = str(exc.detail)
    return _error_response(exc.status_code, code, message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return _error_response(422, "validation_error", "; ".join(parts))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
    responses={422: {"model": APIError}},
)
def create_task(task: TaskCreate, conn: sqlite3.Connection = Depends(get_db)):
    task_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO tasks (id, title, status, due_date, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            task_id,
            task.title,
            task.status,
            task.due_date.isoformat() if task.due_date else None,
            now,
        ),
    )
    conn.commit()
    return TaskResponse(
        id=task_id,
        title=task.title,
        status=task.status,
        due_date=task.due_date,
        created_at=now,
    )


@app.get(
    "/tasks",
    response_model=List[TaskResponse],
    responses={422: {"model": APIError}},
)
def list_tasks(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    query = "SELECT id, title, status, due_date, created_at FROM tasks"
    params: list = []

    if status is not None:
        query += " WHERE status = ?"
        params.append(status)

    if limit is not None:
        if limit < 1:
            raise HTTPException(
                status_code=422,
                detail={"code": "validation_error", "message": "limit must be >= 1"},
            )
        query += " LIMIT ?"
        params.append(limit)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    return [TaskResponse(**dict(row)) for row in rows]


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"model": APIError}, 422: {"model": APIError}},
)
def get_task(task_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.execute(
        "SELECT id, title, status, due_date, created_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Task not found"},
        )
    return TaskResponse(**dict(row))


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"model": APIError}, 422: {"model": APIError}},
)
def update_task(
    task_id: str,
    task_update: TaskUpdate,
    conn: sqlite3.Connection = Depends(get_db),
):
    cursor = conn.execute(
        "SELECT id, title, status, due_date, created_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Task not found"},
        )

    update_data = task_update.model_dump(exclude_unset=True)
    if "due_date" in update_data and update_data["due_date"] is not None:
        update_data["due_date"] = update_data["due_date"].isoformat()

    if not update_data:
        return TaskResponse(**dict(row))

    set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
    values = list(update_data.values()) + [task_id]
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()

    cursor = conn.execute(
        "SELECT id, title, status, due_date, created_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    return TaskResponse(**dict(row))


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    responses={404: {"model": APIError}},
)
def delete_task(task_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Task not found"},
        )
    conn.commit()
    return None
