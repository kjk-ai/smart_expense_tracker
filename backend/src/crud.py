from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
import json

from . import models, schemas
from .core.security import verify_password, decode_token
from .core.config import settings
from .holiday_provider import fetch_calendarific_holidays

# User CRUD operations
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Get a user by email address
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str) -> models.User:
    """
    Create a new user
    """
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_current_user(token: str, db: Session):
    """
    Get the current authenticated user from token
    """
    payload = decode_token(token)
    email: str = payload.get("sub")
    if email is None:
        return None
    
    user = get_user_by_email(db, email=email)
    return user

def update_user_preferences(db: Session, user: models.User, prefs: schemas.UserPreferencesUpdate) -> models.User:
    if prefs.country_code is not None:
        user.country_code = prefs.country_code
    if prefs.timezone is not None:
        user.timezone = prefs.timezone
    if prefs.culture_tags is not None:
        user.culture_tags = json.dumps(prefs.culture_tags)
    if prefs.calendar_opt_in is not None:
        user.calendar_opt_in = prefs.calendar_opt_in
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

# Transaction CRUD operations
def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Transaction]:
    """
    Get all transactions for a specific user
    """
    return db.query(models.Transaction)\
        .filter(models.Transaction.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_transaction(db: Session, transaction_id: int) -> Optional[models.Transaction]:
    """
    Get a specific transaction by ID
    """
    return db.query(models.Transaction)\
        .filter(models.Transaction.id == transaction_id)\
        .first()

def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int) -> models.Transaction:
    """
    Create a new transaction
    """
    db_transaction = models.Transaction(
        **transaction.dict(),
        user_id=user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, transaction_id: int, transaction: schemas.TransactionCreate) -> models.Transaction:
    """
    Update an existing transaction
    """
    db_transaction = get_transaction(db, transaction_id=transaction_id)
    if db_transaction:
        for key, value in transaction.dict().items():
            setattr(db_transaction, key, value)
        db_transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int):
    """
    Delete a transaction
    """
    db_transaction = get_transaction(db, transaction_id=transaction_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()

# Budget CRUD operations
def get_budgets(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Budget]:
    """
    Get all budgets for a specific user
    """
    return db.query(models.Budget)\
        .filter(models.Budget.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_budget(db: Session, budget_id: int) -> Optional[models.Budget]:
    """
    Get a specific budget by ID
    """
    return db.query(models.Budget)\
        .filter(models.Budget.id == budget_id)\
        .first()

def create_budget(db: Session, budget: schemas.BudgetCreate, user_id: int) -> models.Budget:
    """
    Create a new budget
    """
    db_budget = models.Budget(
        **budget.dict(),
        user_id=user_id
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def update_budget(db: Session, budget_id: int, budget: schemas.BudgetCreate) -> models.Budget:
    """
    Update an existing budget
    """
    db_budget = get_budget(db, budget_id=budget_id)
    if db_budget:
        for key, value in budget.dict().items():
            setattr(db_budget, key, value)
        db_budget.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_budget)
    return db_budget

def delete_budget(db: Session, budget_id: int):
    """
    Delete a budget
    """
    db_budget = get_budget(db, budget_id=budget_id)
    if db_budget:
        db.delete(db_budget)
        db.commit()

# Statistics operations
def get_transaction_stats(db: Session, user_id: int) -> dict:
    """
    Get statistics about transactions
    """
    transactions = get_transactions(db, user_id=user_id)
    
    # Calculate totals
    total_income = 0.0
    total_expenses = 0.0
    category_breakdown = {}
    
    for transaction in transactions:
        if transaction.type == "income":
            total_income += transaction.amount
        else:
            total_expenses += transaction.amount
            if transaction.category not in category_breakdown:
                category_breakdown[transaction.category] = 0.0
            category_breakdown[transaction.category] += transaction.amount
    
    net_income = total_income - total_expenses
    transactions_count = len(transactions)
    average_transaction_amount = net_income / transactions_count if transactions_count > 0 else 0.0
    
    # Calculate monthly summary
    monthly_summary = {}
    for transaction in transactions:
        month_key = transaction.date.strftime("%Y-%m")
        if month_key not in monthly_summary:
            monthly_summary[month_key] = {
                "income": 0.0,
                "expenses": 0.0
            }
        if transaction.type == "income":
            monthly_summary[month_key]["income"] += transaction.amount
        else:
            monthly_summary[month_key]["expenses"] += transaction.amount
    
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_income": round(net_income, 2),
        "transactions_count": transactions_count,
        "average_transaction_amount": round(average_transaction_amount, 2),
        "category_breakdown": {category: round(amount, 2) for category, amount in category_breakdown.items()},
        "monthly_summary": monthly_summary
    }

def get_holidays(db: Session, country_code: str, start_date: date, end_date: date) -> List[models.HolidayEvent]:
    ensure_holidays_for_range(db, country_code, start_date, end_date)
    return db.query(models.HolidayEvent).filter(
        models.HolidayEvent.country_code == country_code,
        models.HolidayEvent.date >= start_date,
        models.HolidayEvent.date <= end_date
    ).order_by(models.HolidayEvent.date.asc()).all()

def _date_range_to_datetimes(start_date: date, end_date: date):
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    return start_dt, end_dt

def _sum_expenses(db: Session, user_id: int, start_date: date, end_date: date) -> float:
    start_dt, end_dt = _date_range_to_datetimes(start_date, end_date)
    total = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == "expense",
        models.Transaction.date >= start_dt,
        models.Transaction.date <= end_dt
    ).scalar()
    return float(total or 0.0)

def _sum_expenses_for_category(db: Session, user_id: int, category: str, start_date: date, end_date: date) -> float:
    start_dt, end_dt = _date_range_to_datetimes(start_date, end_date)
    total = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == "expense",
        models.Transaction.category == category,
        models.Transaction.date >= start_dt,
        models.Transaction.date <= end_dt
    ).scalar()
    return float(total or 0.0)

def _count_expense_transactions(db: Session, user_id: int, start_date: date, end_date: date) -> int:
    start_dt, end_dt = _date_range_to_datetimes(start_date, end_date)
    count = db.query(func.count(models.Transaction.id)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == "expense",
        models.Transaction.date >= start_dt,
        models.Transaction.date <= end_dt
    ).scalar()
    return int(count or 0)

def _sum_expenses_by_category(db: Session, user_id: int, start_date: date, end_date: date) -> Dict[str, float]:
    start_dt, end_dt = _date_range_to_datetimes(start_date, end_date)
    rows = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == "expense",
        models.Transaction.date >= start_dt,
        models.Transaction.date <= end_dt
    ).group_by(models.Transaction.category).all()
    return {row[0]: float(row[1] or 0.0) for row in rows}

def _get_month_range(target_date: date):
    start = date(target_date.year, target_date.month, 1)
    if target_date.month == 12:
        end = date(target_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
    return start, end

def _get_week_range(target_date: date):
    start = target_date - timedelta(days=target_date.weekday())
    end = start + timedelta(days=6)
    return start, end

def _compute_confidence(sample_count: int, pct_changes: List[float]) -> str:
    if sample_count >= 3:
        mean = sum(pct_changes) / sample_count
        variance = sum((x - mean) ** 2 for x in pct_changes) / sample_count
        if variance <= 0.1:
            return "high"
        return "medium"
    if sample_count >= 2:
        return "medium"
    return "low"

def get_holiday_insights(
    db: Session,
    user: models.User,
    window_days: int = 30,
    force: bool = False,
    lookback_years: int = 2
) -> List[Dict[str, Any]]:
    today = date.today()
    window_end = today + timedelta(days=window_days)
    country_code = user.country_code or "US"
    ensure_holidays_for_range(db, country_code, today, window_end)
    try:
        user_tags = json.loads(user.culture_tags or "[]")
    except json.JSONDecodeError:
        user_tags = []

    upcoming = db.query(models.HolidayEvent).filter(
        models.HolidayEvent.country_code == country_code,
        models.HolidayEvent.date >= today,
        models.HolidayEvent.date <= window_end
    ).order_by(models.HolidayEvent.date.asc()).all()

    if user_tags:
        filtered = []
        for event in upcoming:
            try:
                event_tags = json.loads(event.tags or "[]")
            except json.JSONDecodeError:
                event_tags = []
            if any(tag in event_tags for tag in user_tags):
                filtered.append(event)
        upcoming = filtered

    insights: List[Dict[str, Any]] = []
    for event in upcoming:
        window_start = event.date - timedelta(days=7)
        window_end = event.date + timedelta(days=2)

        cached = None
        if not force:
            cached = db.query(models.HolidayInsight).filter(
                models.HolidayInsight.user_id == user.id,
                models.HolidayInsight.holiday_event_id == event.id,
                models.HolidayInsight.window_start == window_start
            ).order_by(models.HolidayInsight.generated_at.desc()).first()
            if cached and cached.expires_at and cached.expires_at > datetime.utcnow():
                insights.append(_format_insight_response(event, cached))
                continue

        historical = db.query(models.HolidayEvent).filter(
            models.HolidayEvent.country_code == country_code,
            models.HolidayEvent.name == event.name,
            models.HolidayEvent.date < event.date,
            models.HolidayEvent.date >= event.date - timedelta(days=365 * lookback_years + 30)
        ).order_by(models.HolidayEvent.date.desc()).all()

        sample_spend = []
        sample_baseline = []
        sample_pct_changes = []
        category_deltas: Dict[str, float] = {}
        transaction_samples = 0

        for sample in historical:
            holiday_start = sample.date - timedelta(days=7)
            holiday_end = sample.date + timedelta(days=2)
            baseline_start = holiday_start - timedelta(days=28)
            baseline_end = holiday_end - timedelta(days=28)

            holiday_spend = _sum_expenses(db, user.id, holiday_start, holiday_end)
            baseline_spend = _sum_expenses(db, user.id, baseline_start, baseline_end)
            transaction_samples += _count_expense_transactions(db, user.id, holiday_start, holiday_end)

            if baseline_spend <= 0:
                continue

            holiday_categories = _sum_expenses_by_category(db, user.id, holiday_start, holiday_end)
            baseline_categories = _sum_expenses_by_category(db, user.id, baseline_start, baseline_end)

            for category, value in holiday_categories.items():
                delta = value - baseline_categories.get(category, 0.0)
                category_deltas[category] = category_deltas.get(category, 0.0) + delta

            pct_change = (holiday_spend - baseline_spend) / baseline_spend
            sample_spend.append(holiday_spend)
            sample_baseline.append(baseline_spend)
            sample_pct_changes.append(pct_change)

        sample_count = len(sample_spend)
        if sample_count < 2 or transaction_samples < 5:
            insight = _build_insufficient_insight(event, window_start, window_end, sample_count)
            _save_insight(db, user.id, event.id, insight)
            insights.append(insight)
            continue

        baseline_spend_avg = sum(sample_baseline) / sample_count
        holiday_spend_avg = sum(sample_spend) / sample_count
        pct_change_avg = (holiday_spend_avg - baseline_spend_avg) / baseline_spend_avg if baseline_spend_avg > 0 else 0.0
        confidence = _compute_confidence(sample_count, sample_pct_changes)

        averaged_deltas = {category: value / sample_count for category, value in category_deltas.items()}
        sorted_categories = sorted(averaged_deltas.items(), key=lambda x: x[1], reverse=True)
        top_categories = [
            {"category": name, "delta": round(value, 2)}
            for name, value in sorted_categories[:3]
            if value > 0
        ]

        recommended_adjustment_pct = 0.0
        budgets = db.query(models.Budget).filter(models.Budget.user_id == user.id).all()
        budget_map = {budget.category: budget for budget in budgets}
        for item in top_categories:
            budget = budget_map.get(item["category"])
            if not budget:
                continue
            if budget.period == "weekly":
                spend_start, spend_end = _get_week_range(today)
            else:
                spend_start, spend_end = _get_month_range(today)
            spent = _sum_expenses_for_category(db, user.id, item["category"], spend_start, spend_end)
            remaining = max(budget.amount - spent, 0.0)
            expected_delta = item["delta"]
            if expected_delta > remaining and expected_delta > 0:
                adjustment = ((expected_delta - remaining) / expected_delta) * 100
                recommended_adjustment_pct = max(recommended_adjustment_pct, adjustment)

        explanation = _build_explanation(event.name, sample_count, pct_change_avg, holiday_spend_avg - baseline_spend_avg, top_categories)

        insight = {
            "holiday_event_id": event.id,
            "holiday_name": event.name,
            "holiday_date": event.date,
            "expected_change_pct": round(pct_change_avg * 100, 1),
            "recommended_adjustment_pct": round(recommended_adjustment_pct, 1),
            "confidence": confidence,
            "explanation": explanation,
            "top_categories": top_categories,
            "status": "ok"
        }

        _save_insight(db, user.id, event.id, {
            **insight,
            "baseline_spend": baseline_spend_avg,
            "holiday_spend": holiday_spend_avg,
            "pct_change": pct_change_avg,
            "window_start": window_start,
            "window_end": window_end
        })
        insights.append(insight)

    return insights

def ensure_holidays_for_range(db: Session, country_code: str, start_date: date, end_date: date) -> int:
    if settings.HOLIDAY_API_PROVIDER != "calendarific":
        return 0
    if not settings.CALENDARIFIC_API_KEY:
        return 0

    inserted = 0
    for year in range(start_date.year, end_date.year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        existing_api = db.query(models.HolidayEvent).filter(
            models.HolidayEvent.country_code == country_code,
            models.HolidayEvent.source == "calendarific",
            models.HolidayEvent.date >= year_start,
            models.HolidayEvent.date <= year_end
        ).count()
        if existing_api > 0:
            continue
        fetched = fetch_calendarific_holidays(country_code, year)
        if not fetched:
            continue
        existing_keys = {
            (row[0], row[1], row[2])
            for row in db.query(
                models.HolidayEvent.name,
                models.HolidayEvent.date,
                models.HolidayEvent.country_code
            ).filter(
                models.HolidayEvent.country_code == country_code,
                models.HolidayEvent.date >= year_start,
                models.HolidayEvent.date <= year_end
            ).all()
        }
        records = []
        for item in fetched:
            key = (item["name"], item["date"], item["country_code"])
            if key in existing_keys:
                continue
            records.append(models.HolidayEvent(
                name=item["name"],
                date=item["date"],
                country_code=item["country_code"],
                type=item["type"],
                tags=json.dumps(item.get("tags", [])),
                source=item.get("source", "calendarific")
            ))
        if records:
            db.add_all(records)
            db.commit()
            inserted += len(records)
    return inserted

def _build_explanation(holiday_name: str, sample_count: int, pct_change: float, delta: float, top_categories: List[Dict[str, Any]]) -> str:
    change_pct = round(pct_change * 100, 1)
    change_sign = "+" if change_pct >= 0 else ""
    categories = ", ".join([item["category"] for item in top_categories]) or "your usual categories"
    return f"Based on your last {sample_count} {holiday_name} periods, spending changed {change_sign}{change_pct}% (~${abs(delta):.0f}), mostly in {categories}."

def _build_insufficient_insight(event: models.HolidayEvent, window_start: date, window_end: date, sample_count: int) -> Dict[str, Any]:
    return {
        "holiday_event_id": event.id,
        "holiday_name": event.name,
        "holiday_date": event.date,
        "expected_change_pct": 0.0,
        "recommended_adjustment_pct": 0.0,
        "confidence": "low",
        "explanation": "We don't have enough history around this holiday yet. Add more transactions to unlock personalized insights.",
        "top_categories": [],
        "status": "insufficient_data",
        "baseline_spend": 0.0,
        "holiday_spend": 0.0,
        "pct_change": 0.0,
        "window_start": window_start,
        "window_end": window_end
    }

def _save_insight(db: Session, user_id: int, event_id: int, insight_data: Dict[str, Any]) -> None:
    expires_at = datetime.utcnow() + timedelta(hours=12)
    record = models.HolidayInsight(
        user_id=user_id,
        holiday_event_id=event_id,
        window_start=insight_data.get("window_start"),
        window_end=insight_data.get("window_end"),
        baseline_spend=insight_data.get("baseline_spend", 0.0),
        holiday_spend=insight_data.get("holiday_spend", 0.0),
        pct_change=insight_data.get("pct_change", 0.0),
        confidence=insight_data.get("confidence", "low"),
        top_categories_json=json.dumps(insight_data.get("top_categories", [])),
        recommended_adjustment_pct=insight_data.get("recommended_adjustment_pct", 0.0),
        explanation=insight_data.get("explanation", ""),
        status=insight_data.get("status", "ok"),
        generated_at=datetime.utcnow(),
        expires_at=expires_at
    )
    db.add(record)
    db.commit()

def _format_insight_response(event: models.HolidayEvent, insight: models.HolidayInsight) -> Dict[str, Any]:
    try:
        top_categories = json.loads(insight.top_categories_json or "[]")
    except json.JSONDecodeError:
        top_categories = []
    return {
        "holiday_event_id": event.id,
        "holiday_name": event.name,
        "holiday_date": event.date,
        "expected_change_pct": round(insight.pct_change * 100, 1),
        "recommended_adjustment_pct": round(insight.recommended_adjustment_pct or 0.0, 1),
        "confidence": insight.confidence or "low",
        "explanation": insight.explanation or "",
        "top_categories": top_categories,
        "status": insight.status or "ok"
    }
