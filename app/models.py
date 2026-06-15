from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# CRITICAL IMPORT: Bring in Base from your database setup
from app.database import Base


class User(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "TradeManager"} # Explicitly tells the compiler: TradeManager.members

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(30), unique=True, index=True, nullable=False) # Explicit length
    username = Column(String(30), unique=True, index=True, nullable=False) # Explicit length
    firstName = Column(String(20), unique=False, index=True, nullable=True) # Explicit length
    lastName = Column(String(20), unique=False, index=False, nullable=True) # Explicit length
    password = Column(String(256), unique=False, index=False, nullable=False) # Explicit length
    google_id = Column(String(150), unique=True, index=True, nullable=True) # Explicit length
    roleId = Column(Integer, unique=False, index=False, nullable=False) # Explicit length
    active = Column(Boolean, default=True)
    createdBy = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    createdDate = Column(DateTime(timezone=True), server_default=func.now())
    modBy = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    modDate = Column(DateTime(timezone=True), server_default=func.now())

