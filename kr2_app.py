"""
FastAPI КР2 - Контрольная работа №2
Все 7 заданий в одном приложении
"""

from fastapi import FastAPI, HTTPException, Header, Response, Request
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
import time
from itsdangerous import TimestampSigner, SignatureExpired, BadSignature

app = FastAPI(title="FastAPI KR2")

# ============================================================================
# TASK 3.1: User Creation with Pydantic Model
# ============================================================================


class UserCreate(BaseModel):
    """Model for user creation with validation"""

    name: str
    email: EmailStr
    age: Optional[int] = None
    is_subscribed: Optional[bool] = False

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("age must be a positive integer")
        return v


@app.post("/create_user")
def create_user(user: UserCreate):
    """Create user endpoint - accepts POST with user data"""
    return {
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "is_subscribed": user.is_subscribed,
    }


# ============================================================================
# TASK 3.2: Product Search and Retrieval
# ============================================================================

# Sample products data
sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99,
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99,
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99,
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99,
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99,
}

sample_products = [
    sample_product_1,
    sample_product_2,
    sample_product_3,
    sample_product_4,
    sample_product_5,
]


def find_product_by_id(product_id: int):
    """Find product by ID - pure function"""
    return next((p for p in sample_products if p["product_id"] == product_id), None)


def search_products(
    keyword: str, category: Optional[str] = None, limit: int = 10
) -> List[dict]:
    """Search products by keyword and optional category - pure function"""
    results = [p for p in sample_products if keyword.lower() in p["name"].lower()]

    if category:
        results = [p for p in results if p["category"] == category]

    return results[:limit]


@app.get("/products/search")
def products_search(keyword: str, category: Optional[str] = None, limit: int = 10):
    """Search endpoint - must be before /{product_id} to avoid conflict"""
    return search_products(keyword, category, limit)


@app.get("/product/{product_id}")
def get_product(product_id: int):
    """Get product by ID"""
    product = find_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ============================================================================
# TASK 5.1: Basic Cookie Authentication
# ============================================================================

# In-memory session storage for basic auth
sessions_basic = {}

DEMO_CREDENTIALS = {"user123": "password123"}


@app.post("/login")
def login(username: str, password: str, response: Response):
    """Login endpoint - sets session_token cookie"""
    if username not in DEMO_CREDENTIALS or DEMO_CREDENTIALS[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_token = str(uuid.uuid4())
    sessions_basic[session_token] = {"username": username, "created_at": time.time()}

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=300,  # 5 minutes
    )
    return {"message": "Login successful"}


@app.get("/user")
def get_user(session_token: Optional[str] = None):
    """Protected endpoint - requires valid session_token cookie"""
    if not session_token or session_token not in sessions_basic:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session = sessions_basic[session_token]
    return {
        "username": session["username"],
        "message": "User profile retrieved successfully",
    }


# ============================================================================
# TASK 5.2: Signed Cookie Authentication with itsdangerous
# ============================================================================

SECRET_KEY = "your-secret-key-change-in-production"
signer = TimestampSigner(SECRET_KEY)

sessions_signed = {}


def generate_signed_token(user_id: str) -> str:
    """Generate signed token with user_id"""
    token_value = f"{user_id}"
    signed = signer.sign(token_value)
    return signed.decode() if isinstance(signed, bytes) else signed


def verify_signed_token(token: str):
    """Verify signed token and extract user_id"""
    try:
        value = signer.unsign(token)
        return value.decode() if isinstance(value, bytes) else value
    except (SignatureExpired, BadSignature):
        return None


@app.post("/login_signed")
def login_signed(username: str, password: str, response: Response):
    """Login endpoint with signed cookie"""
    if username not in DEMO_CREDENTIALS or DEMO_CREDENTIALS[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = str(uuid.uuid4())
    signed_token = generate_signed_token(user_id)

    sessions_signed[user_id] = {"username": username, "created_at": time.time()}

    response.set_cookie(
        key="session_token", value=signed_token, httponly=True, max_age=300
    )
    return {"message": "Login successful"}


@app.get("/profile")
def get_profile(session_token: Optional[str] = None):
    """Protected endpoint - requires valid signed session_token cookie"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = verify_signed_token(session_token)
    if not user_id or user_id not in sessions_signed:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session = sessions_signed[user_id]
    return {
        "user_id": user_id,
        "username": session["username"],
        "message": "Profile retrieved successfully",
    }


# ============================================================================
# TASK 5.3: Dynamic Session with 3-5 minute refresh logic
# ============================================================================

sessions_dynamic = {}


def should_refresh_session(last_activity: float, current_time: float) -> bool:
    """Check if session should be refreshed (3-5 min rule)"""
    time_since_activity = current_time - last_activity
    # Refresh if >= 3 minutes and < 5 minutes
    return 180 <= time_since_activity < 300


def is_session_expired(last_activity: float, current_time: float) -> bool:
    """Check if session is expired (> 5 min)"""
    time_since_activity = current_time - last_activity
    return time_since_activity >= 300


@app.post("/login_dynamic")
def login_dynamic(username: str, password: str, response: Response):
    """Login endpoint with dynamic session"""
    if username not in DEMO_CREDENTIALS or DEMO_CREDENTIALS[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = str(uuid.uuid4())
    current_time = time.time()

    # Create token: user_id.timestamp.signature
    token_data = f"{user_id}.{int(current_time)}"
    signature = hmac.new(
        SECRET_KEY.encode(), token_data.encode(), hashlib.sha256
    ).hexdigest()[:16]

    signed_token = f"{token_data}.{signature}"

    sessions_dynamic[user_id] = {
        "username": username,
        "last_activity": current_time,
        "created_at": current_time,
    }

    response.set_cookie(
        key="session_token", value=signed_token, httponly=True, max_age=300
    )
    return {"message": "Login successful"}


def verify_dynamic_token(token: str) -> Optional[dict]:
    """Verify dynamic token and return user_id, timestamp"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        user_id, timestamp_str, signature = parts

        # Verify signature
        token_data = f"{user_id}.{timestamp_str}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(), token_data.encode(), hashlib.sha256
        ).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_signature):
            return None

        return {"user_id": user_id, "timestamp": int(timestamp_str)}
    except Exception:
        return None


@app.get("/profile_dynamic")
def get_profile_dynamic(
    session_token: Optional[str] = None, response: Response = Response()
):
    """Protected endpoint with dynamic session refresh"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session expired")

    token_data = verify_dynamic_token(session_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user_id = token_data["user_id"]
    token_timestamp = token_data["timestamp"]

    if user_id not in sessions_dynamic:
        raise HTTPException(status_code=401, detail="Session expired")

    current_time = time.time()
    session = sessions_dynamic[user_id]

    # Check if session is expired
    if is_session_expired(session["last_activity"], current_time):
        raise HTTPException(status_code=401, detail="Session expired")

    # Check if we should refresh the session
    if should_refresh_session(session["last_activity"], current_time):
        new_timestamp = int(current_time)
        new_token_data = f"{user_id}.{new_timestamp}"
        new_signature = hmac.new(
            SECRET_KEY.encode(), new_token_data.encode(), hashlib.sha256
        ).hexdigest()[:16]

        new_signed_token = f"{new_token_data}.{new_signature}"

        response.set_cookie(
            key="session_token", value=new_signed_token, httponly=True, max_age=300
        )
        session["last_activity"] = current_time

    return {
        "user_id": user_id,
        "username": session["username"],
        "message": "Profile retrieved successfully",
    }


# ============================================================================
# TASK 5.4: Headers Extraction
# ============================================================================


def validate_accept_language_format(accept_language: str) -> bool:
    """Validate Accept-Language header format"""
    if not accept_language:
        return False

    # Simple validation: should contain language codes like en-US or en;q=0.9
    parts = accept_language.split(",")
    for part in parts:
        lang_part = part.split(";")[0].strip()
        if not lang_part:
            return False
    return True


@app.get("/headers")
def get_headers(
    user_agent: Optional[str] = Header(None),
    accept_language: Optional[str] = Header(None),
):
    """Extract and return User-Agent and Accept-Language headers"""
    if not user_agent:
        raise HTTPException(status_code=400, detail="User-Agent header is required")

    if not accept_language:
        raise HTTPException(
            status_code=400, detail="Accept-Language header is required"
        )

    if not validate_accept_language_format(accept_language):
        raise HTTPException(status_code=400, detail="Accept-Language format is invalid")

    return {"User-Agent": user_agent, "Accept-Language": accept_language}


# ============================================================================
# TASK 5.5: CommonHeaders Model for Reusable Header Extraction
# ============================================================================


class CommonHeaders(BaseModel):
    """Reusable model for common headers with validation"""

    user_agent: str = Header(...)
    accept_language: str = Header(...)

    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v):
        if not validate_accept_language_format(v):
            raise ValueError("Invalid Accept-Language format")
        return v


@app.get("/info")
def get_info(headers: CommonHeaders, response: Response):
    """Get info endpoint with CommonHeaders model"""
    current_time = datetime.now().isoformat()

    response.headers["X-Server-Time"] = current_time

    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language,
        },
    }


@app.get("/headers_v2")
def get_headers_v2(headers: CommonHeaders):
    """Get headers endpoint with CommonHeaders model"""
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
