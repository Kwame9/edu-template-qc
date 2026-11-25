"""Validation checks.

Every check returns a list of issues. An issue records where the problem is
(file, sheet, row, level, year), what failed, the value found, and a severity:
  error   -- the value is wrong and must be fixed before it is used
  warning -- the value is possible but unusual, so the country should confirm it
"""
import pandas as pd

from .config import GER_MAX, MAX_YEAR_CHANGE, METADATA_FIELDS, PTR_MAX, PTR_MIN


def _issue(row, check, severity, message, value=None):
    return {
        "country_code": row.get("country_code"),
        "source_file": row.get("source_file"),
        "sheet": row.get("sheet"),
        "excel_row": row.get("excel_row"),
        "level": row.get("level"),
        "year": row.get("year"),
        "check": check,
        "severity": severity,
        "message": message,
        "value": value,
    }


def check_metadata(meta, source_file):
    issues = []
    for field in METADATA_FIELDS:
        v = meta.get(field)
        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
            issues.append(_issue({"country_code": meta.get("Country code"), "source_file": source_file,
                                  "sheet": "Metadata"}, "metadata_missing", "error",
                                 f"Metadata field '{field}' is empty"))
    return issues


def check_values(tidy):
    """Missing, non-numeric and negative values."""
    issues = []
    for _, r in tidy.iterrows():
        raw = r["raw_value"]
        if pd.isna(raw):
            issues.append(_issue(r, "missing_value", "error", f"{r['sex']} is empty"))
        elif pd.isna(r["value"]):
            issues.append(_issue(r, "not_numeric", "error", f"{r['sex']} is not a number", raw))
        elif r["value"] < 0:
            issues.append(_issue(r, "negative_value", "error", f"{r['sex']} is negative", raw))
    return issues


def check_duplicates(tidy):
    issues = []
    keys = ["country_code", "sheet", "level", "year", "sex"]
    dupes = tidy[tidy.duplicated(keys, keep="first")]
    for _, r in dupes[dupes["sex"] == "Total"].iterrows():
        issues.append(_issue(r, "duplicate_row", "error", "The same level and year appear more than once"))
    return issues


def check_totals(tidy):
    """Female + Male must equal Total."""
    issues = []
    wide = _wide(tidy)
    for _, r in wide.iterrows():
        if pd.notna(r["Female"]) and pd.notna(r["Male"]) and pd.notna(r["Total"]):
            if r["Female"] + r["Male"] != r["Total"]:
                issues.append(_issue(r, "total_mismatch", "error",
                                     f"Female + Male = {r['Female'] + r['Male']:,.0f} but Total = {r['Total']:,.0f}",
                                     r["Total"]))
    return issues


def check_year_on_year(tidy):
    """Flag large changes in Total between consecutive years."""
    issues = []
    wide = _wide(tidy).sort_values("year")
    for (country, sheet, level), grp in wide.groupby(["country_code", "sheet", "level"]):
        grp = grp.dropna(subset=["Total"])
        prev = None
        for _, r in grp.iterrows():
            if prev is not None and prev["Total"] > 0:
                change = (r["Total"] - prev["Total"]) / prev["Total"]
                if abs(change) > MAX_YEAR_CHANGE:
                    issues.append(_issue(r, "year_on_year_change", "warning",
                                         f"Total changed by {change:+.0%} from {int(prev['year'])}",
                                         r["Total"]))
            prev = r
    return issues


def check_indicators(indicators):
    """Plausibility checks on calculated indicators."""
    issues = []
    for _, r in indicators.iterrows():
        r = dict(r, sheet="Calculated indicators")
        if pd.notna(r["GER"]) and r["GER"] > GER_MAX:
            issues.append(_issue(r, "ger_out_of_range", "warning",
                                 f"Gross enrolment ratio is {r['GER']:.1f}%, above {GER_MAX:.0f}%", r["GER"]))
        if pd.notna(r["PTR"]) and not (PTR_MIN <= r["PTR"] <= PTR_MAX):
            issues.append(_issue(r, "ptr_out_of_range", "warning",
                                 f"Pupil-teacher ratio is {r['PTR']:.1f}, outside {PTR_MIN:.0f}-{PTR_MAX:.0f}", r["PTR"]))
    return issues


def _wide(tidy):
    """One row per country/sheet/level/year with Female, Male, Total columns."""
    keys = ["country_code", "source_file", "sheet", "level", "year"]
    wide = (tidy.drop_duplicates(keys + ["sex"])
                .pivot_table(index=keys, columns="sex", values="value", aggfunc="first", dropna=False)
                .reset_index())
    rows = tidy.drop_duplicates(keys)[keys + ["excel_row"]]
    wide = wide.merge(rows, on=keys, how="left")
    for col in ("Female", "Male", "Total"):
        if col not in wide:
            wide[col] = float("nan")
    return wide
