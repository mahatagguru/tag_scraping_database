from contextlib import contextmanager
import os
from typing import Generator, Iterator

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Always load .env from the project root
project_root = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get individual database configuration variables
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'tag_scraper')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

# Construct PostgreSQL DSN
if POSTGRES_PASSWORD:
    POSTGRES_DSN = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
else:
    POSTGRES_DSN = (
        f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

print("Database Configuration:")
print(f"  Host: {POSTGRES_HOST}")
print(f"  Port: {POSTGRES_PORT}")
print(f"  Database: {POSTGRES_DB}")
print(f"  User: {POSTGRES_USER}")
print(f"  DSN: {POSTGRES_DSN}")

# Create engine with fallback to SQLite if PostgreSQL is not available
try:
    engine = create_engine(POSTGRES_DSN, echo=False, future=True)
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ PostgreSQL connection successful")
except Exception as e:
    print(f"⚠️  PostgreSQL connection failed: {e}")
    print("🔄 Falling back to SQLite database")
    
    # Fallback to SQLite
    sqlite_path = os.path.join(project_root, 'tag_scraper_local.db')
    sqlite_dsn = f"sqlite:///{sqlite_path}"
    engine = create_engine(sqlite_dsn, echo=False, future=True)
    print(f"✅ SQLite database created at: {sqlite_path}")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session_context() -> Iterator[Session]:
    """Get a database session as a context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_connection() -> Engine:
    """Get a database connection (for backward compatibility)."""
    return engine