from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Optional
import logging
import sys
import bcrypt

from . import models, schemas, crud
from .database import SessionLocal, engine
from .core.security import create_access_token, verify_password, get_password_hash
from .core.config import settings
from .db_migrations import ensure_schema
from .holiday_seed import seed_holidays_missing

# Setup logging
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0")

@app.on_event("startup")
def log_runtime_env():
    logger.info("Python executable: %s", sys.executable)
    logger.info("bcrypt version: %s", getattr(bcrypt, "__version__", "unknown"))
    ensure_schema()
    with SessionLocal() as db:
        seed_holidays_missing(db)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to Expense Tracker API"}

# Authentication Routes
@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Validate password length (bcrypt has a 72 byte limit)
        if len(user.password.encode('utf-8')) > 72:
            raise HTTPException(status_code=400, detail="Password is too long. Maximum 72 bytes allowed.")
        
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user.password)
        db_user = crud.create_user(db=db, user=user, hashed_password=hashed_password)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = crud.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return user

@app.patch("/api/users/me/preferences", response_model=schemas.UserResponse)
def update_user_preferences(
    prefs: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return crud.update_user_preferences(db, user, prefs)

@app.get("/api/holidays", response_model=List[schemas.HolidayEventResponse])
def read_holidays(
    country: Optional[str] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    country_code = country or user.country_code or "US"
    start = from_date or date.today().replace(day=1)
    end = to_date or (start + timedelta(days=31))
    return crud.get_holidays(db, country_code, start, end)

@app.get("/api/insights/holidays", response_model=List[schemas.HolidayInsightResponse])
def read_holiday_insights(
    window_days: int = 30,
    force: bool = False,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.calendar_opt_in is False:
        return []
    return crud.get_holiday_insights(db, user, window_days=window_days, force=force)

# Transaction Routes
@app.get("/api/transactions", response_model=List[schemas.TransactionResponse])
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    return crud.get_transactions(db, user_id=user.id, skip=skip, limit=limit)

@app.post("/api/transactions", response_model=schemas.TransactionResponse)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    return crud.create_transaction(db=db, transaction=transaction, user_id=user.id)

@app.get("/api/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None or db_transaction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@app.put("/api/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None or db_transaction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return crud.update_transaction(db=db, transaction_id=transaction_id, transaction=transaction)

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None or db_transaction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    crud.delete_transaction(db=db, transaction_id=transaction_id)
    return {"message": "Transaction deleted successfully"}

# Budget Routes
@app.get("/api/budgets", response_model=List[schemas.BudgetResponse])
def read_budgets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    return crud.get_budgets(db, user_id=user.id, skip=skip, limit=limit)

@app.post("/api/budgets", response_model=schemas.BudgetResponse)
def create_budget(
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    return crud.create_budget(db=db, budget=budget, user_id=user.id)

@app.get("/api/budgets/{budget_id}", response_model=schemas.BudgetResponse)
def read_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_budget = crud.get_budget(db, budget_id=budget_id)
    if db_budget is None or db_budget.user_id != user.id:
        raise HTTPException(status_code=404, detail="Budget not found")
    return db_budget

@app.put("/api/budgets/{budget_id}", response_model=schemas.BudgetResponse)
def update_budget(
    budget_id: int,
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_budget = crud.get_budget(db, budget_id=budget_id)
    if db_budget is None or db_budget.user_id != user.id:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return crud.update_budget(db=db, budget_id=budget_id, budget=budget)

@app.delete("/api/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    db_budget = crud.get_budget(db, budget_id=budget_id)
    if db_budget is None or db_budget.user_id != user.id:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    crud.delete_budget(db=db, budget_id=budget_id)
    return {"message": "Budget deleted successfully"}

# Statistics Routes
@app.get("/api/stats/transactions", response_model=schemas.TransactionStats)
def get_transaction_stats(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = crud.get_current_user(token, db)
    return crud.get_transaction_stats(db, user_id=user.id)
