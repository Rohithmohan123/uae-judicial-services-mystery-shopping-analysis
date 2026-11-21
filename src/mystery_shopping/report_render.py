"""Render the evaluation report (Markdown + PDF) from computed results."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from . import framework as A

TITLE = "Mystery Shopper Evaluation Report: Judicial Services Customer Experience"
SUBTITLE = "Anonymised, independent demonstration of mystery-shopping and service-quality research methods (synthetic data)"
# ---------------------------------------------------------------------------- Markdown

def _md_table(df: pd.DataFrame) -> str:
    d = df.copy()
    for c in d.columns:
        if d[c].dtype == bool:
            d[c] = d[c].map({True: "yes", False: "no"})
    header = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "|".join("---" for _ in d.columns) + "|"
    rows = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join([header, sep, *rows])


def _md_text(s: str) -> str:
    return (s.replace("<b>", "**").replace("</b>", "**").replace("<sub>", "").replace("</sub>", "")
            .replace("<super>2</super>", "²").replace("<super>", "^").replace("</super>", ""))


def to_markdown(blocks: list[tuple], path: Path) -> None:
    out = [f"# {TITLE}", f"*{SUBTITLE}*", "", f"Generated {date.today():%d %B %Y} by `run_pipeline.py`.", ""]
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            out += ["", f"## {b[1]}", ""]
        elif kind == "p":
            out += [_md_text(b[1]), ""]
        elif kind == "bullets":
            out += [f"- {_md_text(x)}" for x in b[1]] + [""]
        elif kind == "table":
            out += [_md_table(b[1]), ""]
        elif kind == "img":
            rel = Path("..") / Path(b[1]).relative_to(A.ROOT)
            out += [f"![{Path(b[1]).stem}]({rel.as_posix()})", ""]
    path.write_text("\n".join(out), encoding="utf-8")


# ---------------------------------------------------------------------------- PDF

INK, MUTED, LINE, ACCENT = colors.HexColor("#0b0b0b"), colors.HexColor("#6b6a66"), colors.HexColor("#e1e0d9"), colors.HexColor("#2a78d6")


def _styles():
    ss = getSampleStyleSheet()
    base = ParagraphStyle("base", parent=ss["Normal"], fontName="Helvetica", fontSize=9.6, leading=13.6, textColor=INK, alignment=TA_LEFT, spaceAfter=6)
    return {
        "title": ParagraphStyle("title", parent=base, fontName="Helvetica-Bold", fontSize=21, leading=25, spaceAfter=8),
        "subtitle": ParagraphStyle("subtitle", parent=base, fontSize=11, leading=15, textColor=MUTED, spaceAfter=18),
        "h1": ParagraphStyle("h1", parent=base, fontName="Helvetica-Bold", fontSize=14, leading=18, spaceBefore=12, spaceAfter=8, textColor=INK),
        "p": base,
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=12, bulletIndent=2, spaceAfter=4),
        "cell": ParagraphStyle("cell", parent=base, fontSize=7.6, leading=9.6, spaceAfter=0),
        "cellh": ParagraphStyle("cellh", parent=base, fontName="Helvetica-Bold", fontSize=7.6, leading=9.6, spaceAfter=0, textColor=MUTED),
        "box": ParagraphStyle("box", parent=base, fontSize=9, leading=12.5, textColor=colors.HexColor("#52514e")),
    }


def _pdf_table(df: pd.DataFrame, st, widths_cm: list[float] | None, avail: float) -> Table:
    d = df.copy()
    for c in d.columns:
        if d[c].dtype == bool:
            d[c] = d[c].map({True: "yes", False: "no"})
    data = [[Paragraph(str(c), st["cellh"]) for c in d.columns]]
    data += [[Paragraph("" if pd.isna(v) else str(v), st["cell"]) for v in r] for r in d.itertuples(index=False)]
    widths = [w * cm for w in widths_cm] if widths_cm else [avail / len(d.columns)] * len(d.columns)
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#c3c2b7")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, "SYNTHETIC data. Not an official or authorised publication of any court or judicial entity.")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def to_pdf(blocks: list[tuple], path: Path) -> None:
    st = _styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title=TITLE, author="Rohith Mohan", subject="Mystery shopping methodology demonstration (synthetic)")
    avail = A4[0] - 4 * cm
    story = [Paragraph(TITLE, st["title"]), Paragraph(SUBTITLE, st["subtitle"]),
             Paragraph(f"Generated {date.today():%d %B %Y}. All observations, scores and findings are synthetic. Code, data and tables: see the repository README.", st["box"]), Spacer(1, 8)]
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            story.append(Paragraph(b[1], st["h1"]))
        elif kind == "p":
            story.append(Paragraph(b[1], st["p"]))
        elif kind == "bullets":
            story += [Paragraph(x, st["bullet"], bulletText="•") for x in b[1]]
            story.append(Spacer(1, 4))
        elif kind == "table":
            story += [_pdf_table(b[1], st, b[2], avail), Spacer(1, 10)]
        elif kind == "img":
            from PIL import Image as PILImage
            with PILImage.open(b[1]) as im:
                w, h = im.size
            width = avail
            max_h = 10.5 * cm
            if width * h / w > max_h:
                width = max_h * w / h
            story.append(KeepTogether([Image(str(b[1]), width=width, height=width * h / w), Spacer(1, 8)]))
        elif kind == "pagebreak":
            story.append(PageBreak())
    doc.build(story, onFirstPage=_page, onLaterPages=_page)


