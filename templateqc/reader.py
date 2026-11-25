"""Read completed templates into one tidy table.

Tidy format means one row per value: country, sheet, level, year, sex, value.
That shape makes checks, indicator calculations and consolidation simple and
keeps every value traceable to the exact sheet and row it came from.
"""
from pathlib import Path

import pandas as pd

from .config import DATA_COLUMNS, DATA_SHEETS, METADATA_FIELDS


def read_metadata(path):
    meta = pd.read_excel(path, sheet_name="Metadata", header=None, names=["field", "value"])
    return dict(zip(meta["field"], meta["value"]))


def read_template(path):
    """Return (metadata dict, tidy DataFrame, list of structural problems)."""
    path = Path(path)
    problems = []
    meta = read_metadata(path)
    code = meta.get("Country code")

    frames = []
    for sheet in DATA_SHEETS:
        # keep_default_na=False so a typed "n/a" is kept as text and flagged, not read as blank
        df = pd.read_excel(path, sheet_name=sheet, keep_default_na=False, na_values=[""])
        missing_cols = [c for c in DATA_COLUMNS if c not in df.columns]
        if missing_cols:
            problems.append({"sheet": sheet, "message": f"Missing columns: {missing_cols}"})
            continue
        df["excel_row"] = df.index + 2  # +1 for header, +1 for 1-based rows
        long = df.melt(id_vars=["Level", "Year", "excel_row"], value_vars=["Female", "Male", "Total"],
                       var_name="sex", value_name="raw_value")
        long["sheet"] = sheet
        frames.append(long)

    tidy = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    tidy = tidy.rename(columns={"Level": "level", "Year": "year"})
    tidy["country_code"] = code
    tidy["source_file"] = path.name
    # Keep the raw entry for the QC log; coerce a numeric copy for calculations.
    tidy["value"] = pd.to_numeric(tidy["raw_value"], errors="coerce")
    return meta, tidy, problems


def read_folder(folder):
    """Read every .xlsx template in a folder."""
    results = []
    for path in sorted(Path(folder).glob("*.xlsx")):
        results.append((path,) + read_template(path))
    return results
