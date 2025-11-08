from fastapi import APIRouter, HTTPException, status, Response, Depends
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import hash_password, verify_password, create_access_token
from app.db.mongodb import get_db
from app.dependencies.auth import get_current_user
from app.config import COOKIE_NAME, COOKIE_HTTPONLY, COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_MAX_AGE
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    db = get_db()
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Create new user
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "created_at": datetime.utcnow()
    }

    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        email=created_user["email"],
        created_at=created_user["created_at"]
    )


@router.post("/login", response_model=Token)
async def login(user: UserLogin, response: Response):
    """Login user and set cookie"""
    db = get_db()
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(db_user["_id"])})

    # Set cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE
    )

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(response: Response, current_user: UserResponse = Depends(get_current_user)):
    """Refresh access token"""
    # Create new access token
    access_token = create_access_token(data={"sub": current_user.id})

    # Update cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current logged in user"""
    return current_user
