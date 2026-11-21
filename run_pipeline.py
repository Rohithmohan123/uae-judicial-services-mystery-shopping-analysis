"""Full pipeline: synthetic observations -> cleaning & scoring -> analysis, charts, scorecards -> templates, Power BI model -> PDF report.

Usage:
    python run_pipeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mystery_shopping import analysis, clean_score, deliverables, generate, report  # noqa: E402


def main() -> None:
    print("1/5 Generating synthetic mystery-shopper observations")
    generate.main()
    print("2/5 Cleaning, validating and scoring")
    clean_score.main()
    print("3/5 Analysis, charts and channel scorecards")
    results = analysis.run()
    print("4/5 Questionnaire templates, Excel scorecard and Power BI model")
    deliverables.questionnaires()
    deliverables.scorecard_workbook(results)
    deliverables.powerbi_model(results)
    print("5/5 Writing the evaluation report")
    md, pdf = report.write_reports(results)
    print(f"Done: reports/{pdf.name}")


if __name__ == "__main__":
    main()
