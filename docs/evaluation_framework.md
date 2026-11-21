# Mystery shopping evaluation framework

An independently designed, generic framework for evaluating customer service at a public-facing judicial services entity. It does not reproduce any client's internal framework, forms or standards.

## Channels and example scenarios

| Channel | Group | Example scenarios | Response-time measure (illustrative standard) |
|---|---|---|---|
| Email | Remote | Filing procedure, court fees, document requirements | Minutes to first reply (≤ 1 working day / 1,440 min) |
| Telephone | Remote | Hearing dates, fees, appeals, opening hours | Minutes until answered by a person (≤ 1 min) |
| Social media | Remote | General enquiries, e-services help, accessibility, complaints | Minutes to first reply (≤ 2 h) |
| Registry | In person | Document submission, certified copies, file inspection, fee payment | Waiting time before being served (≤ 15 min) |
| Ancillary services | In person | Translation, notarisation / attestation, mediation information, visitor support | Waiting time before being served (≤ 20 min) |

## Dimensions and weights

| Dimension | Weight | What it measures |
|---|---|---|
| Response time | 15% | Speed against the channel standard; whether timelines are communicated |
| Communication quality | 15% | Clarity, language choice (Arabic/English), structure, active listening |
| Professionalism | 15% | Courtesy, identification, impartiality (no legal advice) |
| Information accuracy | 25% | Correct, complete information and correct signposting |
| Resolution effectiveness | 20% | First-contact resolution, next steps, transaction completed correctly |
| Customer experience | 10% | Ease of use, accessibility, overall efficiency |

## Scoring

- Each criterion is scored **2** (fully met), **1** (partly met) or **0** (not met). Criteria that do not apply to a channel are left blank.
- **Dimension score** = mean of the applicable criteria ÷ 2 × 100.
- **Service Quality Index (SQI)** = weighted mean of the dimension scores, re-normalised over the dimensions present.
- **Target:** 80. **Critical visit:** SQI below 60.
- **Consistency:** standard deviation and coefficient of variation of visit SQI by channel, the share of critical visits, the wave-to-wave change, and an assessor calibration check (each assessor's residual against peers on the same channel and wave; flagged when |z| > 2.5).

The full question list per channel is in [`questionnaires/questionnaires.md`](../questionnaires/questionnaires.md) and the Excel template [`mystery_shopping_questionnaires.xlsx`](../questionnaires/mystery_shopping_questionnaires.xlsx).

## Ethics and confidentiality (for real programmes)

- Assess processes, not named individuals. Record roles, not names, and never record real customers.
- Get the client's authorisation before fieldwork. Follow call-recording and data-protection rules, and store evidence securely.
- Report findings to the commissioning client only. This repository contains synthetic data only.
