from sqlalchemy         import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm     import relationship
from sqlalchemy.sql     import func

# CRITICAL IMPORT: Bring in Base from your database setup
from app.database import Base


class User(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "TradeManager"} # Explicitly tells the compiler: TradeManager.members

    id          = Column(Integer, primary_key=True, index=True)
    email       = Column(String(30), unique=True, index=True, nullable=False) # Explicit length
    userName    = Column(String(30), unique=True, index=True, nullable=False) # Explicit length
    firstName   = Column(String(20), unique=False, index=True, nullable=True) # Explicit length
    lastName    = Column(String(20), unique=False, index=False, nullable=True) # Explicit length
    password    = Column(String(256), unique=False, index=False, nullable=False) # Explicit length
    google_id   = Column(String(150), unique=True, index=True, nullable=True) # Explicit length
    roleId      = Column(Integer, unique=False, index=False, nullable=False) # Explicit length
    pix         = Column(String(200), unique=False, index=False, nullable=True) 
    active      = Column(Boolean, default=True)
    createdBy   = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    createdDate = Column(DateTime(timezone=True), server_default=func.now())
    modBy       = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    modDate     = Column(DateTime(timezone=True), server_default=func.now())


class Accounts(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "TradeManager"} # Explicitly tells the compiler: TradeManager.accounts
    id              = Column(Integer, primary_key=True, index=True)
    member_id       = Column(Integer, unique=False , index=True)    
    accountTypeId   = Column(Integer, unique=False, index=True) 
    client_id       = Column(String(200), unique=True, index=True, nullable=True)
    client_secret   = Column(String(200), unique=True, index=True, nullable=True)
    account_id      = Column(Integer, unique=False, index=True)
    active          = Column(Boolean, default=True)
    createdBy       = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    createdDate     = Column(DateTime(timezone=True), server_default=func.now())
    modBy           = Column(String(20), unique=False, index=False, nullable=False) # Explicit length
    modDate         = Column(DateTime(timezone=True), server_default=func.now())
