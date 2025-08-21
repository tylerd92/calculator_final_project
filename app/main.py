from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List
import logging

from fastapi import Body, FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

import uvicorn

from app.auth.dependencies import get_current_active_user
from app.core.config import get_settings
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate, CalculationReportResponse
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserUpdate
from app.database import Base, get_db, engine

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully!")
    yield
    logger.info("Application shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="API for managing calculations",
    version=settings.VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

# Home page route
@app.get("/", response_class=HTMLResponse, tags=["web"])
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Login page route
@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Registration page route
@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# User profile page route
@app.get("/profile", response_class=HTMLResponse, tags=["web"])
def user_profile_page(request: Request):
    return templates.TemplateResponse("user_profile.html", {"request": request})

@app.get("/report", response_class=HTMLResponse, tags=["web"])
def report_page(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})


# ------------------------------------------------------------------------------
# Health Endpoint
# ------------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}

# ------------------------------------------------------------------------------
# User Registration Endpoint
# ------------------------------------------------------------------------------
@app.post(
    "/auth/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    # Exclude confirm_password before passing data to User.register
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ------------------------------------------------------------------------------
# User Login Endpoints
# ------------------------------------------------------------------------------
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login with JSON payload"""
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_result["user"]
    db.commit()  # Commit the last_login update

    # Ensure expires_at is timezone-aware
    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )

@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with form data for Swagger UI"""
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }

# ------------------------------------------------------------------------------
# Dashboard Endpoints
# ------------------------------------------------------------------------------
# Dashboard page Route

@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])
def view_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse("view_calculation.html", {"request": request, "calc_id": calc_id})

@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])
def edit_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse("edit_calculation.html", {"request": request, "calc_id": calc_id})

# ------------------------------------------------------------------------------
# Calculations Endpoints (BREAD)
# ------------------------------------------------------------------------------
# Create (Add) Calculation – using CalculationBase so that 'user_id' from the client is ignored.
@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Compute and persist a calculation.
    
    The endpoint reads the calculation type and inputs from the request (ignoring any extra fields),
    computes the result using the appropriate operation, and assigns the authenticated user's ID.
    """
    try:
        # Create the calculation using the factory method.
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calculation.result = new_calculation.get_result()

        # Persist the calculation to the database.
        db.add(new_calculation)
        db.commit()
        db.refresh(new_calculation)
        return new_calculation

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Browse / List Calculations (for the current user)
@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    calculations = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    return calculations

# Read / Retrieve a Specific Calculation by ID
@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def get_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    return calculation

# Edit / Update a Calculation
@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()
    calculation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(calculation)
    return calculation

# Delete a Calculation
@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    db.delete(calculation)
    db.commit()
    return None

# Report on Calculations
@app.get("/calculations/report", response_model=CalculationReportResponse, tags=["calculations"])
def calculation_report(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    calculations = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    total = len(calculations)
    totals_by_type = {}

    for calc in calculations:
        if calc.type not in totals_by_type:
            totals_by_type[calc.type] = 0
        totals_by_type[calc.type] += 1
    addition_total = totals_by_type.get("addition", 0)
    subtraction_total = totals_by_type.get("subtraction", 0)
    multiplication_total = totals_by_type.get("multiplication", 0)
    division_total = totals_by_type.get("division", 0)
    power_total = totals_by_type.get("power", 0)

    return {
        "total_calculations": total,
        "addition_total": addition_total,
        "subtraction_total": subtraction_total,
        "multiplication_total": multiplication_total,
        "division_total": division_total,
        "power_total": power_total
    }

# ------------------------------------------------------------------------------
# User Profile Endpoints
# ------------------------------------------------------------------------------
@app.get("/user/profile", response_model=UserResponse, tags=["user"])
def get_user_profile(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/user/profile", response_model=UserResponse, tags=["user"])
def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    # Get the user
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for duplicate username/email if they're being updated
    if user_update.username and user_update.username != user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Update fields that are provided
    update_data = {}
    if user_update.username is not None:
        update_data["username"] = user_update.username
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.first_name is not None:
        update_data["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_data["last_name"] = user_update.last_name

    if update_data:
        user.update(**update_data)
        db.commit()
        db.refresh(user)
    
    return user

@app.post("/user/change-password", tags=["user"])
def change_password(
    password_data: dict = Body(...),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current password and new password are required")
    
    # Get the user
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not user.verify_password(current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")
    
    # Hash and update password
    hashed_password = User.hash_password(new_password)
    user.update(password=hashed_password)
    
    db.commit()
    
    return {"message": "Password changed successfully"}

# ------------------------------------------------------------------------------
# Main Block to Run the Server
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
