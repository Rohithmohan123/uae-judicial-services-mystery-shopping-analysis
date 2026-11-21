# Power BI dashboard (optional)

The pipeline writes a star schema to this folder. Load it into Power BI Desktop to build an interactive dashboard. No `.pbix` file is included, because Power BI Desktop is Windows-only and binary files are hard to review in Git.

| Table | Grain | Key columns |
|---|---|---|
| `fact_visit.csv` | One row per synthetic visit | `visit_id`, `visit_date`, `channel_key`, `sqi`, `score_*`, `response_time_min`, `likelihood_to_recommend` |
| `fact_criterion_score.csv` | One row per visit × criterion | `visit_id`, `criterion`, `score` (0/1/2) |
| `dim_channel.csv` | Channel | `channel_key`, `channel`, `channel_group`, `response_standard_min` |
| `dim_criterion.csv` | Criterion | `criterion`, `dimension`, `question`, `dimension_weight` |
| `dim_date.csv` | Calendar day | `date`, `year`, `month`, `weekday` |

**Relationships:** `fact_visit[channel_key]` → `dim_channel[channel_key]` · `fact_visit[visit_date]` → `dim_date[date]` · `fact_criterion_score[visit_id]` → `fact_visit[visit_id]` · `fact_criterion_score[criterion]` → `dim_criterion[criterion]`

## Suggested DAX measures

```DAX
Visits = COUNTROWS ( fact_visit )
SQI = AVERAGE ( fact_visit[sqi] )
SQI vs Target = [SQI] - 80
Response Standard Met % = DIVIDE ( CALCULATE ( [Visits], fact_visit[meets_response_standard] = TRUE () ), [Visits] )
Full Pass % = DIVIDE ( CALCULATE ( COUNTROWS ( fact_criterion_score ), fact_criterion_score[score] = 2 ), COUNTROWS ( fact_criterion_score ) )
Critical Visits % = DIVIDE ( CALCULATE ( [Visits], fact_visit[sqi] < 60 ), [Visits] )
NPS (demo) =
VAR n = CALCULATE ( [Visits], NOT ISBLANK ( fact_visit[likelihood_to_recommend] ) )
VAR p = CALCULATE ( [Visits], fact_visit[likelihood_to_recommend] >= 9 )
VAR d = CALCULATE ( [Visits], fact_visit[likelihood_to_recommend] <= 6 )
RETURN DIVIDE ( p - d, n ) * 100
```

**Suggested pages:** (1) Overview KPI cards and SQI by channel; (2) channel × dimension matrix with conditional formatting; (3) registry vs ancillary comparison; (4) wave trend and assessor calibration; (5) criterion drill-through using `fact_criterion_score`.

All data is synthetic.
