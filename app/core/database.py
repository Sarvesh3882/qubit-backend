from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession  # SQLModel wrapper — has .exec()
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os
import re

# ── Ensure the database directory exists (needed on Render's persistent disk) ─
# Extract file path from sqlite URLs like "sqlite+aiosqlite:////data/qubit.db"
_db_url = settings.DATABASE_URL
_sqlite_path_match = re.match(r"sqlite\+aiosqlite:////(.+)", _db_url)
if _sqlite_path_match:
    _db_dir = os.path.dirname("/" + _sqlite_path_match.group(1))
    os.makedirs(_db_dir, exist_ok=True)
elif _db_url.startswith("sqlite+aiosqlite:///./") or _db_url.startswith("sqlite+aiosqlite:///"):
    # Relative path — directory is current working dir, always exists
    pass

engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Use SQLModel's AsyncSession so .exec(select(...)) works as expected
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
