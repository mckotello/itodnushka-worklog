from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.security import hash_password, verify_password


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    session.add(user)

    await session.commit()
    await session.refresh(user)

    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    user_data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
    )