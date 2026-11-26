import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from app.database.session import get_db
from app.authentication.security import current_user
from app.models import *
from app.algorithms.problem import DAY_NAMES
from app.services.access import get_version_or_404, scoped_entries, serialize_entries

router = APIRouter(prefix="/export", tags=["export"])

def _grids(db, user, vid, section_id=None):
    v = get_version_or_404(db, user, vid)
    rows = serialize_entries(db, scoped_entries(db, user, vid, section_id=section_id))
    slots = db.query(TimeSlot).order_by(TimeSlot.period).all()
    days = max((s.day for s in slots), default=4) + 1
    periods = {s.period: f"{s.start_time}-{s.end_time}" for s in slots}
    faculty_view = user.role == "faculty"
    groups = {}
    for r in rows: groups.setdefault("My timetable" if faculty_view else r["section"], []).append(r)
    out = {}
    for title, rs in sorted(groups.items()):
        grid = {(p, d): "" for p in periods for d in range(days)}
        for r in rs:
            for k in range(r["duration"]):
                lab = " [LAB]" if r["is_lab"] else ""
                txt = f"{r['subject']}{lab}\n{r['section'] if faculty_view else r['faculty']}\n{r['room']}"
                grid[(r["period"] + k, r["day"])] = txt if k == 0 else "(contd.)"
        out[title] = grid
    return v, out, periods, days

@router.get("/timetable/{vid}/excel")
def excel(vid: int, section_id: int | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v, grids, periods, days = _grids(db, user, vid, section_id)
    if not grids: raise HTTPException(404, "Nothing to export")
    wb = Workbook(); wb.remove(wb.active)
    for title, grid in grids.items():
        ws = wb.create_sheet(title[:31].replace("/", "-"))
        ws.append(["Period"] + DAY_NAMES[:days])
        for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1E3A8A")
        for p, t in periods.items(): ws.append([f"P{p + 1} ({t})"] + [grid[(p, d)] for d in range(days)])
        for row in ws.iter_rows(min_row=2):
            for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions["A"].width = 18
        for i in range(days): ws.column_dimensions[chr(66 + i)].width = 26
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="timetable_{vid}.xlsx"'})

@router.get("/timetable/{vid}/pdf")
def pdf(vid: int, section_id: int | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    v, grids, periods, days = _grids(db, user, vid, section_id)
    if not grids: raise HTTPException(404, "Nothing to export")
    buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    st = getSampleStyleSheet(); cell = st["BodyText"]; cell.fontSize = 7; cell.leading = 8.5
    story = []
    for n, (title, grid) in enumerate(grids.items()):
        if n: story.append(PageBreak())
        story += [Paragraph(f"{v.name} – {title}", st["Title"]), Spacer(1, 6)]
        data = [["Period"] + DAY_NAMES[:days]]
        for p, t in periods.items():
            data.append([Paragraph(f"P{p + 1}<br/>{t}", cell)] + [Paragraph(grid[(p, d)].replace("\n", "<br/>").replace("&", "&amp;"), cell) for d in range(days)])
        t = Table(data, colWidths=[70] + [(landscape(A4)[0] - 48 - 70) / days] * days, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")])]))
        story.append(t)
    doc.build(story); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="timetable_{vid}.pdf"'})
