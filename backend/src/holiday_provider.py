import json
import urllib.parse
import urllib.request
from datetime import date
from typing import List, Dict, Any

from .core.config import settings

def fetch_calendarific_holidays(country_code: str, year: int) -> List[Dict[str, Any]]:
    if not settings.CALENDARIFIC_API_KEY:
        return []

    params = {
        "api_key": settings.CALENDARIFIC_API_KEY,
        "country": country_code,
        "year": year
    }
    url = "https://calendarific.com/api/v2/holidays?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "expense-tracker/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    holidays = payload.get("response", {}).get("holidays", [])
    results: List[Dict[str, Any]] = []
    for item in holidays:
        normalized = _normalize_calendarific(item, country_code)
        if normalized:
            results.append(normalized)
    return results

def _normalize_calendarific(item: Dict[str, Any], country_code: str) -> Dict[str, Any] | None:
    name = item.get("name") or "Holiday"
    date_info = item.get("date", {})
    date_iso = date_info.get("iso")
    if not date_iso:
        return None
    try:
        event_date = date.fromisoformat(date_iso[:10])
    except ValueError:
        return None

    types = item.get("type") or []
    type_tokens = [token.lower() for token in types]
    holiday_type = "cultural"
    if any("religious" in token for token in type_tokens):
        holiday_type = "religious"
    elif any("national" in token or "public" in token or "bank" in token for token in type_tokens):
        holiday_type = "public"

    tags = set()
    for token in type_tokens:
        token = token.replace("/", " ").replace("-", " ")
        tags.update([part.strip() for part in token.split() if part.strip()])

    name_lower = name.lower()
    if "ramadan" in name_lower:
        tags.add("ramadan")
    if "eid" in name_lower:
        tags.add("eid")
    if "diwali" in name_lower:
        tags.add("diwali")
    if "christmas" in name_lower:
        tags.add("christmas")

    return {
        "name": name,
        "date": event_date,
        "country_code": country_code,
        "type": holiday_type,
        "tags": sorted(tags),
        "source": "calendarific"
    }
