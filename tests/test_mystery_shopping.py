"""Tests for the framework, cleaning rules, scoring maths and analysis helpers."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mystery_shopping import analysis as AN  # noqa: E402
from mystery_shopping import clean_score as CS  # noqa: E402
from mystery_shopping import framework as F  # noqa: E402
from mystery_shopping import generate as G  # noqa: E402


def test_framework_weights_and_coverage():
    assert sum(F.DIMENSION_WEIGHTS.values()) == pytest.approx(1)
    assert set(F.DIMENSION_WEIGHTS) == set(F.DIMENSIONS)
    ids = [c[0] for c in F.CRITERIA]
    assert len(ids) == len(set(ids))
    for ch in F.CHANNELS:
        dims = {c[1] for c in F.criteria_for(ch)}
        assert dims == set(F.DIMENSIONS), f"{ch} must cover all six dimensions"


@pytest.fixture(scope="module")
def cleaned():
    raw = G.inject_errors(G.generate_clean(seed=11), seed=11).astype(str).replace({"nan": np.nan, "": np.nan})
    df, log = CS.clean(raw)
    return CS.score(df), log


def test_clean_output_valid(cleaned):
    df, _ = cleaned
    assert CS.validate(df) == []
    assert set(df["channel"]) == set(F.CHANNELS)
    assert df["shopper_id"].notna().all()


def test_cleaning_log_reconciles(cleaned):
    df, log = cleaned
    l = log.set_index("rule")
    dropped = l[l["action"].str.startswith("dropped")]["rows_affected"].sum()
    assert l.loc["Rows in raw file", "rows_affected"] - dropped == l.loc["Rows in clean dataset", "rows_affected"] == len(df)


def test_not_applicable_criteria_are_blank(cleaned):
    df, _ = cleaned
    assert df.loc[df["channel"] == "Telephone", "CQ3"].isna().all()   # written-response criterion
    assert df.loc[df["channel"] == "Email", "RE3"].isna().all()       # in-person transaction criterion


def test_scoring_maths():
    row = {c[0]: np.nan for c in F.CRITERIA}
    row.update({"visit_id": "X1", "channel": "Email", "response_time_min": 10.0, "likelihood_to_recommend": 9})
    for cid, _, _, chans in F.CRITERIA:
        if "Email" in chans:
            row[cid] = 2
    df = CS.score(pd.DataFrame([row]))
    assert df["sqi"].iloc[0] == pytest.approx(100)
    row2 = dict(row)
    for cid in ["IA1", "IA2", "IA3"]:
        row2[cid] = 0  # information accuracy fully failed
    df2 = CS.score(pd.DataFrame([row2]))
    assert df2["score_Information accuracy"].iloc[0] == 0
    assert df2["sqi"].iloc[0] == pytest.approx(100 * (1 - F.DIMENSION_WEIGHTS["Information accuracy"]))
    assert bool(df["meets_response_standard"].iloc[0]) is True


def test_nps_and_ci_helpers():
    assert AN.nps_value(pd.Series([10, 9, 8, 7, 6, 0])) == pytest.approx(100 * (2 / 6 - 2 / 6))
    m, lo, hi = AN.mean_ci(pd.Series([70, 80, 90]))
    assert lo < m == 80 < hi


def test_shopper_calibration_flags_biased_assessors(cleaned):
    df, _ = cleaned
    flags = AN.shopper_calibration(df).set_index("shopper_id")["flag"]
    assert flags["MS03"].startswith("Lenient") and flags["MS07"].startswith("Strict")


def test_generator_reproducible():
    pd.testing.assert_frame_equal(G.generate_clean(seed=3), G.generate_clean(seed=3))
