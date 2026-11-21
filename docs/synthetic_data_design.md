# Synthetic data design

**Every observation in this repository is synthetic.** It comes from [`generate.py`](../src/mystery_shopping/generate.py) with seed `2025`. It is not derived from any real mystery-shopping programme, organisation, staff member, customer, email, social-media post or call recording.

## How a visit is generated

- **Volume:** 60 visits per channel per wave × 5 channels × 2 waves = 600 visits, on weekdays, with 8 assessors (`MS01`-`MS08`).
- **Quality model:** each criterion's probability of "Yes" (2) or "Partly" (1) comes from a latent quality score on a logit scale:

```
quality = channel effect + wave effect + assessor bias + afternoon effect + dimension effect
          + channel × dimension weak spot + visit-level noise
```

| Assumption | Value (logit points) |
|---|---|
| Channel effect | Registry 2.6 · Email 2.2 · Telephone 2.0 · Ancillary services 1.7 · Social media 1.5 |
| Wave 2 vs Wave 1 | +0.25 (modest improvement) |
| Dimension effect | Professionalism +0.9 · Communication +0.4 · Customer experience +0.1 · Accuracy −0.1 · Response time −0.2 · Resolution −0.4 |
| Built-in weak spots | Social media / response time −0.9 · Ancillary / information accuracy −0.8 · Telephone / resolution −0.5 |
| Assessor bias | MS03 +0.9 (lenient) · MS07 −0.6 (strict) · others 0 |
| Afternoon visits | −0.3 |

- **Response times** are log-normal per channel, and criterion RT1 is scored from the measured time against the channel standard.
- **Likelihood to recommend** (0-10) follows the share of criteria met, plus noise.
- **Data-quality problems** are injected afterwards: channel spelling variants (5%), invalid scores (2% of rows), bad response times (1%), dd/mm/yyyy dates (1.5%), missing assessor IDs (0.5%), invalid recommendation scores (0.6%) and duplicate rows (1%).

Because the patterns are known, the analysis can be checked. It should recover the registry > ancillary gap, the social-media response-time problem and the two biased assessors, and the tests confirm that it does.
