"""
FastAPI Application - All Tasks Combined
Tasks: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 8.1, 8.2
"""

import os
import secrets
import sqlite3
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated

from app.config import get_settings

# ============================================================================
# CONFIGURATION
# ============================================================================

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Security
security = HTTPBasic()


# ============================================================================
# MANUAL RATE LIMITER (Task 6.5)
# ============================================================================


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        # Remove old requests outside the window
        self.requests[key] = [t for t in self.requests[key] if now - t < window]

        if len(self.requests[key]) >= limit:
            return False

        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


# Task 6.2 models
class UserBase(BaseModel):
    username: str


class User(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


# Task 6.4/6.5 models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


# Task 7.1 - Roles and Permissions
class Role(BaseModel):
    name: str
    permissions: list[str]


# Task 8.2 - Todo model
class TodoBase(BaseModel):
    title: str
    description: str


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class Todo(TodoBase):
    id: int
    completed: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# IN-MEMORY DATA STORES
# ============================================================================

# Users database (in-memory for tasks 6.1-7.1)
fake_users_db: dict[str, UserInDB] = {}

# Roles database
roles_db: dict[str, Role] = {
    "admin": Role(name="admin", permissions=["create", "read", "update", "delete"]),
    "user": Role(name="user", permissions=["read", "update"]),
    "guest": Role(name="guest", permissions=["read"]),
}

# Todo database (in-memory)
todos_db: dict[int, Todo] = {}
next_todo_id = 1


# ============================================================================
# DATABASE SETUP (Task 8.1)
# ============================================================================

DB_PATH = "users.db"


def init_db():
    """Initialize SQLite database for users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    return conn


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# DEPENDENCIES
# ============================================================================


# Task 6.1/6.2 - Basic authentication dependency
async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> UserInDB:
    """Validate HTTP Basic credentials."""
    # Use secrets.compare_digest for timing-safe comparison
    user_username = credentials.username
    password = credentials.password

    # Find user in database
    user = fake_users_db.get(user_username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user


# Task 6.4/6.5/7.1 - JWT authentication dependency
async def get_current_user_jwt(request: Request) -> str:
    """Validate JWT token from Authorization header."""
    credentials = request.headers.get("Authorization")
    if not credentials or not credentials.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# Task 7.1 - Role checking dependency
def check_role(required_role: str):
    """Dependency factory for role-based access control."""

    async def role_checker(
        current_user: Annotated[str, Depends(get_current_user_jwt)],
    ) -> str:
        # Get user from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, role FROM users WHERE username = ?", (current_user,)
        )
        result = cursor.fetchone()
        conn.close()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_role = result[1] if len(result) > 1 else "guest"

        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return current_user

    return role_checker


# ============================================================================
# DOCS PROTECTION DEPENDENCY (Task 6.3)
# ============================================================================


async def verify_docs_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> bool:
    """Verify credentials for documentation access in DEV mode."""
    # Use secrets.compare_digest for timing-safe comparison
    if not (
        secrets.compare_digest(credentials.username, settings.DOCS_USER)
        and secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app: FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown


# Create FastAPI app with conditional docs configuration
if settings.MODE == "PROD":
    # Hide all documentation endpoints
    app = FastAPI(
        title="FastAPI Application",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
else:
    # DEV mode - protect docs with basic auth
    app = FastAPI(
        title="FastAPI Application",
        lifespan=lifespan,
        dependencies=[Depends(verify_docs_credentials)],
    )


# ============================================================================
# ROUTES
# ============================================================================


# ============================================================================
# TASK 6.1 & 6.2: Basic HTTP Authentication /login (GET)
# ============================================================================


@app.get("/login", status_code=200)
async def login_basic_auth(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
):
    """Task 6.1 & 6.2: Basic HTTP authentication login endpoint (GET).

    Returns welcome message with username.
    """
    return {"message": f"Welcome, {current_user.username}!"}


# ============================================================================
# TASK 6.2, 6.5: User Registration
# ============================================================================


@app.post("/register", status_code=201)
async def register_user(request: Request, user: User):
    """Task 6.2 & 6.5: Register a new user with hashed password.

    Rate limited to 1 request per minute (Task 6.5).
    """
    # Rate limiting: 1 request per minute (Task 6.5)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(f"register:{client_ip}", limit=1, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
        )

    # Check if user exists
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Use secrets.compare_digest for timing-safe username comparison (Task 6.5)
    # Hash password
    hashed_password = get_password_hash(user.password)

    # Create user in database
    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db[user.username] = user_in_db

    return {"message": "New user created"}


# ============================================================================
# TASK 6.4 & 6.5: JWT Authentication /login (POST)
# ============================================================================


@app.post("/login", response_model=Token)
async def login_jwt(request: Request, user_login: UserLogin):
    """Task 6.4 & 6.5: JWT login endpoint (POST).

    Rate limited to 5 requests per minute (Task 6.5).
    Returns JWT access token.
    """
    # Rate limiting: 5 requests per minute (Task 6.5)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(f"login:{client_ip}", limit=5, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
        )

    # Find user in database
    user = fake_users_db.get(user_login.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify password
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================================
# TASK 6.4: Protected Resource
# ============================================================================


@app.get("/protected_resource")
async def protected_resource(
    current_user: Annotated[str, Depends(get_current_user_jwt)],
):
    """Task 6.4: Protected resource requiring JWT authentication."""
    return {"message": "Access granted", "user": current_user}


# ============================================================================
# TASK 7.1: Role-Based Access Control (RBAC)
# ============================================================================


@app.get("/admin_resource")
async def admin_resource(current_user: Annotated[str, Depends(check_role("admin"))]):
    """Task 7.1: Admin-only endpoint (full CRUD permissions)."""
    return {
        "message": "Admin access granted",
        "user": current_user,
        "permissions": roles_db["admin"].permissions,
    }


@app.get("/user_resource")
async def user_resource(current_user: Annotated[str, Depends(check_role("user"))]):
    """Task 7.1: User endpoint (read + update permissions)."""
    return {
        "message": "User access granted",
        "user": current_user,
        "permissions": roles_db["user"].permissions,
    }


@app.get("/guest_resource")
async def guest_resource(current_user: Annotated[str, Depends(check_role("guest"))]):
    """Task 7.1: Guest endpoint (read-only permissions)."""
    return {
        "message": "Guest access granted",
        "user": current_user,
        "permissions": roles_db["guest"].permissions,
    }


@app.get("/roles")
async def get_roles():
    """Task 7.1: Get all available roles and permissions."""
    return {name: role.permissions for name, role in roles_db.items()}


# ============================================================================
# TASK 8.1: SQLite Database User Registration
# ============================================================================


@app.post("/db/register", status_code=201)
async def register_to_db(user: User):
    """Task 8.1: Register user directly to SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Insert new user (password stored as-is for this task)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user.username, user.password),
    )
    conn.commit()
    conn.close()

    return {"message": "User registered successfully!"}


# ============================================================================
# TASK 8.2: CRUD Operations with Todo Resource
# ============================================================================


@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate):
    """Task 8.2: Create a new todo item."""
    global next_todo_id

    new_todo = Todo(
        id=next_todo_id, title=todo.title, description=todo.description, completed=False
    )
    todos_db[next_todo_id] = new_todo
    next_todo_id += 1

    return new_todo


@app.get("/todos/{todo_id}", response_model=Todo)
async def read_todo(todo_id: int):
    """Task 8.2: Get a todo item by ID."""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )

    return todos_db[todo_id]


@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Task 8.2: Update an existing todo item."""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )

    existing_todo = todos_db[todo_id]

    # Update fields if provided
    if todo_update.title is not None:
        existing_todo.title = todo_update.title
    if todo_update.description is not None:
        existing_todo.description = todo_update.description
    if todo_update.completed is not None:
        existing_todo.completed = todo_update.completed

    return existing_todo


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """Task 8.2: Delete a todo item."""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )

    del todos_db[todo_id]
    return {"message": "Todo deleted successfully"}


@app.get("/todos", response_model=list[Todo])
async def list_todos():
    """Task 8.2: List all todo items."""
    return list(todos_db.values())


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint with application info."""
    return {
        "message": "FastAPI Application",
        "mode": settings.MODE,
        "endpoints": {
            "auth": ["/register", "/login (GET - basic auth)", "/login (POST - JWT)"],
            "protected": ["/protected_resource"],
            "rbac": ["/admin_resource", "/user_resource", "/guest_resource", "/roles"],
            "database": ["/db/register"],
            "todos": ["/todos", "/todos/{id}"],
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
