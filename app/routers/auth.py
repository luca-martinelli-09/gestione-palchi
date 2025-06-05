from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from app.core.config import get_settings
from app.database.base import get_db
from app.models.auth import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.auth import User as UserSchema
from app.schemas.auth import UserCreate, UserUpdate

router = APIRouter()


# @router.post("/register", response_model=UserSchema)
# async def register_user(user: UserCreate, db: Session = Depends(get_db)):
#     # Check if user already exists
#     db_user = (
#         db.query(User)
#         .filter((User.username == user.username) | (User.email == user.email))
#         .first()
#     )

#     if db_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="⚠️ Nome utente o email già registrati",
#         )

#     # Create new user
#     hashed_password = get_password_hash(user.password)
#     db_user = User(
#         username=user.username,
#         email=user.email,
#         hashed_password=hashed_password,
#         is_active=user.is_active,
#         is_superuser=user.is_superuser,
#     )

#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)

#     return db_user


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="❌ Nome utente o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    update_data = user_update.dict(exclude_unset=True)

    # Handle password update separately
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user
