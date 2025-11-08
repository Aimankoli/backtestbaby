from fastapi import Depends, HTTPException, status, Request
from app.utils.auth import verify_token
from app.db.mongodb import get_db
from app.models.user import UserResponse
from app.config import COOKIE_NAME
from bson import ObjectId
from datetime import datetime


async def get_current_user(request: Request) -> UserResponse:
    """
    Dependency to get the current authenticated user from cookie
    Use this in protected routes like: current_user: UserResponse = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Get token from cookie
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise credentials_exception

    # Verify token
    token_data = verify_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    # Get user from database
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception

    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"]
    )
