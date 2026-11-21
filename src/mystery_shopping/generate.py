"""Generate SYNTHETIC mystery-shopper observations. No real visits, staff, customers or results.

The behaviour of each channel is driven by documented assumptions (docs/synthetic_data_design.md),
so the analysis can be checked against known patterns. Errors are injected afterwards so the
cleaning step has realistic problems to solve.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import framework as F

VISITS_PER_CHANNEL_WAVE = 60
SHOPPERS = [f"MS{i:02d}" for i in range(1, 9)]

# Latent service quality on a logit scale (assumptions)
CHANNEL_EFFECT = {"Email": 2.2, "Telephone": 2.0, "Social media": 1.5, "Registry": 2.6, "Ancillary services": 1.7}
WAVE_EFFECT = {"Wave 1": 0.0, "Wave 2": 0.25}  # modest improvement between waves
DIMENSION_EFFECT = {"Response time": -0.2, "Communication quality": 0.4, "Professionalism": 0.9,
                    "Information accuracy": -0.1, "Resolution effectiveness": -0.4, "Customer experience": 0.1}
# Channel-specific weak spots (assumptions) so the gap analysis has something to find
CHANNEL_DIMENSION = {("Social media", "Response time"): -0.9, ("Ancillary services", "Information accuracy"): -0.8,
                     ("Telephone", "Resolution effectiveness"): -0.5, ("Email", "Communication quality"): 0.3}
SHOPPER_BIAS = {s: 0.0 for s in SHOPPERS} | {"MS03": 0.9, "MS07": -0.6}  # one lenient and one strict assessor
AFTERNOON_EFFECT = -0.3
VISIT_SD = 0.6

# Typical response times (minutes) as log-normal medians, and how often the standard is breached
RT_MEDIAN = {"Email": 900, "Telephone": 0.8, "Social media": 200, "Registry": 9, "Ancillary services": 16}
RT_SIGMA = {"Email": 0.8, "Telephone": 0.9, "Social media": 0.9, "Registry": 0.6, "Ancillary services": 0.7}

POS = ["Staff member was courteous and explained the steps clearly.", "Correct fee and document list provided first time.",
       "Quick, helpful response with a link to the right e-service.", "Counter staff checked the documents carefully and issued a receipt."]
NEG = ["Information on required documents was incomplete.", "Had to wait well beyond the expected time.",
       "Answer did not match the published procedure on the website.", "Enquiry was not resolved and no next step was given.",
       "Response was only available in one language.", "Agent could not transfer the call to the right department."]


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate_clean(seed: int = F.SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    vid = 0
    start = {"Wave 1": pd.Timestamp("2025-02-02"), "Wave 2": pd.Timestamp("2025-08-03")}
    for wave in F.WAVES:
        for ch in F.CHANNELS:
            for _ in range(VISITS_PER_CHANNEL_WAVE):
                vid += 1
                shopper = str(rng.choice(SHOPPERS))
                afternoon = rng.random() < 0.45
                visit_q = rng.normal(0, VISIT_SD)
                base = CHANNEL_EFFECT[ch] + WAVE_EFFECT[wave] + SHOPPER_BIAS[shopper] + (AFTERNOON_EFFECT if afternoon else 0) + visit_q
                day = start[wave] + pd.Timedelta(days=int(rng.integers(0, 60)))
                while day.weekday() >= 5:  # Mon-Fri working days
                    day += pd.Timedelta(days=1)
                rt = float(np.round(rng.lognormal(np.log(RT_MEDIAN[ch]), RT_SIGMA[ch]) * np.exp(-0.3 * visit_q), 1))
                row = {"visit_id": f"V{vid:04d}", "wave": wave, "visit_date": day.strftime("%Y-%m-%d"), "channel": ch,
                       "scenario": str(rng.choice(F.SCENARIOS[ch])), "shopper_id": shopper,
                       "time_of_day": "Afternoon" if afternoon else "Morning", "response_time_min": rt}
                for cid, dim, _, chans in F.CRITERIA:
                    if ch not in chans:
                        row[cid] = np.nan
                        continue
                    if cid == "RT1":  # driven by the measured response time against the standard
                        row[cid] = 2 if rt <= F.RESPONSE_STANDARD_MIN[ch] else (1 if rt <= 1.5 * F.RESPONSE_STANDARD_MIN[ch] else 0)
                        continue
                    logit = base + DIMENSION_EFFECT[dim] + CHANNEL_DIMENSION.get((ch, dim), 0)
                    p_yes, p_part = _sigmoid(logit), _sigmoid(logit - 1.6)
                    u = rng.random()
                    row[cid] = 2 if u < p_part else (1 if u < p_yes else 0)
                score_share = np.nanmean([row[c[0]] for c in F.CRITERIA if ch in c[3]]) / 2
                row["likelihood_to_recommend"] = int(np.clip(np.round(rng.normal(2 + 8.3 * score_share, 1.3)), 0, 10))
                row["observation"] = str(rng.choice(POS if score_share > 0.75 else NEG))
                rows.append(row)
    return pd.DataFrame(rows)


def inject_errors(df: pd.DataFrame, seed: int = F.SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    out = df.copy().astype(object)
    n = len(out)
    pick = lambda frac: rng.choice(n, size=max(1, int(n * frac)), replace=False)  # noqa: E731
    variants = {"Email": ["email", "E-mail"], "Telephone": ["Phone", "telephone"], "Social media": ["Social Media", "Twitter/X"],
                "Registry": ["registry", "Registry counter"], "Ancillary services": ["Ancillary", "ancillary services"]}
    for i in pick(0.05):
        out.at[i, "channel"] = str(rng.choice(variants[out.at[i, "channel"]]))
    crit_cols = [c[0] for c in F.CRITERIA]
    for i in pick(0.02):
        col = str(rng.choice(crit_cols))
        if not pd.isna(out.at[i, col]):
            out.at[i, col] = rng.choice([3, -1, "Y", "n/a"])
    for i in pick(0.01):
        out.at[i, "response_time_min"] = rng.choice([-5, "", "approx 10"])
    for i in pick(0.015):
        out.at[i, "visit_date"] = pd.Timestamp(out.at[i, "visit_date"]).strftime("%d/%m/%Y")
    for i in pick(0.005):
        out.at[i, "shopper_id"] = ""
    for i in pick(0.006):
        out.at[i, "likelihood_to_recommend"] = rng.choice([11, -2, ""])
    dupes = out.iloc[pick(0.01)]
    return pd.concat([out, dupes], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> None:
    F.DATA_RAW.parent.mkdir(parents=True, exist_ok=True)
    raw = inject_errors(generate_clean())
    raw.to_csv(F.DATA_RAW, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(raw):,} synthetic observation rows to {F.DATA_RAW.relative_to(F.ROOT)}")


if __name__ == "__main__":
    main()
