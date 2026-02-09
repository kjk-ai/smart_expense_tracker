import json
import os
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from . import models

def load_holiday_data() -> List[Dict[str, Any]]:
    data_path = os.path.join(os.path.dirname(__file__), "data", "holidays.json")
    with open(data_path, "r", encoding="utf-8") as handle:
        return json.load(handle)

def seed_holidays_missing(db: Session) -> int:
    existing_rows = db.query(
        models.HolidayEvent.name,
        models.HolidayEvent.date,
        models.HolidayEvent.country_code
    ).all()
    existing_keys = {(row[0], row[1], row[2]) for row in existing_rows}

    records = []
    for item in load_holiday_data():
        key = (item["name"], datetime.strptime(item["date"], "%Y-%m-%d").date(), item["country_code"])
        if key in existing_keys:
            continue
        records.append(models.HolidayEvent(
            name=item["name"],
            date=key[1],
            country_code=item["country_code"],
            type=item["type"],
            tags=json.dumps(item.get("tags", [])),
            source=item.get("source", "curated")
        ))
    if records:
        db.add_all(records)
        db.commit()
    return len(records)
