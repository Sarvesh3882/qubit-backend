from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User, UserCreate, UserRead, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = decode_access_token(credentials.credentials)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await session.exec(select(User).where(User.email == email))
    user = result.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register", response_model=dict, status_code=201)
async def register(data: UserCreate, session: AsyncSession = Depends(get_session)):
    # Check duplicates
    existing = await session.exec(select(User).where(User.email == data.email))
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_u = await session.exec(select(User).where(User.username == data.username))
    if existing_u.first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer", "user": UserRead.model_validate(user).model_dump()}


@router.post("/login", response_model=dict)
async def login(data: UserLogin, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == data.email))
    user = result.first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer", "user": UserRead.model_validate(user).model_dump()}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
