from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    country_code = Column(String, default="US")
    timezone = Column(String, default="UTC")
    culture_tags = Column(Text, default="[]")
    calendar_opt_in = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="owner")
    budgets = relationship("Budget", back_populates="owner")
    holiday_insights = relationship("HolidayInsight", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    type = Column(String, nullable=False)  # income or expense
    date = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    period = Column(String, nullable=False)  # monthly, weekly, yearly
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="budgets")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HolidayEvent(Base):
    __tablename__ = "holiday_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False, index=True)
    country_code = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    tags = Column(Text, default="[]")
    source = Column(String, default="curated")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_holiday_events_country_date", "country_code", "date"),
    )

class HolidayInsight(Base):
    __tablename__ = "holiday_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    holiday_event_id = Column(Integer, ForeignKey("holiday_events.id"), nullable=False, index=True)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    baseline_spend = Column(Float, default=0.0)
    holiday_spend = Column(Float, default=0.0)
    pct_change = Column(Float, default=0.0)
    confidence = Column(String, default="low")
    top_categories_json = Column(Text, default="[]")
    recommended_adjustment_pct = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    status = Column(String, default="ok")
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="holiday_insights")
    holiday_event = relationship("HolidayEvent")

    __table_args__ = (
        Index("ix_holiday_insights_user_event_window", "user_id", "holiday_event_id", "window_start"),
    )
