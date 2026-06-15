from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Initialize the MariaDB connection engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Automatically tests/recovers stale connections
    pool_size=5,         # Base connection pool size
    max_overflow=10      # Extra burst connections allowed
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Context manager wrapper to yield database connections safely."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
