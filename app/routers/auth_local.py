from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, security

router = APIRouter(prefix="/auth/local", tags=["Local Auth"])

@router.post("/login")
async def local_login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Handles standard form submissions from the login page.
    form_data.username will contain whatever string was passed into the input field.
    """
    # 1. Look up the identity provider layer for local credentials
    member = db.query(models.User).filter(
    or_(
        models.User.email == form_data.username,
        models.User.username == form_data.username
    )
    ).first()

    # Security baseline: Avoid indicating whether the user exists or if just the password was wrong
    if not member or not member.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check the password using our security helpers
    if not security.verify_password(form_data.password, member.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Cleaned Up: Check account status directly on the object we just retrieved
    if not member.active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    # 4. Mint our app's session JWT token
    access_token = security.create_access_token(data={"sub": str(member.id)})

    from fastapi.responses import RedirectResponse
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response
