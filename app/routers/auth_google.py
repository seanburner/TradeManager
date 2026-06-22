import httpx

from datetime           import datetime
from fastapi            import APIRouter, Depends, HTTPException, status
from fastapi.responses  import RedirectResponse
from sqlalchemy         import or_
from sqlalchemy.orm     import Session
from app                import models, security
from app.config         import settings
from app.database       import get_db

router = APIRouter(prefix="/auth/google", tags=["Google Auth"])

@router.get("/login")
async def google_login():
    """Redirects the user to Google's secure OAuth2 sign-in screen."""
    google_provider_cfg = "https://accounts.google.com/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        res = await client.get(google_provider_cfg)
        authorization_endpoint = res.json()["authorization_endpoint"]

    # Construct the authorization redirect URL
    request_uri = (
        f"{authorization_endpoint}?"
        f"response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=request_uri)


@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Receives the authorization code from Google, verifies it, and signs the user in."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing from Google redirect.")

    # 1. Exchange the authorization code for an identity token
    google_provider_cfg = "https://accounts.google.com/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        cfg_res = await client.get(google_provider_cfg)
        token_endpoint = cfg_res.json()["token_endpoint"]
        userinfo_endpoint = cfg_res.json()["userinfo_endpoint"]

        token_res = await client.post(
            token_endpoint,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")

        # 2. Fetch the user's verified profile data using the access token
        userinfo_res = await client.get(
            userinfo_endpoint, 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = userinfo_res.json()

    # Google profile attributes
    google_id = str(user_info.get("sub"))
    email = user_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Google account lacks a valid email address.")

    # 3. Match against your read-only database
    # Look for an explicit google_id match first, fallback to checking the email address
    member = db.query(models.User).filter(
        or_(
            models.User.google_id == google_id,
            models.User.email == email
        )
    ).first()

    if not member:
        # Optional: If you want to automatically CREATE an account for new users now:
         member = models.User(email=email, google_id=google_id,
                              active=True,createdBy='viewer',modBy='viewer',createdDate=datetime.now(),modDate=datetime.now())
         db.add(member)
         db.commit()
         db.refresh(member)
        # Since the 'viewer' user cannot create accounts, reject unknown identities
        #raise HTTPException(
        #    status_code=status.HTTP_401_UNAUTHORIZED,
        #    detail="Your Google identity is not registered on this platform.",
        #)

    # 4. If the user matched via email but doesn't have the google_id column stamped yet,
    # note that your 'viewer' account cannot write this update back directly.
    if not member.google_id:
        try:
            member.google_id = google_id
            member.modBy     ='viewer'
            member.modDate   = datetime.now()
            db.commit()
            db.refresh(member)
        except Exception as e:
            db.rollback()
            # Log the error but potentially allow the login to proceed if you don't want to block them,
            # or raise a 500 if DB consistency is critical right here.
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to bind Google identity to local account configuration: {str(e)}"
            )

    if not member.active:
        raise HTTPException(status_code=400, detail="Inactive account status.")

    # 5. Issue the standard TradeManager application session token
    app_token = security.create_access_token(data={"sub": str(member.id)})

    # Redirect your user to the dashboard or internal landing page with their token
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {app_token}", httponly=True)
    return response
