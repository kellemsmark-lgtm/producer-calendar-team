"""PDF export for Producer Calendar local app.

The PDF button must create and download a PDF only.

v3.3 safe export path: first try LibreOffice/soffice to convert the same
reference-format XLSX into a PDF. If LibreOffice is not available, generate a
native ReportLab PDF instead. Microsoft Excel automation is intentionally not used
because it can open a temporary XLSX/save prompt on some Macs.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional, Tuple
import calendar as py_calendar
import math
import shutil
import subprocess
import tempfile

from openpyxl import load_workbook

from calendar_engine import calculate_schedule, parse_date, fmt, PERIOD_COLORS, PERIOD_LABELS
from export_excel import create_workbook


def _candidate_soffice_paths() -> Iterable[str]:
    """Yield LibreOffice/soffice paths.

    LibreOffice produces the closest match to the reference Excel layout because
    it exports directly from the generated workbook.
    """
    for name in ("libreoffice", "soffice"):
        found = shutil.which(name)
        if found:
            yield found
    yield "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def _convert_with_libreoffice(xlsx_path: Path, out_pdf: Path) -> bool:
    for soffice in _candidate_soffice_paths():
        if not soffice or not Path(soffice).exists():
            continue
        with tempfile.TemporaryDirectory(prefix="producer_calendar_pdf_") as td:
            td_path = Path(td)
            cmd = [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(td_path),
                str(xlsx_path),
            ]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            except Exception:
                continue
            if result.returncode != 0:
                continue
            produced = td_path / f"{xlsx_path.stem}.pdf"
            if not produced.exists():
                matches = list(td_path.glob("*.pdf"))
                produced = matches[0] if matches else produced
            if produced.exists():
                out_pdf.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(produced, out_pdf)
                return True
    return False




def _hide_non_calendar_sheets_for_pdf(xlsx_path: Path) -> None:
    """Hide Inputs/helper sheets so the converted PDF contains only calendar tabs."""
    wb = load_workbook(xlsx_path)
    visible_years = []
    for ws in wb.worksheets:
        if ws.title.isdigit():
            ws.sheet_state = "visible"
            visible_years.append(ws)
        else:
            ws.sheet_state = "hidden"
    if not visible_years:
        wb.worksheets[0].sheet_state = "visible"
        visible_years = [wb.worksheets[0]]
    wb.active = wb.index(visible_years[0])
    wb.save(xlsx_path)


def _hex(hex_color: str):
    from reportlab.lib import colors
    return colors.HexColor("#" + hex_color.replace("#", ""))


def _parse_iso(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return parse_date(value)


def _month_name(month: int) -> str:
    return py_calendar.month_name[month].upper()


def _ordinal(d: date) -> str:
    day = d.day
    if 11 <= (day % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{d.strftime('%B')} {day}{suffix}, {d.year}"


def _period_records(schedule: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {p.get("key"): p for p in schedule.get("periods", [])}


def _date_in_period(d: date, rec: Dict[str, Any]) -> bool:
    start = _parse_iso(rec.get("start"))
    end = _parse_iso(rec.get("end"))
    return bool(start and end and start <= d <= end)


def _production_holiday_dates(schedule: Dict[str, Any]) -> set[date]:
    recs = _period_records(schedule)
    prod = recs.get("production") or {}
    start = _parse_iso(prod.get("start"))
    end = _parse_iso(prod.get("end"))
    if not start or not end:
        return set()
    out = set()
    for h in schedule.get("holidays", []):
        hd = _parse_iso(h.get("date"))
        if hd and start <= hd <= end and hd.weekday() < 5:
            out.add(hd)
    return out


def _fill_for_date(d: date, schedule: Dict[str, Any]) -> Tuple[Optional[str], str]:
    recs = _period_records(schedule)
    ready_date = _parse_iso((schedule.get("ready") or {}).get("date"))
    if ready_date and d == ready_date:
        return PERIOD_COLORS["ready"], "white"
    if d.weekday() >= 5:
        return None, "#777777"
    prod_holidays = _production_holiday_dates(schedule)
    if d in prod_holidays:
        return PERIOD_COLORS["hiatus"], "black"
    for key in ["rd", "pre", "travel", "production", "hiatus", "post", "print_ship"]:
        rec = recs.get(key)
        if rec and _date_in_period(d, rec):
            return PERIOD_COLORS[key], "black"
    return None, "black"


def _draw_centered(c, text: str, x: float, y: float, w: float, h: float, font="Helvetica", size=7, color="black"):
    c.setFont(font, size)
    if color == "white":
        from reportlab.lib import colors
        c.setFillColor(colors.white)
    elif isinstance(color, str) and color.startswith("#"):
        c.setFillColor(_hex(color[1:]))
    else:
        from reportlab.lib import colors
        c.setFillColor(colors.black)
    c.drawCentredString(x + w / 2, y + h / 2 - size / 2 + 2, str(text))


def _draw_month(c, year: int, month: int, x: float, y_top: float, w: float, h: float, schedule: Dict[str, Any]):
    """Draw a month block that closely follows the reference XLSX/PDF style."""
    from reportlab.lib import colors
    navy = colors.HexColor("#092060")
    grid = colors.HexColor("#9EB6D8")
    title_h = 17
    dow_h = 12
    cell_h = (h - title_h - dow_h) / 6
    cell_w = w / 7

    # Navy month header, month/year in white.
    y = y_top - title_h
    c.setFillColor(navy)
    c.rect(x, y, w, title_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x + 3, y + 4.2, f"{py_calendar.month_name[month]} '{str(year)[-2:]}")
    c.drawRightString(x + w - 3, y + 4.2, str(year))

    # Weekday row.
    y -= dow_h
    c.setFillColor(colors.white)
    c.rect(x, y, w, dow_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6.7)
    for idx, label in enumerate(["Su", "M", "Tu", "W", "Th", "F", "Sa"]):
        c.drawCentredString(x + idx * cell_w + cell_w/2, y + 3.2, label)

    first = date(year, month, 1)
    start_offset = (first.weekday() + 1) % 7  # Sunday=0
    days = py_calendar.monthrange(year, month)[1]
    c.setStrokeColor(grid)
    c.setLineWidth(0.45)
    for i in range(42):
        col = i % 7
        row = i // 7
        cx = x + col * cell_w
        cy = y - (row + 1) * cell_h
        day_num = i - start_offset + 1
        if 1 <= day_num <= days:
            d = date(year, month, day_num)
            fill_hex, text_color = _fill_for_date(d, schedule)
            if fill_hex:
                c.setFillColor(_hex(fill_hex))
                c.rect(cx, cy, cell_w, cell_h, stroke=0, fill=1)
            else:
                c.setFillColor(colors.white)
                c.rect(cx, cy, cell_w, cell_h, stroke=0, fill=1)
            c.setStrokeColor(grid)
            c.setLineWidth(0.45)
            c.rect(cx, cy, cell_w, cell_h, stroke=1, fill=0)
            is_weekend = d.weekday() >= 5
            font = "Helvetica-Bold" if fill_hex else "Helvetica"
            color = text_color if fill_hex else ("#777777" if is_weekend else "black")
            _draw_centered(c, day_num, cx, cy, cell_w, cell_h, font, 6.4, color)
        else:
            c.setFillColor(colors.white)
            c.rect(cx, cy, cell_w, cell_h, stroke=1, fill=1)


def _metric_text(key: str, rec: Dict[str, Any]) -> str:
    metric = rec.get("metric") or {}
    if key == "production":
        days = metric.get("value") or metric.get("countedWorkdays") or ""
        start = _parse_iso(rec.get("start"))
        end = _parse_iso(rec.get("end"))
        weeks = ""
        if start and end:
            weeks = math.ceil(((end - start).days + 1) / 7)
        return f"{weeks} weeks /\n{days} days" if weeks else f"{days} days"
    if key in ("hiatus", "ready", "print_ship"):
        return ""
    val = metric.get("value")
    return f"{val} weeks" if val not in (None, "", 0) else ""


def _date_line(key: str, rec: Dict[str, Any], ready: Dict[str, Any]) -> str:
    if key == "ready":
        rd = _parse_iso(ready.get("date"))
        return f"Ready for Release - {_ordinal(rd)}" if rd else ""
    s = _parse_iso(rec.get("start"))
    e = _parse_iso(rec.get("end"))
    if key == "print_ship":
        metric = rec.get("metric") or {}
        return f"Plus {metric.get('value') or ''} weeks for Print & Ship".strip()
    if key == "hiatus":
        return f"Hiatus - {_ordinal(s)} to {_ordinal(e)}" if s and e else ""
    if s:
        return f"Begin {PERIOD_LABELS[key]} - {_ordinal(s)}"
    return ""


def _draw_bottom_box(c, x: float, y_top: float, w: float, h: float, schedule: Dict[str, Any]):
    """Draw the bottom Dates box and adjacent legend without text overlap.

    This native PDF fallback mirrors the XLSX lower section: a single thick
    Dates box on the left and two-cell-wide color swatches with labels on the
    right.  Earlier PDF fallback layouts used fixed y positions that could push
    Ready for Release onto the bottom border when Hiatus, R&D, or Travel/Prep
    were present.  This version computes the available vertical spacing and
    shrinks the text slightly only when extra rows are required.
    """
    from reportlab.lib import colors

    recs = _period_records(schedule)
    present = {k for k in recs.keys() if k}

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8.6)
    c.drawString(x, y_top + 4, "Dates:")

    # Match the relative Excel proportions: B:P narrative box, a gap, R:S
    # swatch stack, another gap, then black text labels.
    box_x = x
    box_w = w * 0.56
    box_top = y_top - 2
    box_h = h
    box_y = box_top - box_h
    c.setLineWidth(1.8)
    c.setStrokeColor(colors.black)
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    # Narrative order. R&D and Travel/Prep appear only when used by the schedule.
    order: List[str] = []
    for key in ["rd", "pre", "travel", "production", "hiatus", "post", "print_ship"]:
        if key in present:
            order.append(key)
    order.append("ready")

    # Keep Ready for Release inside the box for both compact and expanded cases.
    # If all optional rows are used, the fallback reduces font/spacing just enough
    # to keep the final line above the bottom border.
    row_count = max(1, len(order))
    if row_count <= 5:
        font_size = 8.5
        metric_gap = 10.0
    elif row_count == 6:
        font_size = 8.1
        metric_gap = 9.0
    else:
        font_size = 7.4
        metric_gap = 7.3

    top_pad = 13.0
    bottom_pad = 12.0
    usable = max(10.0, box_h - top_pad - bottom_pad)
    step = usable / max(1, row_count - 1)
    # Avoid overly wide spacing when only a few rows exist, but never let the
    # final row drift below the border.
    step = min(step, 17.0)
    y_positions: Dict[str, float] = {}
    first_y = box_top - top_pad
    for i, key in enumerate(order):
        y_positions[key] = first_y - i * step

    left_text_x = box_x + 4
    metric_x = box_x + box_w - 66
    for key in order:
        text = _date_line(key, recs.get(key, {}), schedule.get("ready") or {})
        if not text:
            continue
        ty = y_positions.get(key, first_y)
        # Clamp every baseline into the box, leaving enough room for descenders.
        ty = max(box_y + 10, min(ty, box_top - 10))
        if key == "print_ship":
            c.setFont("Helvetica-Oblique", font_size)
        elif key == "ready":
            c.setFont("Helvetica-Bold", font_size)
        else:
            c.setFont("Helvetica", font_size)
        c.setFillColor(colors.black)
        c.drawString(left_text_x, ty, text)

        metric = _metric_text(key, recs.get(key, {}))
        if metric:
            c.setFont("Helvetica-Bold", font_size)
            parts = [p for p in metric.split("\n") if p]
            for j, part in enumerate(parts[:2]):
                c.drawCentredString(metric_x + 33, ty - j * metric_gap, part)

    c.setFont("Helvetica-Bold", 8.6)
    c.setFillColor(colors.black)
    c.drawString(x, box_y - 13, "Notes:")

    legend_items: List[Tuple[str, str]] = []
    for key in ["rd", "pre", "travel"]:
        if key in present:
            legend_items.append((key, PERIOD_LABELS[key]))
    if "production" in present:
        legend_items.append(("production", PERIOD_LABELS["production"]))
        legend_items.append(("hiatus", "Holidays / Hiatus"))
    elif "hiatus" in present:
        legend_items.append(("hiatus", "Holidays / Hiatus"))
    for key in ["post", "print_ship"]:
        if key in present:
            legend_items.append((key, PERIOD_LABELS[key]))

    lx = box_x + box_w + 27
    ly = box_top - 17
    sw_w = 42
    # The swatches are drawn as stacked two-cell-like boxes with thick borders.
    sw_h = min(16.0, max(11.5, (box_h - 4) / max(1, len(legend_items))))
    label_font = 8.3 if len(legend_items) <= 5 else 7.4
    for key, label in legend_items[:7]:
        c.setFillColor(_hex(PERIOD_COLORS[key]))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.8)
        c.rect(lx, ly - 4, sw_w, sw_h, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", label_font)
        c.drawString(lx + sw_w + 26, ly, label)
        ly -= sw_h

def _generate_reportlab_pdf(payload: Dict[str, Any], out_pdf: Path) -> Path:
    """Native PDF fallback: no Excel app, no visible .xlsx side effect."""
    out_pdf = Path(out_pdf)
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except Exception as exc:
        raise RuntimeError(
            "PDF export requires LibreOffice or the Python reportlab package. "
            "Install dependencies by running: python3 -m pip install -r requirements.txt"
        ) from exc

    schedule = calculate_schedule(payload)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=landscape(letter))
    width, height = landscape(letter)

    project = schedule.get("projectTitle") or "Feature Film"
    ready_date = _parse_iso((schedule.get("ready") or {}).get("date"))
    as_of = parse_date(payload.get("asOfDate") or payload.get("as_of") or payload.get("asOf")) or date.today()
    recs = _period_records(schedule)
    shoot_days = ((recs.get("production") or {}).get("metric") or {}).get("value") or ""
    post_weeks = ((recs.get("post") or {}).get("metric") or {}).get("value") or ""

    for year in schedule.get("years") or [date.today().year]:
        c.setFillColor(colors.white)
        c.rect(0, 0, width, height, stroke=0, fill=1)
        left = 22
        top = height - 24
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        ready_text = _ordinal(ready_date) if ready_date else ""
        c.drawString(left, top, f"{project}, Ready for Release {ready_text} as of {as_of.strftime('%-m/%-d/%y') if hasattr(as_of, 'strftime') else as_of}")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left, top - 15, f"Assumes {shoot_days} Shoot Days; {post_weeks} Workweek Post")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, top - 31, f"JANUARY - DECEMBER   {year}")

        grid_top = top - 44
        month_w = (width - 2 * left - 24) / 4
        month_h = 112
        gap_x = 8
        gap_y = 11
        for m in range(1, 13):
            row = (m - 1) // 4
            col = (m - 1) % 4
            x = left + col * (month_w + gap_x)
            y_top = grid_top - row * (month_h + gap_y)
            _draw_month(c, year, m, x, y_top, month_w, month_h, schedule)

        _draw_bottom_box(c, left, 154, width - 2 * left, 108, schedule)
        c.showPage()
    c.save()
    return out_pdf


def create_pdf(payload: Dict[str, Any], out_path: str | Path) -> Path:
    """Create a PDF and never return a temporary XLSX.

    Preferred path: convert the generated reference-format XLSX with LibreOffice.
    Safe fallback: native ReportLab PDF. Microsoft Excel automation is not used
    because on some Macs it opens a temporary workbook/save dialog instead of
    returning a clean PDF download.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="producer_calendar_xlsx_for_pdf_") as td:
        xlsx_path = Path(td) / f"{out_path.stem}.xlsx"
        try:
            create_workbook(payload, xlsx_path)
            _hide_non_calendar_sheets_for_pdf(xlsx_path)
            if _convert_with_libreoffice(xlsx_path, out_path):
                return out_path
        except Exception:
            # If conversion fails for any reason, fall through to the safe native
            # PDF path rather than surfacing a temp XLSX to the user.
            pass

    # Guaranteed PDF-only fallback. It will not open Excel and will not save an
    # .xlsx file to the user's temp folder.
    return _generate_reportlab_pdf(payload, out_path)


if __name__ == "__main__":
    sample = {
        "projectTitle": "THE COMEBACKER",
        "productionLocation": "US",
        "anchorMode": "production",
        "asOfDate": "04/13/26",
        "periods": {
            "rd": {"start": "", "weeks": 0},
            "pre": {"start": "", "weeks": 12},
            "travel": {"start": "", "weeks": 0},
            "production": {"start": "10/05/26", "days": 40},
            "hiatus": {"start": "", "end": ""},
            "post": {"start": "", "weeks": 24},
            "print_ship": {"start": "", "weeks": 4},
            "ready": {"date": "06/18/27"},
        },
    }
    create_pdf(sample, Path(__file__).resolve().parent / "exports" / "sample_calendar_reference.pdf")
