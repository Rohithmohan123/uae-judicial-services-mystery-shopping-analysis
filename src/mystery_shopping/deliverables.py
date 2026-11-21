"""Write the questionnaire templates (Excel + Markdown), the Excel scorecard workbook and a Power BI-ready star schema."""
from __future__ import annotations

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from . import framework as F

HEADER = PatternFill("solid", fgColor="1F3A5F")
WHITE = Font(color="FFFFFF", bold=True)
GUIDANCE = {
    "RT1": "2 = within standard; 1 = within 1.5× standard; 0 = slower. Record the measured time.",
    "IA1": "Compare against the published procedure checked before the visit; note discrepancies.",
    "PR3": "Staff must not give legal advice; signposting to official guidance is correct behaviour.",
    "RE1": "2 = fully resolved; 1 = partly resolved; 0 = not resolved.",
}


def questionnaires() -> None:
    F.TEMPLATES.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    cover = wb.create_sheet("How to use")
    lines = ["Mystery shopping evaluation templates (independent, generic framework)",
             "One sheet per channel. Complete one row of scores per visit, or copy the sheet per visit.",
             "Scoring: 2 = Yes / fully met, 1 = Partly met, 0 = No / not met. Leave blank if not observed.",
             "Record response time in minutes using the channel's definition shown on each sheet.",
             "Do not record personal data about staff or real customers. Use role descriptions only.",
             "These templates are a demonstration and do not reproduce any organisation's internal forms."]
    for i, line in enumerate(lines, 1):
        cover.cell(i, 1, line).font = Font(bold=(i == 1), size=13 if i == 1 else 11)
    cover.column_dimensions["A"].width = 110
    md = ["# Mystery shopping questionnaires", "",
          "Scoring for every criterion: **2 = Yes / fully met · 1 = Partly met · 0 = No / not met**. Leave blank if not observed.", ""]
    for ch in F.CHANNELS:
        ws = wb.create_sheet(ch[:31])
        ws["A1"] = f"{ch}: evaluation questionnaire"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = (f"Visit details: Visit ID · Date · Shopper ID · Scenario (e.g. {F.SCENARIOS[ch][0]}) · Response time "
                    f"({F.RESPONSE_UNIT[ch]}; standard ≤ {F.RESPONSE_STANDARD_MIN[ch]} min)")
        heads = ["Criterion", "Dimension", "Question", "Score (0/1/2)", "Evidence / notes", "Scoring guidance"]
        for j, h in enumerate(heads, 1):
            c = ws.cell(4, j, h)
            c.fill, c.font = HEADER, WHITE
        dv = DataValidation(type="list", formula1='"0,1,2"', allow_blank=True)
        ws.add_data_validation(dv)
        md += [f"## {ch}", "", f"*Scenarios:* {', '.join(F.SCENARIOS[ch])}  ", f"*Response time:* {F.RESPONSE_UNIT[ch]} (illustrative standard ≤ {F.RESPONSE_STANDARD_MIN[ch]} min)", "",
               "| ID | Dimension | Question |", "|---|---|---|"]
        for i, (cid, dim, q, _) in enumerate(F.criteria_for(ch), 5):
            for j, v in enumerate([cid, dim, q, None, None, GUIDANCE.get(cid, "")], 1):
                ws.cell(i, j, v).alignment = Alignment(wrap_text=True, vertical="top")
            dv.add(ws.cell(i, 4))
            md.append(f"| {cid} | {dim} | {q} |")
        n = 4 + len(F.criteria_for(ch))
        ws.cell(n + 2, 1, "Likelihood to recommend (0-10):").font = Font(bold=True)
        ws.cell(n + 3, 1, "Overall observation (factual, no personal data):").font = Font(bold=True)
        for col, w in zip("ABCDEF", [10, 24, 70, 13, 40, 48]):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A5"
        md += ["", "Also record: likelihood to recommend (0-10) and a factual overall observation.", ""]
    wb.save(F.TEMPLATES / "mystery_shopping_questionnaires.xlsx")
    md += ["## Registry and ancillary services: additional criteria", "",
           "In-person channels also score **CQ4** (active listening), **PR2** (staff identification) and **RE3** (transaction completed correctly: documents accepted, receipt issued). "
           "Waiting time is measured from arrival or ticket issue to being served.", ""]
    (F.TEMPLATES / "questionnaires.md").write_text("\n".join(md), encoding="utf-8")


def scorecard_workbook(results: dict) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Channel scorecard"
    ws["A1"] = "Service quality scorecard: SYNTHETIC demonstration data"
    ws["A1"].font = Font(bold=True, size=14)
    ch = results["ch"]
    cols = ["channel", "visits", "sqi", "visits_meeting_target_pct", "response_standard_met_pct", "first_contact_resolution_pct", "sqi_cv_pct", "critical_visits_pct", "nps_demo"]
    labels = ["Channel", "Visits", "SQI (0-100)", "Visits ≥ target %", "Response standard met %", "First-contact resolution %", "Variability (CV %)", "Critical visits %", "NPS (demo)"]
    for j, h in enumerate(labels, 1):
        c = ws.cell(3, j, h)
        c.fill, c.font = HEADER, WHITE
    for i, r in enumerate(ch[cols].itertuples(index=False), 4):
        for j, v in enumerate(r, 1):
            ws.cell(i, j, v)
    last = 3 + len(ch)
    ws.conditional_formatting.add(f"C4:C{last}", CellIsRule(operator="greaterThanOrEqual", formula=[str(F.TARGET_SCORE)], fill=PatternFill("solid", fgColor="D8F0D8")))
    ws.conditional_formatting.add(f"C4:C{last}", CellIsRule(operator="lessThan", formula=[str(F.TARGET_SCORE)], fill=PatternFill("solid", fgColor="F8D7D7")))
    for j in range(1, len(labels) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 22 if j == 1 else 18
    ws2 = wb.create_sheet("Dimension heatmap")
    dims = results["dims"]
    ws2.cell(1, 1, "Channel").font = Font(bold=True)
    for j, d in enumerate(dims.columns, 2):
        ws2.cell(1, j, d).font = Font(bold=True)
        ws2.column_dimensions[get_column_letter(j)].width = 22
    for i, (c, row) in enumerate(dims.iterrows(), 2):
        ws2.cell(i, 1, c)
        for j, v in enumerate(row, 2):
            ws2.cell(i, j, float(v))
    ws2.column_dimensions["A"].width = 22
    ws2.conditional_formatting.add(f"B2:{get_column_letter(1 + dims.shape[1])}{1 + len(dims)}",
                                   ColorScaleRule(start_type="num", start_value=45, start_color="E06666", mid_type="num", mid_value=F.TARGET_SCORE, mid_color="F3F3F3", end_type="num", end_value=95, end_color="6FA8DC"))
    for name in ["04_registry_vs_ancillary", "05_wave_comparison", "06_shopper_calibration", "08_top_10_gaps"]:
        t = results["tables"][name]
        s = wb.create_sheet(name[3:][:31])
        for j, h in enumerate(t.columns, 1):
            c = s.cell(1, j, h)
            c.fill, c.font = HEADER, WHITE
            s.column_dimensions[get_column_letter(j)].width = 20
        for i, r in enumerate(t.itertuples(index=False), 2):
            for j, v in enumerate(r, 1):
                s.cell(i, j, v if not isinstance(v, (bool,)) else str(v))
    wb.save(F.TABLES / "service_quality_scorecard.xlsx")


def powerbi_model(results: dict) -> None:
    """Star schema CSVs for Power BI (or any BI tool) + DAX measures documented in powerbi/README.md."""
    F.POWERBI.mkdir(parents=True, exist_ok=True)
    df = results["df"]
    dim_channel = pd.DataFrame({"channel_key": range(1, len(F.CHANNELS) + 1), "channel": F.CHANNELS,
                                "channel_group": [F.CHANNEL_GROUP[c] for c in F.CHANNELS],
                                "response_standard_min": [F.RESPONSE_STANDARD_MIN[c] for c in F.CHANNELS]})
    key = dict(zip(dim_channel["channel"], dim_channel["channel_key"]))
    dim_criterion = pd.DataFrame([{"criterion": c, "dimension": d, "question": q, "dimension_weight": F.DIMENSION_WEIGHTS[d]} for c, d, q, _ in F.CRITERIA])
    dates = pd.date_range(df["visit_date"].min(), df["visit_date"].max())
    dim_date = pd.DataFrame({"date": dates.date, "year": dates.year, "month": dates.month, "month_name": dates.strftime("%b"), "weekday": dates.strftime("%a")})
    fact_visit = df[["visit_id", "visit_date", "wave", "channel", "scenario", "shopper_id", "time_of_day", "response_time_min",
                     "meets_response_standard", "likelihood_to_recommend", "sqi"] + [f"score_{d}" for d in F.DIMENSIONS]].copy()
    fact_visit.insert(4, "channel_key", fact_visit.pop("channel").map(key))
    fact_visit["visit_date"] = fact_visit["visit_date"].dt.date
    crit_cols = [c[0] for c in F.CRITERIA]
    fact_score = df.melt(id_vars=["visit_id"], value_vars=crit_cols, var_name="criterion", value_name="score").dropna()
    fact_score["score"] = fact_score["score"].astype(int)
    for name, t in {"dim_channel": dim_channel, "dim_criterion": dim_criterion, "dim_date": dim_date, "fact_visit": fact_visit, "fact_criterion_score": fact_score}.items():
        t.to_csv(F.POWERBI / f"{name}.csv", index=False, encoding="utf-8-sig")
