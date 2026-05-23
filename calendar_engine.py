"""Calendar and production schedule engine for the Producer Calendar local app.

This module is intentionally dependency-light so it can be reused by the local web
app, Excel export, and PDF export paths.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
import calendar
import json
import re
from typing import Dict, Iterable, List, Optional, Tuple, Any

DATE_FMT = "%m/%d/%y"

PERIOD_ORDER = [
    "rd",
    "pre",
    "travel",
    "production",
    "hiatus",
    "post",
    "print_ship",
]

PERIOD_LABELS = {
    "rd": "R&D",
    "pre": "Pre-Production",
    "travel": "Travel/Prep",
    "production": "Production",
    "hiatus": "Hiatus",
    "post": "Post Production",
    "print_ship": "Print & Ship",
    "ready": "Ready for Release",
}

# Hex colors are aligned to the production methodology requested by the user.
# Travel/Prep color updated to tan per user request.
PERIOD_COLORS = {
    "rd": "F4B183",          # light orange
    "pre": "FFF26B",         # yellow
    "travel": "D2B48C",      # tan for Travel/Prep
    "production": "5B9BD5",  # blue
    "hiatus": "E7A1C4",      # pink
    "post": "E06666",        # red
    "print_ship": "70AD47",  # green
    "ready": "000000",       # black
}

LOCATION_LABELS = {
    "US": "United States",
    "NY": "New York",
    "CA": "Canada",
    "UK": "United Kingdom",
    "MX": "Mexico",
}

HOLIDAY_COLORS = {
    "US": "82D9F1",
    "NY": "F4A93B",
    "CA": "DFE3DC",
    "UK": "EF9ACB",
    "MX": "FFF719",
}


def parse_date(value: Any) -> Optional[date]:
    """Parse supported app date formats into a date.

    The UI displays mm/dd/yy but also sends ISO dates in some contexts.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    value = str(value).strip()
    if not value:
        return None
    # Accept yyyy-mm-dd from HTML date controls if they appear.
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%m-%d-%y", "%m-%d-%Y"):
        try:
            return __import__("datetime").datetime.strptime(value, fmt).date()
        except Exception:
            pass
    # Accept compact 010526 or 01052026.
    compact = re.sub(r"\D", "", value)
    if len(compact) == 6:
        try:
            return __import__("datetime").datetime.strptime(compact, "%m%d%y").date()
        except Exception:
            pass
    if len(compact) == 8:
        try:
            return __import__("datetime").datetime.strptime(compact, "%m%d%Y").date()
        except Exception:
            pass
    return None


def fmt(d: Optional[date]) -> str:
    return d.strftime(DATE_FMT) if d else ""


def iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return nth weekday in month. weekday: Monday=0."""
    first = date(year, month, 1)
    days_until = (weekday - first.weekday()) % 7
    return first + timedelta(days=days_until + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def observed_fixed(year: int, month: int, day: int) -> date:
    """Common observed-day rule: Saturday -> previous Friday; Sunday -> following Monday."""
    d = date(year, month, day)
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def easter_date(year: int) -> date:
    """Gregorian Easter Sunday using Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


@dataclass
class Holiday:
    date: date
    name: str
    region: str
    observed: bool = False
    source: str = "dynamic rule"

    def as_json(self) -> Dict[str, Any]:
        return {
            "date": iso(self.date),
            "displayDate": fmt(self.date),
            "name": self.name,
            "region": self.region,
            "regionLabel": LOCATION_LABELS.get(self.region, self.region),
            "observed": self.observed,
            "source": self.source,
            "color": HOLIDAY_COLORS.get(self.region, "D9EAD3"),
        }


def _fixed_holiday(year: int, month: int, day: int, name: str, region: str, source: str) -> Holiday:
    actual = date(year, month, day)
    obs = observed_fixed(year, month, day)
    return Holiday(obs, name + (" (observed)" if obs != actual else ""), region, obs != actual, source)


def holidays_for_year(year: int, region: str = "US") -> List[Holiday]:
    """Generate dynamic holidays by year and region.

    US/NY holiday source follows the Paymaster 2025-26 holiday list and holiday breakdown
    the user provided. CA/UK/MX continue the same dynamic assumptions used in the prior tool.
    """
    region = (region or "US").upper()
    e = easter_date(year)
    source_paymaster = "Paymaster holiday list + dynamic carry-forward rule"
    holidays: List[Holiday] = []

    if region == "US":
        holidays.extend([
            _fixed_holiday(year, 1, 1, "New Year's Day", "US", source_paymaster),
            Holiday(nth_weekday(year, 1, 0, 3), "Martin Luther King, Jr. Day", "US", False, source_paymaster),
            Holiday(nth_weekday(year, 2, 0, 3), "Presidents Day / Washington's Birthday", "US", False, source_paymaster),
            Holiday(e - timedelta(days=2), "Good Friday", "US", False, source_paymaster),
            Holiday(e, "Easter Sunday", "US", False, source_paymaster),
            Holiday(last_weekday(year, 5, 0), "Memorial Day", "US", False, source_paymaster),
            _fixed_holiday(year, 6, 19, "Juneteenth", "US", source_paymaster),
            _fixed_holiday(year, 7, 4, "Independence Day", "US", source_paymaster),
            Holiday(nth_weekday(year, 9, 0, 1), "Labor Day", "US", False, source_paymaster),
            Holiday(nth_weekday(year, 10, 0, 2), "Columbus Day", "US", False, source_paymaster),
            _fixed_holiday(year, 11, 11, "Veterans Day", "US", source_paymaster),
            Holiday(nth_weekday(year, 11, 3, 4), "Thanksgiving Day", "US", False, source_paymaster),
            Holiday(nth_weekday(year, 11, 3, 4) + timedelta(days=1), "Day After Thanksgiving", "US", False, source_paymaster),
            _fixed_holiday(year, 12, 25, "Christmas Day", "US", source_paymaster),
        ])
    elif region == "NY":
        # NY profile is the Paymaster/film-production US profile with New York-specific Lincoln's Birthday retained.
        holidays = holidays_for_year(year, "US")
        for h in holidays:
            h.region = "NY"
            h.source = "Paymaster list + New York profile"
        holidays.append(_fixed_holiday(year, 2, 12, "Lincoln's Birthday", "NY", "Paymaster list + New York profile"))
    elif region == "CA":
        # Canada default: federal/common production-planning set, with observed fixed-date holidays.
        holidays.extend([
            _fixed_holiday(year, 1, 1, "New Year's Day", "CA", "Canada dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 2, 0, 3), "Family Day", "CA", False, "Canada dynamic carry-forward rule"),
            Holiday(e - timedelta(days=2), "Good Friday", "CA", False, "Canada dynamic carry-forward rule"),
            Holiday(last_weekday(year, 5, 0) if last_weekday(year, 5, 0).day <= 24 else last_weekday(year, 5, 0) - timedelta(days=7), "Victoria Day", "CA", False, "Canada dynamic carry-forward rule"),
            _fixed_holiday(year, 7, 1, "Canada Day", "CA", "Canada dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 8, 0, 1), "Civic Holiday", "CA", False, "Canada dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 9, 0, 1), "Labour Day", "CA", False, "Canada dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 10, 0, 2), "Thanksgiving Day", "CA", False, "Canada dynamic carry-forward rule"),
            _fixed_holiday(year, 12, 25, "Christmas Day", "CA", "Canada dynamic carry-forward rule"),
            _fixed_holiday(year, 12, 26, "Boxing Day", "CA", "Canada dynamic carry-forward rule"),
        ])
    elif region == "UK":
        # England/Wales bank holiday default for UK production planning.
        holidays.extend([
            _fixed_holiday(year, 1, 1, "New Year's Day", "UK", "UK England/Wales dynamic carry-forward rule"),
            Holiday(e - timedelta(days=2), "Good Friday", "UK", False, "UK England/Wales dynamic carry-forward rule"),
            Holiday(e + timedelta(days=1), "Easter Monday", "UK", False, "UK England/Wales dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 5, 0, 1), "Early May Bank Holiday", "UK", False, "UK England/Wales dynamic carry-forward rule"),
            Holiday(last_weekday(year, 5, 0), "Spring Bank Holiday", "UK", False, "UK England/Wales dynamic carry-forward rule"),
            Holiday(last_weekday(year, 8, 0), "Summer Bank Holiday", "UK", False, "UK England/Wales dynamic carry-forward rule"),
        ])
        christmas = date(year, 12, 25)
        boxing = date(year, 12, 26)
        # UK substitute days when Christmas/Boxing Day fall on weekends.
        if christmas.weekday() < 5:
            holidays.append(Holiday(christmas, "Christmas Day", "UK", False, "UK England/Wales dynamic carry-forward rule"))
        else:
            # substitute is Monday unless Boxing Day also needs it; handled below.
            holidays.append(Holiday(observed_fixed(year, 12, 25), "Christmas Day (substitute)", "UK", True, "UK England/Wales dynamic carry-forward rule"))
        if boxing.weekday() < 5 and boxing not in [h.date for h in holidays]:
            holidays.append(Holiday(boxing, "Boxing Day", "UK", False, "UK England/Wales dynamic carry-forward rule"))
        else:
            sub = observed_fixed(year, 12, 26)
            while sub in [h.date for h in holidays]:
                sub += timedelta(days=1)
            holidays.append(Holiday(sub, "Boxing Day (substitute)", "UK", True, "UK England/Wales dynamic carry-forward rule"))
    elif region == "MX":
        holidays.extend([
            _fixed_holiday(year, 1, 1, "New Year's Day", "MX", "Mexico dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 2, 0, 1), "Constitution Day", "MX", False, "Mexico dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 3, 0, 3), "Benito Juarez Day", "MX", False, "Mexico dynamic carry-forward rule"),
            Holiday(e - timedelta(days=2), "Good Friday", "MX", False, "Mexico dynamic carry-forward rule"),
            _fixed_holiday(year, 5, 1, "Labor Day", "MX", "Mexico dynamic carry-forward rule"),
            _fixed_holiday(year, 9, 16, "Independence Day", "MX", "Mexico dynamic carry-forward rule"),
            Holiday(nth_weekday(year, 11, 0, 3), "Revolution Day", "MX", False, "Mexico dynamic carry-forward rule"),
            _fixed_holiday(year, 12, 25, "Christmas Day", "MX", "Mexico dynamic carry-forward rule"),
        ])
    else:
        return holidays_for_year(year, "US")

    # Deduplicate by date/name and sort.
    seen = set()
    out: List[Holiday] = []
    for h in holidays:
        key = (h.date, h.name, h.region)
        if key not in seen:
            seen.add(key)
            out.append(h)
    out.sort(key=lambda h: (h.date, h.name))
    return out


def holiday_map_for_range(start: date, end: date, region: str) -> Dict[date, List[Holiday]]:
    if start > end:
        return {}
    mapping: Dict[date, List[Holiday]] = {}
    for year in range(start.year, end.year + 1):
        for h in holidays_for_year(year, region):
            if start <= h.date <= end:
                mapping.setdefault(h.date, []).append(h)
    return mapping


def all_holidays_for_year(year: int) -> List[Holiday]:
    out: List[Holiday] = []
    for region in ["CA", "NY", "US", "UK", "MX"]:
        out.extend(holidays_for_year(year, region))
    out.sort(key=lambda h: (h.date, h.region, h.name))
    return out


def is_valid_production_day(d: date, region: str, hmap: Dict[date, List[Holiday]]) -> bool:
    return d.weekday() < 5 and d not in hmap


def add_calendar_days(start: date, days: int) -> Tuple[date, date]:
    days = max(int(days or 0), 0)
    if days <= 0:
        return start, start - timedelta(days=1)
    return start, start + timedelta(days=days - 1)


def subtract_calendar_days(end: date, days: int) -> Tuple[date, date]:
    days = max(int(days or 0), 0)
    if days <= 0:
        return end + timedelta(days=1), end
    return end - timedelta(days=days - 1), end


def next_weekday(d: date) -> date:
    """Return d if it is Monday-Friday; otherwise the next Monday."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def prev_weekday(d: date) -> date:
    """Return d if it is Monday-Friday; otherwise the prior Friday."""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def add_weekdays(start: date, workdays: int) -> Tuple[date, date]:
    """Add a Monday-Friday duration. Returns adjusted_start, end."""
    workdays = max(int(workdays or 0), 0)
    if workdays <= 0:
        return start, start - timedelta(days=1)
    cur = next_weekday(start)
    adjusted_start = cur
    counted = 0
    while counted < workdays:
        if cur.weekday() < 5:
            counted += 1
            if counted >= workdays:
                return adjusted_start, cur
        cur += timedelta(days=1)
    return adjusted_start, cur


def subtract_weekdays(end: date, workdays: int) -> Tuple[date, date]:
    """Subtract a Monday-Friday duration. Returns start, adjusted_end."""
    workdays = max(int(workdays or 0), 0)
    if workdays <= 0:
        return end + timedelta(days=1), end
    cur = prev_weekday(end)
    adjusted_end = cur
    counted = 0
    while counted < workdays:
        if cur.weekday() < 5:
            counted += 1
            if counted >= workdays:
                return cur, adjusted_end
        cur -= timedelta(days=1)
    return cur, adjusted_end


def next_valid_production_day(d: date, region: str) -> date:
    hmap = holiday_map_for_range(d - timedelta(days=7), d + timedelta(days=30), region)
    while d.weekday() >= 5 or d in hmap:
        d += timedelta(days=1)
        if d not in hmap:
            hmap = holiday_map_for_range(d - timedelta(days=7), d + timedelta(days=30), region)
    return d


def prev_valid_production_day(d: date, region: str) -> date:
    hmap = holiday_map_for_range(d - timedelta(days=30), d + timedelta(days=7), region)
    while d.weekday() >= 5 or d in hmap:
        d -= timedelta(days=1)
        if d not in hmap:
            hmap = holiday_map_for_range(d - timedelta(days=30), d + timedelta(days=7), region)
    return d


def production_end_from_start(start: date, workdays: int, region: str) -> Tuple[date, Dict[str, Any]]:
    workdays = max(int(workdays or 0), 0)
    if workdays <= 0:
        return start - timedelta(days=1), {"countedWorkdays": 0, "skippedWeekends": 0, "skippedHolidays": 0}
    # Make a broad holiday map; production can extend substantially if dates land around year boundaries.
    broad_end = start + timedelta(days=workdays * 3 + 45)
    hmap = holiday_map_for_range(start - timedelta(days=10), broad_end, region)
    counted = 0
    skipped_weekends = 0
    skipped_holidays = 0
    cur = start
    while counted < workdays:
        if cur.weekday() >= 5:
            skipped_weekends += 1
        elif cur in hmap:
            skipped_holidays += 1
        else:
            counted += 1
        if counted >= workdays:
            break
        cur += timedelta(days=1)
    return cur, {"countedWorkdays": counted, "skippedWeekends": skipped_weekends, "skippedHolidays": skipped_holidays}


def production_start_from_end(end: date, workdays: int, region: str) -> Tuple[date, Dict[str, Any]]:
    workdays = max(int(workdays or 0), 0)
    if workdays <= 0:
        return end + timedelta(days=1), {"countedWorkdays": 0, "skippedWeekends": 0, "skippedHolidays": 0}
    broad_start = end - timedelta(days=workdays * 3 + 45)
    hmap = holiday_map_for_range(broad_start, end + timedelta(days=10), region)
    counted = 0
    skipped_weekends = 0
    skipped_holidays = 0
    cur = end
    while counted < workdays:
        if cur.weekday() >= 5:
            skipped_weekends += 1
        elif cur in hmap:
            skipped_holidays += 1
        else:
            counted += 1
        if counted >= workdays:
            break
        cur -= timedelta(days=1)
    return cur, {"countedWorkdays": counted, "skippedWeekends": skipped_weekends, "skippedHolidays": skipped_holidays}


def _get_periods(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    periods = payload.get("periods") or {}
    # Accept flat payloads from earlier tests.
    return periods


def _weeks(periods: Dict[str, Dict[str, Any]], key: str, default: int = 0) -> int:
    try:
        return int(periods.get(key, {}).get("weeks") or default)
    except Exception:
        return default


def _prod_days(periods: Dict[str, Dict[str, Any]], default: int = 0) -> int:
    try:
        return int(periods.get("production", {}).get("days") or default)
    except Exception:
        return default


def _start(periods: Dict[str, Dict[str, Any]], key: str) -> Optional[date]:
    return parse_date(periods.get(key, {}).get("start"))


def _hiatus_start(periods: Dict[str, Dict[str, Any]]) -> Optional[date]:
    return parse_date(periods.get("hiatus", {}).get("start"))


def _hiatus_end(periods: Dict[str, Dict[str, Any]]) -> Optional[date]:
    return parse_date(periods.get("hiatus", {}).get("end"))


def _ready_date(periods: Dict[str, Dict[str, Any]]) -> Optional[date]:
    return parse_date(periods.get("ready", {}).get("date"))


def _determine_anchor(payload: Dict[str, Any], periods: Dict[str, Dict[str, Any]]) -> Optional[str]:
    mode = (payload.get("anchorMode") or payload.get("anchor") or "auto").strip()
    aliases = {"print": "print_ship", "printship": "print_ship", "ready_for_release": "ready"}
    mode = aliases.get(mode, mode)
    valid = set(PERIOD_ORDER + ["ready"])
    if mode in valid:
        return mode
    last = aliases.get(str(payload.get("lastEditedAnchor") or "").strip(), str(payload.get("lastEditedAnchor") or "").strip())
    if last in valid:
        # Verify there is a date value for that field.
        if last == "ready" and _ready_date(periods):
            return last
        if last == "hiatus" and _hiatus_start(periods):
            return last
        if last not in ("ready", "hiatus") and _start(periods, last):
            return last
    # Production is the practical default the user requested.
    if _start(periods, "production"):
        return "production"
    if _ready_date(periods):
        return "ready"
    for key in ["rd", "pre", "travel", "production", "hiatus", "post", "print_ship"]:
        if key == "hiatus" and _hiatus_start(periods):
            return key
        if key != "hiatus" and _start(periods, key):
            return key
    return None


def _phase_record(key: str, start: Optional[date], end: Optional[date], metric: Dict[str, Any], notes: Optional[List[str]] = None) -> Dict[str, Any]:
    days = 0
    if start and end and end >= start:
        days = (end - start).days + 1
    return {
        "key": key,
        "label": PERIOD_LABELS[key],
        "start": iso(start),
        "end": iso(end),
        "displayStart": fmt(start),
        "displayEnd": fmt(end),
        "calendarDays": days,
        "metric": metric,
        "color": PERIOD_COLORS[key],
        "notes": notes or [],
    }


def calculate_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    periods = _get_periods(payload)
    location = (payload.get("productionLocation") or payload.get("location") or "US").upper()
    if location not in LOCATION_LABELS:
        location = "US"
    anchor = _determine_anchor(payload, periods)
    warnings: List[str] = []
    notes: List[str] = []

    # Durations.
    weeks = {k: _weeks(periods, k, 0) for k in ["rd", "pre", "travel", "post", "print_ship"]}
    prod_days = _prod_days(periods, 0)
    h_start = _hiatus_start(periods)
    h_end = _hiatus_end(periods)
    if h_start and not h_end:
        h_end = h_start
    if h_start and h_end and h_end < h_start:
        h_start, h_end = h_end, h_start
        warnings.append("Hiatus dates were reversed; the app corrected the range.")

    # Helper calculations based on duration.
    intervals: Dict[str, Tuple[Optional[date], Optional[date]]] = {k: (None, None) for k in PERIOD_ORDER}
    production_stats: Dict[str, Any] = {}

    def forward_calendar(key: str, start: date) -> date:
        # Week-based phases use 5-day work weeks (Monday-Friday). Holidays only
        # extend Production, not these supporting phases.
        if weeks.get(key, 0) <= 0:
            intervals[key] = (None, None)
            return next_weekday(start)
        s, e = add_weekdays(start, weeks[key] * 5)
        intervals[key] = (s, e)
        return next_weekday(e + timedelta(days=1))

    def backward_calendar(key: str, end: date) -> date:
        # Week-based phases use 5-day work weeks (Monday-Friday). Holidays only
        # extend Production, not these supporting phases.
        if weeks.get(key, 0) <= 0:
            intervals[key] = (None, None)
            return prev_weekday(end)
        s, e = subtract_weekdays(end, weeks[key] * 5)
        intervals[key] = (s, e)
        return prev_weekday(s - timedelta(days=1))

    def forward_production(start: date) -> date:
        nonlocal production_stats
        if prod_days <= 0:
            intervals["production"] = (None, None)
            production_stats = {"countedWorkdays": 0, "skippedWeekends": 0, "skippedHolidays": 0}
            return next_weekday(start)
        adjusted_start = next_valid_production_day(start, location)
        if adjusted_start != start:
            warnings.append(f"Production start was moved from {fmt(start)} to {fmt(adjusted_start)} because Production counts workdays only and selected-location holidays extend the schedule.")
        e, production_stats = production_end_from_start(adjusted_start, prod_days, location)
        intervals["production"] = (adjusted_start, e)
        if production_stats.get("skippedHolidays", 0):
            notes.append(f"Production was automatically extended by {production_stats['skippedHolidays']} selected-location holiday day(s).")
        return next_weekday(e + timedelta(days=1))

    def backward_production(end: date) -> date:
        nonlocal production_stats
        if prod_days <= 0:
            intervals["production"] = (None, None)
            production_stats = {"countedWorkdays": 0, "skippedWeekends": 0, "skippedHolidays": 0}
            return prev_weekday(end)
        adjusted_end = prev_valid_production_day(end, location)
        if adjusted_end != end:
            warnings.append(f"Production end was moved from {fmt(end)} to {fmt(adjusted_end)} because Production counts workdays only and selected-location holidays extend the schedule.")
        s, production_stats = production_start_from_end(adjusted_end, prod_days, location)
        intervals["production"] = (s, adjusted_end)
        if production_stats.get("skippedHolidays", 0):
            notes.append(f"Production was automatically extended by {production_stats['skippedHolidays']} selected-location holiday day(s).")
        return prev_weekday(s - timedelta(days=1))

    def set_hiatus_forward(next_start: date) -> date:
        if h_start and h_end:
            intervals["hiatus"] = (h_start, h_end)
            if next_start > h_start:
                warnings.append("The fixed Hiatus range overlaps or begins before the calculated preceding phase ends.")
            return next_weekday(h_end + timedelta(days=1))
        intervals["hiatus"] = (None, None)
        return next_weekday(next_start)

    def set_hiatus_backward(prev_end: date) -> date:
        if h_start and h_end:
            intervals["hiatus"] = (h_start, h_end)
            if prev_end < h_end:
                warnings.append("The fixed Hiatus range overlaps or ends after the calculated following phase begins.")
            return prev_weekday(h_start - timedelta(days=1))
        intervals["hiatus"] = (None, None)
        return prev_weekday(prev_end)

    ready = _ready_date(periods)

    if not anchor:
        # Blank initial state.
        today = date.today()
        return {
            "ok": True,
            "needsInput": True,
            "message": "Enter a date into any period field or Ready for Release to create the calendar.",
            "projectTitle": payload.get("projectTitle") or "Feature Film",
            "anchor": "",
            "productionLocation": location,
            "productionLocationLabel": LOCATION_LABELS[location],
            "periods": [],
            "ready": None,
            "years": [today.year],
            "holidays": [h.as_json() for h in holidays_for_year(today.year, location)],
            "allHolidays": [h.as_json() for h in all_holidays_for_year(today.year)],
            "warnings": warnings,
            "notes": notes,
        }

    # Locate anchor date.
    if anchor == "ready":
        if not ready:
            warnings.append("Ready for Release is selected as anchor, but no date is entered.")
            ready = date.today()
        # Work backwards from the release milestone. Print & Ship ends the day before release.
        prev_end = prev_weekday(ready - timedelta(days=1))
        prev_end = backward_calendar("print_ship", prev_end)
        prev_end = backward_calendar("post", prev_end)
        prev_end = set_hiatus_backward(prev_end)
        prev_end = backward_production(prev_end)
        prev_end = backward_calendar("travel", prev_end)
        prev_end = backward_calendar("pre", prev_end)
        backward_calendar("rd", prev_end)
    elif anchor == "hiatus":
        if not h_start:
            h_start = date.today()
            h_end = h_start
            warnings.append("Hiatus is selected as anchor, but no range is entered; using today as a temporary one-day range.")
        if not h_end:
            h_end = h_start
        intervals["hiatus"] = (h_start, h_end)
        # Before hiatus.
        prev_end = h_start - timedelta(days=1)
        prev_end = backward_production(prev_end)
        prev_end = backward_calendar("travel", prev_end)
        prev_end = backward_calendar("pre", prev_end)
        backward_calendar("rd", prev_end)
        # After hiatus.
        next_start = next_weekday(h_end + timedelta(days=1))
        next_start = forward_calendar("post", next_start)
        next_start = forward_calendar("print_ship", next_start)
        ready = ready or next_start
    else:
        start = _start(periods, anchor)
        if not start:
            start = date.today()
            warnings.append(f"{PERIOD_LABELS[anchor]} is selected as anchor, but no date is entered; using today temporarily.")
        # Calculate anchor and forward side.
        idx = PERIOD_ORDER.index(anchor)
        if anchor in ["rd", "pre", "travel", "post", "print_ship"]:
            next_start = forward_calendar(anchor, start)
        elif anchor == "production":
            next_start = forward_production(start)
        else:
            next_start = start
        # Forward phases after anchor.
        for key in PERIOD_ORDER[idx + 1:]:
            if key == "hiatus":
                next_start = set_hiatus_forward(next_start)
            elif key == "production":
                next_start = forward_production(next_start)
            else:
                next_start = forward_calendar(key, next_start)
        ready = ready or next_start
        # Backward phases before anchor.
        prev_end = prev_weekday(start - timedelta(days=1))
        for key in reversed(PERIOD_ORDER[:idx]):
            if key == "hiatus":
                prev_end = set_hiatus_backward(prev_end)
            elif key == "production":
                prev_end = backward_production(prev_end)
            else:
                prev_end = backward_calendar(key, prev_end)

    # If the anchor was before hiatus and a fixed hiatus was not specified, preserve blank hiatus.
    if not (h_start and h_end) and intervals.get("hiatus") == (None, None):
        pass

    # Create period records.
    period_records: List[Dict[str, Any]] = []
    for key in PERIOD_ORDER:
        s, e = intervals.get(key, (None, None))
        if not (s and e) or (s and e and e < s):
            continue
        metric: Dict[str, Any] = {}
        if key in weeks:
            metric = {"type": "weeks", "value": weeks[key]}
        elif key == "production":
            metric = {"type": "workdays", "value": prod_days, **production_stats}
        elif key == "hiatus":
            metric = {"type": "date_range", "value": (e - s).days + 1 if s and e else 0}
        period_records.append(_phase_record(key, s, e, metric))
    ready_record = {
        "key": "ready",
        "label": PERIOD_LABELS["ready"],
        "date": iso(ready),
        "displayDate": fmt(ready),
        "color": PERIOD_COLORS["ready"],
    }

    # Warn on non-anchor manually entered dates that do not match calculated starts.
    for rec in period_records:
        key = rec["key"]
        if key == "hiatus":
            continue
        entered = _start(periods, key)
        calc = parse_date(rec["start"])
        if entered and calc and key != anchor and entered != calc:
            warnings.append(f"Entered {PERIOD_LABELS[key]} start {fmt(entered)} differs from calculated start {fmt(calc)}. Select that field as the anchor to use it.")
    entered_ready = _ready_date(periods)
    if entered_ready and ready and anchor != "ready" and entered_ready != ready:
        warnings.append(f"Entered Ready for Release date {fmt(entered_ready)} differs from calculated date {fmt(ready)}. Select Ready for Release as the anchor to use it.")

    all_dates: List[date] = []
    for rec in period_records:
        s = parse_date(rec["start"])
        e = parse_date(rec["end"])
        if s:
            all_dates.append(s)
        if e:
            all_dates.append(e)
    if ready:
        all_dates.append(ready)
    if not all_dates:
        all_dates = [date.today()]
    min_date, max_date = min(all_dates), max(all_dates)
    years = list(range(min_date.year, max_date.year + 1))
    holidays = []
    all_holidays = []
    for y in years:
        holidays.extend([h.as_json() for h in holidays_for_year(y, location)])
        all_holidays.extend([h.as_json() for h in all_holidays_for_year(y)])

    # Day table for exports and UI details.
    selected_hmap = holiday_map_for_range(date(years[0], 1, 1), date(years[-1], 12, 31), location)
    rows: List[Dict[str, Any]] = []
    cursor = min_date
    # Expand displayed rows to whole years for calendar output.
    cursor = date(years[0], 1, 1)
    final = date(years[-1], 12, 31)
    while cursor <= final:
        active_periods = []
        for rec in period_records:
            s = parse_date(rec["start"])
            e = parse_date(rec["end"])
            if s and e and s <= cursor <= e and cursor.weekday() < 5:
                active_periods.append(rec["key"])
        is_ready = ready == cursor
        hlist = selected_hmap.get(cursor, [])
        rows.append({
            "date": iso(cursor),
            "displayDate": fmt(cursor),
            "weekday": cursor.strftime("%A"),
            "year": cursor.year,
            "month": cursor.month,
            "day": cursor.day,
            "periodKeys": active_periods,
            "periodLabels": [PERIOD_LABELS[k] for k in active_periods],
            "ready": is_ready,
            "holidayNames": [h.name for h in hlist],
            "holidayRegions": [h.region for h in hlist],
            "isProductionWorkday": bool("production" in active_periods and is_valid_production_day(cursor, location, selected_hmap)),
            "isWeekend": cursor.weekday() >= 5,
        })
        cursor += timedelta(days=1)

    return {
        "ok": True,
        "needsInput": False,
        "projectTitle": payload.get("projectTitle") or "Feature Film",
        "anchor": anchor,
        "anchorLabel": PERIOD_LABELS.get(anchor, anchor),
        "productionLocation": location,
        "productionLocationLabel": LOCATION_LABELS[location],
        "periods": period_records,
        "ready": ready_record,
        "years": years,
        "holidays": holidays,
        "allHolidays": all_holidays,
        "dayRows": rows,
        "warnings": warnings,
        "notes": notes,
        "periodColors": PERIOD_COLORS,
        "holidayColors": HOLIDAY_COLORS,
        "locationLabels": LOCATION_LABELS,
    }


if __name__ == "__main__":
    sample = {
        "projectTitle": "Feature Film",
        "productionLocation": "US",
        "anchorMode": "production",
        "periods": {
            "rd": {"weeks": 0},
            "pre": {"weeks": 8},
            "travel": {"weeks": 0},
            "production": {"start": "01/05/26", "days": 45},
            "hiatus": {"start": "", "end": ""},
            "post": {"weeks": 12},
            "print_ship": {"weeks": 2},
            "ready": {"date": ""},
        },
    }
    print(json.dumps(calculate_schedule(sample), indent=2, default=str)[:4000])
