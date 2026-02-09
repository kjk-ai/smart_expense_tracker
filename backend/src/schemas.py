from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, date
from typing import List, Optional, Any
import json

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    culture_tags: List[str] = []
    calendar_opt_in: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

    @validator("culture_tags", pre=True)
    def parse_culture_tags(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        return []

class UserPreferencesUpdate(BaseModel):
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    culture_tags: Optional[List[str]] = None
    calendar_opt_in: Optional[bool] = None

class TransactionBase(BaseModel):
    description: str
    amount: float
    category: str
    type: str
    date: datetime

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BudgetBase(BaseModel):
    category: str
    amount: float
    period: str

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TransactionStats(BaseModel):
    total_income: float
    total_expenses: float
    net_income: float
    transactions_count: int
    average_transaction_amount: float
    category_breakdown: dict
    monthly_summary: dict

    class Config:
        orm_mode = True

class HolidayEventResponse(BaseModel):
    id: int
    name: str
    date: date
    country_code: str
    type: str
    tags: List[str] = []
    source: str

    class Config:
        orm_mode = True

    @validator("tags", pre=True)
    def parse_tags(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        return []

class HolidayInsightCategory(BaseModel):
    category: str
    delta: float

class HolidayInsightResponse(BaseModel):
    holiday_event_id: int
    holiday_name: str
    holiday_date: date
    expected_change_pct: float
    recommended_adjustment_pct: float
    confidence: str
    explanation: str
    top_categories: List[HolidayInsightCategory]
    status: str
