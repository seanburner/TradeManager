## ###################################################################################################################
##  Program :   TradeManager
##  Author  :   Sean Burner
##  Detail  :   Web app to manage multiple users/multiple accounts for trading 
##  Install :   
##  Example :
##  Setup   :
##              python3 -m venv venv
##              source venv/bin/activate
##              pip install fastapi uvicorn jinja2 sqlalchemy authlib itsdangerous python-multipart
##              pip install "passlib[bcrypt]" pyjwt  pydantic_settings httpx[http2]
##
##              uvicorn main:app --reload
##  Notes   :   https://docs.python.org/3/tutorial/classes.html
## #############################################################################
import os
import jwt  # Needed to decode the cookie token inside your dashboard route
import logging
import calendar
import httpx

import yfinance as yf

from pathlib                import Path
from datetime               import datetime, timezone
from sqlalchemy.orm         import Session

from fastapi                import FastAPI, Request, HTTPException, Depends 
from fastapi.staticfiles    import StaticFiles
from fastapi.responses      import HTMLResponse, RedirectResponse
from fastapi.templating     import Jinja2Templates
from fastapi.staticfiles    import StaticFiles

from app                    import models
from app.routers            import auth_google, auth_local
from app.database           import engine, get_db
from app.config             import settings

#GLOBAL VARIABLE
Ticker_Map = {
        "SPY": "SPY",
        "SPX": "^GSPC",   # Google Finance uses .INX for the S&P 500 Index
        "ESM26": "ESM26.CME"  # Continuous front-month proxy
    }




"""
import sys
from importlib.metadata import version, PackageNotFoundError

for module_name in sorted(sys.modules.keys()):
    # Filter out sub-modules (e.g., 'os.path') to check the main package
    main_package = module_name.split('.')[0]
    try:
        print(f"{main_package}: {version(main_package)}")
    except PackageNotFoundError:
        # Standard library modules or local project files won't have a pip version
        pass
exit
"""
# Automatically create the database tables in MariaDB if they don't exist
#models.Base.metadata.create_all(bind=engine)

# Create the FastAPI instance
app = FastAPI(title="Unified Auth App")

app.mount("/static", StaticFiles(directory="static"), name="static")

# CRITICAL: This links the file paths together
app.include_router(auth_local.router)
app.include_router(auth_google.router)
# Setup basic logging to see exactly why it's failing in the console
logger = logging.getLogger("uvicorn.error")
templates = Jinja2Templates(directory="templates")

# Get the absolute path of the current directory to ensure Jinja finds the templates folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))



# Catch-all route for the root domain
@app.get("/")
async def root():
    """Redirects root traffic to the login page so you don't get a 404."""
    return RedirectResponse(url="/login")



@app.get("/logout")
def logout(response: RedirectResponse):
    """
    Clears the authentication token cookie and redirects the user safely 
    back to the login framework landing gate.
    """
    # Create a redirect response back to your local login page
    response = RedirectResponse(url="/login", status_code=303)
    
    # Delete the JWT/session cookie completely
    # Change "access_token" to match the exact cookie key name you used in auth_local/auth_google
    response.delete_cookie(key="access_token", path="/")
    
    return response

# The unified login page endpoint
@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """Renders the unified login page."""
    return templates.TemplateResponse(request=request, name="login.html")




def CheckToken( request: Request, pageName : str,db: Session = Depends(get_db)) -> (int , object ) :
    """
        Check if the token is good , if not redirect , this is reuseable functionality
        PARAMETERS :
                        request  [Request] - request session of page
                        pageName [ str ]   - name of page called from
                        db       [ Session] - connection to database  
        RETURNS    :
                        int - id for the current user 
    """
    user_id = -1 
    member  = None 
    # 1. Grab the raw cookie
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        logger.warning(f"{pageName} access rejected: No access_token cookie found.")
        return RedirectResponse(url="/login")
    
        
    try:
        # 2. CRITICAL: Clean up the "Bearer " string if your auth router added it
        if token_cookie.startswith("Bearer "):
            token = token_cookie.replace("Bearer ", "", 1)
        else:
            token = token_cookie
        
        # 3. Decode payload against your environment's SECRET_KEY
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.warning(f"{pageName} access rejected: JWT payload missing 'sub' claim.")
            raise HTTPException(status_code=401, detail="Invalid session token payload.")
        
        #4. Get the member information based on user_id 
        member = db.query(models.User).filter(models.User.id == user_id).first()
        if not member:
            logger.warning(f"{pageName} access rejected: User ID {user_id} not found in database.")
            raise HTTPException(status_code=401, detail=f"User profile mismatch. {member}")
    except jwt.ExpiredSignatureError:
        #logger.warning("Dashboard access rejected: JWT token has expired.")
        #raise HTTPException(status_code=401, detail="Session expired.")
        logger.warning(f"{pageName}  access rejected: JWT token has expired")        
    except jwt.PyJWTError as e:
        logger.warning(f"{pageName}  access rejected: JWT decoding failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid session verification.")
    
    
    return user_id, member


@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    user_id     = -1
    member      = None
    pageName    = "Dashboard"
    
    user_id , member = CheckToken( request = request, pageName=pageName, db=db) 
    if int(user_id) < 0 :
        return RedirectResponse(url="/login")


    # 1. Get current date context
    now = datetime.now()
    year = now.year
    month = now.month
    
    # 2. Get calendar structure: matrix of weeks (0 represents days outside this month)
    # Example: [[0, 0, 1, 2, 3, 4, 5], [6, 7, ...]]
    cal = calendar.Calendar(firstweekday=6) # 6 = Sunday start
    month_days = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]

    # Mock Data: In the future, you'll query your database for trades 
    # grouped by day and pass actual daily PnL values down here!
    mock_pnl = {
        3: 150.00,   # Green Day
        4: -75.50,   # Red Day
        9: 225.00,   # Combined Iron Condor win
        10: 0.00     # Flat / No trades
    }

    # 3. Return template with full time context
    return templates.TemplateResponse(
        request = request,          # Pass it explicitly as a keyword argument
        name    = f"{pageName.lower()}.html",    # Pass the name explicitly
        context = {
            "request"       : request,
            "user"          : member,
            "month_days"    : month_days,
            "month_name"    : month_name,
            "year"          : year,
            "current_day"   : now.day,
            "pnl_data"      : mock_pnl
        }
    )


@app.get("/trade", response_class=HTMLResponse)
async def trade_room(request: Request, db: Session = Depends(get_db)):
    user_id         = "-1"
    member          = None
    pageName        = "Trade"
    date_format     = "%Y-%m-%d %H:%M:%S"
    
    user_id , member = CheckToken( request = request, pageName= pageName, db=db)    
    if int(user_id) < 0 :
        return RedirectResponse(url="/login")
        
    
    # Define variables for selectors
    assets      = ["SPY", "SPX", "ESM26"] # Map ESM26 to TradingView futures symbology
    strategies  = ["Scalp", "Iron Condor", "Butterfly", "Call Spread", "Put Spread"]
    tradeLog    = [["adf",(datetime.now(timezone.utc)).strftime(date_format),"Scalp","SPY","742","100.00","Completed"],
                   ["bdf",(datetime.now(timezone.utc)).strftime(date_format),"Scalp","SPY","742","100.00","Completed"],
                   ["cdf",(datetime.now(timezone.utc)).strftime(date_format),"Put Spread","SPX","7450/7435","325.00","Pending"],
                   ["ddf",(datetime.now(timezone.utc)).strftime(date_format),"Call Spread","SPX","7550/7565","225.00","Pending"] ]

    return templates.TemplateResponse(
        request = request,
        name    = f"{pageName.lower()}.html",
        context = {
            "user": member,
            "assets": assets,
            "strategies": strategies,
            "tradeLog" : tradeLog
        }
    )

@app.get("/profile", response_class=HTMLResponse)
async def user_profile(request: Request, db: Session = Depends(get_db)):
    user_id         = "-1"
    member          = None
    fileExt         =".png"
    dirPath         = "static/img/profiles"
    pageName        = "Profile"
    profilePix      = { f.stem:f  for f in Path(dirPath).iterdir()  if f.suffix ==fileExt }
    profilePixExt   = { 'Default': 'https://via.placeholder.com/40' }
    
    # Verify auth/token checks using your existing custom pipeline layout
    user_id, member = CheckToken(request=request, pageName=pageName, db=db) 
    if int(user_id) < 0:
        return RedirectResponse(url="/login")

    profilePix.update( profilePixExt)

    return templates.TemplateResponse(
        request = request,
        name    = f"{pageName.lower()}.html",
        context = {            
            "user"          : member,
            "profile_pix"   : profilePix
        },
    )



@app.get("/user_settings", response_class=HTMLResponse)
async def read_settings(request: Request, db: Session = Depends(get_db)):
    user_id         = "-1"
    member          = None

    # Verify auth/token checks using your existing custom pipeline layout
    user_id, member = CheckToken(request=request, pageName="User_Settings", db=db) 
    if int(user_id) < 0:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        request=request,
        name="user_settings.html",
        context={            
            "user": member
        },
    )


@app.get("/api/quote/{symbol}")
async def get_spot_price(symbol: str):
    """
    High-reliability, non-throttled spot pricing engine pulling from open web feeds.
    Completely bypasses Yahoo's 429 rate limits.
    """
    #ticker_map = {
    #    "SPY": "SPY",
    #    "SPX": "^GSPC",   # Google Finance uses .INX for the S&P 500 Index
    #    "ESM26": "ESM26.CME"  # Continuous front-month proxy
    #}
    
    target_ticker = Ticker_Map.get(symbol.upper(), symbol)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(http2=True) as client:        
        #YFINANCE        
        # Create a Ticker object for SPY
        yfAsset = yf.Ticker(target_ticker)

        # Get live current price using fast_info
        print("Current Price:", yfAsset.fast_info['lastPrice'], " : " , yfAsset.info)
        current_spot = yfAsset.fast_info['lastPrice']
        return {"symbol": symbol, "spot_price": float(current_spot)}
        
        # For Indexes and general equities, use Google's unthrottled public feed        
        if target_ticker in ["SPY", ".INX"]:
            try:
                url = f"https://www.google.com/finance/quote/{target_ticker}:NYSEARCA" if target_ticker == "SPY" else f"https://www.google.com/finance/quote/{target_ticker}:INDEXSP"
                response = await client.get(url, headers=headers, timeout=4.0)
                
                if response.status_code == 200:
                    text = response.text
                    marker = 'data-last-price="'
                    if marker in text:
                        start = text.find(marker) + len(marker)
                        end = text.find('"', start)
                        current_spot = text[start:end]
                        return {"symbol": symbol, "spot_price": float(current_spot)}
            except Exception:
                pass 

        # Backup Strategy: Nasdaq public query framework
        try:
            nasdaq_symbol = "SPY" if symbol.upper() == "SPY" else ("SPX" if symbol.upper() == "SPX" else "E-MINI")
            if symbol.upper() == "ESM26":
                url = "https://api.nasdaq.com/api/quote/ESM26/info?assetclass=futures"
            else:
                url = f"https://api.nasdaq.com/api/quote/{nasdaq_symbol}/info?assetclass=stocks" if nasdaq_symbol == "SPY" else f"https://api.nasdaq.com/api/quote/{nasdaq_symbol}/info?assetclass=index"
                
            res = await client.get(url, headers=headers, timeout=4.0)
            if res.status_code == 200:
                json_data = res.json()
                data_payload = json_data.get("data", {})
                if data_payload:
                    price_str = data_payload.get("primaryData", {}).get("lastSalePrice", "")
                    clean_price = price_str.replace("$", "").replace(",", "").strip()
                    if clean_price:
                        return {"symbol": symbol, "spot_price": float(clean_price)}
        except Exception:
            pass

        # Static Hard Fallback if remote networks time out
        fallback_prices = {"SPY": 535.20, "SPX": 5430.50, "ESM26": 5485.25}
        return {"symbol": symbol, "spot_price": fallback_prices.get(symbol.upper(), 100.00), "fallback": True}


@app.get("/api/option_chain/{symbol}")
async def get_option_chain(symbol: str):
    """
    Obtain the 0dte option chain for the symbol provided     
    """
    ticker_map = {
        "SPY": "SPY",
        "SPX": "^SPX",   # Google Finance uses .INX for the S&P 500 Index
        "ESM26": "ESM26.CME"  # Continuous front-month proxy
    }
    
    target_ticker = ticker_map.get(symbol.upper(), symbol)    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(http2=True) as client:                
        try:
            #1. Create a Ticker object for SPY
            yfAsset = yf.Ticker("^SPX")#target_ticker)
            print(yfAsset.options)

            # 2. View available expiration dates
            print( f"[DEBUG] {yfAsset }")
            #if not yfAssets.options:
            #    return {"symbol": symbol, "spot_price": float( 0.00), "fallback": True}  # Change for the option chain
            
            print("Available Expirations:", yfAsset.options)

            # 3. Select a specific expiration date (e.g., the first available one)
            expiry_date = yfAsset.options[0]

            # 4. Fetch the option chain for that date
            chain = yfAsset.option_chain(expiry_date)

            # Access the Calls and Puts DataFrames
            calls_df = chain.calls
            puts_df = chain.puts

            # Display the first few rows
            print("Calls:")
            print(calls_df.head())

            print("\nPuts:")
            print(puts_df.head())
            return {"symbol": symbol, "spot_price": float( 0.00)}  # Change for the option chain
        except:
            print(f"[ERROR] Did not get the option chain ")
        
        return {"symbol": symbol, "option_chain": "", "fallback": True}


    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
