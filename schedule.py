import datetime as dt
from copy import deepcopy
from typing import Dict, Iterable, List, Optional


def parse_skip_rows(rows: Optional[Iterable[dict]]) -> List[dict]:
    result = []
    for row in rows or []:
        try:
            start = dt.date.fromisoformat(str(row["start_date"]))
            count = int(row["skip_count"])
        except (KeyError, TypeError, ValueError):
            continue
        if row.get("active", True) and count > 0:
            result.append({"roommate": str(row.get("roommate", "")).strip(), "start_date": start, "skip_count": count})
    return [row for row in result if row["roommate"]]


def person_for_date(selected: dt.date, anchor_date: dt.date, names: List[str], anchor_person: str, skips: Optional[Iterable[dict]] = None, pauses: Optional[Iterable[dict]] = None) -> Optional[str]:
    if not names or anchor_person not in names:
        raise ValueError("invalid roster or anchor person")
    skip_rows = parse_skip_rows(skips)
    paused = {dt.date.fromisoformat(str(row['pause_date'])) for row in pauses or []}
    if selected in paused:
        return None
    if selected < anchor_date:
        return names[((selected - anchor_date).days + names.index(anchor_person)) % len(names)]
    remaining: Dict[str, int] = {name: 0 for name in names}
    current = anchor_date
    current_index = names.index(anchor_person)
    while current <= selected:
        if current in paused:
            current += dt.timedelta(days=1)
            continue
        candidate = names[current_index]
        active_skip = next((row for row in skip_rows if row["roommate"] == candidate and row["start_date"] <= current and row["skip_count"] > 0), None)
        if active_skip:
            active_skip["skip_count"] -= 1
            remaining[candidate] += 1
            current_index = (current_index + 1) % len(names)
            continue
        else:
            result = candidate
            if remaining[candidate] > 0:
                remaining[candidate] -= 1
            else:
                current_index = (current_index + 1) % len(names)
            if current == selected:
                return result
        current += dt.timedelta(days=1)
    raise RuntimeError("schedule calculation did not produce a result")


def week_schedule(start: dt.date, days: int, anchor_date: dt.date, names: List[str], anchor_person: str, skips: Optional[Iterable[dict]] = None, pauses: Optional[Iterable[dict]] = None) -> List[dict]:
    return [{"date": start + dt.timedelta(days=offset), "person": person_for_date(start + dt.timedelta(days=offset), anchor_date, names, anchor_person, skips, pauses)} for offset in range(days)]


def preview_pause(today, skips, pauses):
    """Mirror the transaction without changing caller-owned records."""
    day = today
    paused = {dt.date.fromisoformat(str(row['pause_date'])) for row in pauses}
    while day in paused:
        day += dt.timedelta(days=1)
    shifted = deepcopy(skips)
    for row in shifted:
        start = dt.date.fromisoformat(str(row['start_date']))
        if start >= day:
            row['start_date'] = str(start + dt.timedelta(days=1))
    return day, shifted, [*deepcopy(pauses), {'pause_date': str(day)}]
