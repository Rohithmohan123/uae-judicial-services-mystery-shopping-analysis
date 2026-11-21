"""Clean, validate and score the observations.

Scoring: each criterion is 0 (No) / 1 (Partly) / 2 (Yes). A dimension score is the mean of its
applicable criteria, rescaled to 0-100. The Service Quality Index (SQI) is the weighted mean of the
dimension scores (weights in framework.py), re-normalised over the dimensions that apply.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import framework as F

CHANNEL_ALIASES = {"email": "Email", "e-mail": "Email", "telephone": "Telephone", "phone": "Telephone",
                   "social media": "Social media", "twitter/x": "Social media", "registry": "Registry", "registry counter": "Registry",
                   "ancillary services": "Ancillary services", "ancillary": "Ancillary services"}
CRIT = [c[0] for c in F.CRITERIA]


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    log = []
    rec = lambda rule, n, action: log.append({"rule": rule, "rows_affected": int(n), "action": action})  # noqa: E731
    df = raw.copy()
    rec("Rows in raw file", len(df), "-")
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype("string").str.strip()
    d = df.duplicated()
    rec("Exact duplicate rows", d.sum(), "dropped")
    df = df[~d]
    d = df.duplicated("visit_id")
    rec("Repeated visit_id", d.sum(), "dropped, first kept")
    df = df[~d]
    mapped = df["channel"].str.lower().map(CHANNEL_ALIASES)
    rec("Channel spelling variants standardised", (mapped.notna() & (mapped != df["channel"])).sum(), "recoded")
    rec("Unrecognised channel", mapped.isna().sum(), "dropped")
    df = df.assign(channel=mapped)[mapped.notna()]
    no_shopper = df["shopper_id"].isna() | (df["shopper_id"] == "")
    rec("Missing shopper_id", no_shopper.sum(), "dropped (assessor must be traceable)")
    df = df[~no_shopper]

    bad_cells = 0
    for c in CRIT:
        v = pd.to_numeric(df[c], errors="coerce")
        invalid = df[c].notna() & (df[c] != "") & ~v.isin([0, 1, 2])
        bad_cells += int(invalid.sum())
        df[c] = v.where(v.isin([0, 1, 2]))
    rec("Invalid criterion scores (not 0/1/2)", bad_cells, "set to missing (cell-level)")
    # A criterion that does not apply to the channel must stay empty
    for cid, _, _, chans in F.CRITERIA:
        df.loc[~df["channel"].isin(chans), cid] = np.nan

    rt = pd.to_numeric(df["response_time_min"], errors="coerce")
    bad = rt.isna() | (rt < 0)
    rec("Response time missing, negative or text", bad.sum(), "set to missing; RT1 left as recorded")
    df["response_time_min"] = rt.mask(rt < 0)

    iso = pd.to_datetime(df["visit_date"], format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(df["visit_date"], format="%d/%m/%Y", errors="coerce")
    rec("Visit date in dd/mm/yyyy format", (iso.isna() & dmy.notna()).sum(), "converted to ISO")
    df["visit_date"] = iso.fillna(dmy)

    ltr = pd.to_numeric(df["likelihood_to_recommend"], errors="coerce")
    bad = ltr.isna() | ~ltr.between(0, 10)
    rec("Likelihood-to-recommend missing or outside 0-10", bad.sum(), "set to missing, excluded from NPS only")
    df["likelihood_to_recommend"] = ltr.where(ltr.between(0, 10)).astype("Int64")
    rec("Rows in clean dataset", len(df), "-")
    return df.sort_values("visit_id").reset_index(drop=True), pd.DataFrame(log)


def score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for dim in F.DIMENSIONS:
        cols = [c[0] for c in F.CRITERIA if c[1] == dim]
        out[f"score_{dim}"] = out[cols].mean(axis=1, skipna=True) / 2 * 100
    w = pd.Series(F.DIMENSION_WEIGHTS)
    dims = out[[f"score_{d}" for d in F.DIMENSIONS]].to_numpy(dtype=float)
    weights = np.where(np.isnan(dims), 0, w.reindex(F.DIMENSIONS).to_numpy())
    out["sqi"] = np.nansum(np.nan_to_num(dims) * weights, axis=1) / weights.sum(axis=1)
    out["meets_response_standard"] = out["response_time_min"] <= out["channel"].map(F.RESPONSE_STANDARD_MIN)
    out["nps_segment"] = pd.cut(out["likelihood_to_recommend"].astype(float), [-1, 6, 8, 10], labels=["Detractor", "Passive", "Promoter"])
    return out


def validate(df: pd.DataFrame) -> list[str]:
    problems = []
    if df["visit_id"].duplicated().any():
        problems.append("duplicate visit_id")
    if not set(df["channel"]).issubset(F.CHANNELS):
        problems.append("unknown channel")
    vals = pd.unique(df[CRIT].to_numpy().ravel())
    if not set(v for v in vals if not pd.isna(v)).issubset({0, 1, 2}):
        problems.append("criterion score outside 0/1/2")
    if df["sqi"].dropna().between(0, 100).all() is False:
        problems.append("SQI outside 0-100")
    return problems


def main() -> None:
    raw = pd.read_csv(F.DATA_RAW, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
    df, log = clean(raw)
    df = score(df)
    problems = validate(df)
    if problems:
        raise SystemExit(f"Validation failed: {problems}")
    F.DATA_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(F.DATA_CLEAN, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    log.to_csv(F.CLEANING_LOG, index=False)
    print(log.to_string(index=False))


if __name__ == "__main__":
    main()
