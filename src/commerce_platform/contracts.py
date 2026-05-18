from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class ContractResult:
    clean: pd.DataFrame
    rejected: pd.DataFrame
    issues: pd.DataFrame


def load_contracts(path: str | Path = "config/contracts.yml") -> dict[str, dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_source(path: Path) -> pd.DataFrame:
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return pd.DataFrame(rows)
    return pd.read_csv(path)


def validate_table(
    table_name: str,
    frame: pd.DataFrame,
    contracts: dict[str, dict[str, Any]],
    reference_frames: dict[str, pd.DataFrame],
) -> ContractResult:
    contract = contracts[table_name]
    invalid_mask = pd.Series(False, index=frame.index)
    issue_rows: list[dict[str, object]] = []

    for column in contract.get("required", []):
        if column not in frame.columns:
            invalid_mask[:] = True
            issue_rows.append(_issue(table_name, column, "missing_required_column", None, None))
            continue
        missing = frame[column].isna() | (frame[column].astype(str).str.len() == 0)
        invalid_mask |= missing
        issue_rows.extend(_issues_for_mask(table_name, frame, column, "missing_required_value", missing))

    for column in contract.get("unique", []):
        if column in frame.columns:
            duplicated = frame[column].duplicated(keep="first")
            invalid_mask |= duplicated
            issue_rows.extend(_issues_for_mask(table_name, frame, column, "duplicate_key", duplicated))

    for column in contract.get("positive", []):
        if column in frame.columns:
            numeric = pd.to_numeric(frame[column], errors="coerce")
            invalid = numeric <= 0
            invalid_mask |= invalid
            issue_rows.extend(_issues_for_mask(table_name, frame, column, "not_positive", invalid))

    for column in contract.get("non_negative", []):
        if column in frame.columns:
            numeric = pd.to_numeric(frame[column], errors="coerce")
            invalid = numeric < 0
            invalid_mask |= invalid
            issue_rows.extend(_issues_for_mask(table_name, frame, column, "negative_value", invalid))

    for column, allowed_values in contract.get("allowed", {}).items():
        if column in frame.columns:
            invalid = ~frame[column].isin(allowed_values)
            invalid_mask |= invalid
            issue_rows.extend(_issues_for_mask(table_name, frame, column, "invalid_allowed_value", invalid))

    for column, target in contract.get("foreign_keys", {}).items():
        if column in frame.columns:
            ref_table, ref_column = target.split(".")
            if ref_table not in reference_frames or ref_column not in reference_frames[ref_table].columns:
                continue
            valid_values = set(reference_frames[ref_table][ref_column].dropna().astype(str))
            invalid = ~frame[column].astype(str).isin(valid_values)
            invalid_mask |= invalid
            issue_rows.extend(_issues_for_mask(table_name, frame, column, f"missing_fk:{target}", invalid))

    clean = frame.loc[~invalid_mask].copy()
    rejected = frame.loc[invalid_mask].copy()
    if not rejected.empty:
        rejected.insert(0, "rejected_from", table_name)
    issues = pd.DataFrame(issue_rows)
    return ContractResult(clean=clean, rejected=rejected, issues=issues)


def _issue(table: str, column: str, issue_type: str, row_number: int | None, value: object) -> dict[str, object]:
    return {
        "table_name": table,
        "column_name": column,
        "issue_type": issue_type,
        "row_number": row_number,
        "value": value,
    }


def _issues_for_mask(
    table: str,
    frame: pd.DataFrame,
    column: str,
    issue_type: str,
    mask: pd.Series,
) -> list[dict[str, object]]:
    issues = []
    for index in frame.index[mask.fillna(False)]:
        value = frame.at[index, column] if column in frame.columns else None
        issues.append(_issue(table, column, issue_type, int(index), value))
    return issues
