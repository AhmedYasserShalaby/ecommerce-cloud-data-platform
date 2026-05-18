from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from commerce_platform.gold import run_gold
from commerce_platform.paths import get_paths


def run_quality(profile: str = "ci", data_root: str | Path | None = None) -> dict[str, object]:
    paths = get_paths(data_root)
    run_gold(profile, paths.data_root)
    rules = _load_rules()
    checks = _evaluate_checks(paths, rules)
    scorecard = _scorecard(checks)
    report = _render_report(profile, checks, scorecard)
    checks.to_csv(paths.exports / "quality_checks.csv", index=False)
    scorecard.to_csv(paths.exports / "platform_scorecard.csv", index=False)
    (paths.exports / "data_quality_report.md").write_text(report, encoding="utf-8")
    return {
        "passed": int(checks["passed"].sum()),
        "failed": int((~checks["passed"]).sum()),
        "score": float(scorecard.iloc[0]["platform_score"]),
        "report_path": str(paths.exports / "data_quality_report.md"),
    }


def _load_rules(path: str | Path = "config/quality_rules.yml") -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _evaluate_checks(paths, rules: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    contract_summary = _read_csv(paths.exports / "contract_summary.csv")
    gold_manifest = _read_csv(paths.exports / "gold_manifest.csv")
    funnel = _read_csv(paths.exports / "mart_funnel_conversion.csv")
    fulfillment = _read_csv(paths.exports / "mart_fulfillment_sla.csv")
    revenue = _read_csv(paths.exports / "mart_revenue_daily.csv")

    min_quality = float(contract_summary["quality_score"].min()) if not contract_summary.empty else 0.0
    rows.append(
        _check(
            "contract_quality_floor",
            min_quality >= rules["minimum_contract_quality_score"],
            min_quality,
            f">= {rules['minimum_contract_quality_score']}",
        )
    )

    exported_files = {path.name for path in paths.exports.glob("*")}
    for export_name in rules["required_exports"]:
        rows.append(_check(f"required_export:{export_name}", export_name in exported_files, export_name, "present"))

    rows.append(
        _check(
            "gold_mart_count",
            len(gold_manifest) >= rules["minimum_gold_marts"],
            len(gold_manifest),
            f">= {rules['minimum_gold_marts']}",
        )
    )

    late_events = float(funnel["late_events"].sum()) if not funnel.empty else 0.0
    total_events = float(funnel["events"].sum()) if not funnel.empty else 1.0
    late_event_rate = late_events / total_events if total_events else 0.0
    rows.append(
        _check(
            "late_event_rate",
            late_event_rate <= rules["maximum_late_event_rate"],
            round(late_event_rate, 4),
            f"<= {rules['maximum_late_event_rate']}",
        )
    )

    revenue_total = float(revenue["revenue"].sum()) if not revenue.empty else 0.0
    rows.append(_check("positive_revenue", revenue_total > 0, round(revenue_total, 2), "> 0"))

    on_time_valid = fulfillment["on_time_rate"].between(0, 1).all() if not fulfillment.empty else False
    rows.append(_check("sla_rate_bounds", bool(on_time_valid), "0..1", "all rows"))

    return pd.DataFrame(rows)


def _scorecard(checks: pd.DataFrame) -> pd.DataFrame:
    total = len(checks)
    passed = int(checks["passed"].sum())
    score = round((passed / total) * 100, 2) if total else 0.0
    return pd.DataFrame(
        [
            {
                "checks_total": total,
                "checks_passed": passed,
                "checks_failed": total - passed,
                "platform_score": score,
            }
        ]
    )


def _render_report(profile: str, checks: pd.DataFrame, scorecard: pd.DataFrame) -> str:
    failed = checks.loc[~checks["passed"]]
    lines = [
        "# Data Quality and Observability Report",
        "",
        f"Profile: `{profile}`",
        f"Platform score: **{scorecard.iloc[0]['platform_score']}%**",
        "",
        "## Checks",
        "",
        checks.to_markdown(index=False),
        "",
        "## Failed Checks",
        "",
        failed.to_markdown(index=False) if not failed.empty else "No failed checks.",
        "",
    ]
    return "\n".join(lines)


def _check(name: str, passed: bool, observed: object, expected: object) -> dict[str, object]:
    return {
        "check_name": name,
        "passed": bool(passed),
        "observed": observed,
        "expected": expected,
    }


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
