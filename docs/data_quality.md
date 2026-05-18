# Data Quality

The platform intentionally generates imperfect source data:

- duplicate IDs
- missing foreign keys
- invalid payment status
- negative product cost
- negative item quantity
- late web event

Quality outputs:

| Output | Purpose |
| --- | --- |
| `contract_issues.csv` | Row-level contract failures. |
| `rejected_rows.csv` | Records rejected from bronze clean outputs. |
| `contract_summary.csv` | Quality score by source table. |
| `quality_checks.csv` | Platform-level rule results. |
| `platform_scorecard.csv` | Overall pass/fail score. |
| `data_quality_report.md` | Markdown report for review. |

Run:

```bash
commerce-platform run-quality --profile ci
```
