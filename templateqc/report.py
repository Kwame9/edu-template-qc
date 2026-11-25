"""Write the pipeline outputs.

qc_log.csv              every issue found, across all countries
consolidated.csv        all values in one tidy table, with a flag column
indicators.csv          calculated indicators
review_<CODE>.xlsx      one review report per country, ready to send back
"""
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill

ISSUE_COLUMNS = ["country_code", "source_file", "sheet", "excel_row", "level", "year",
                 "check", "severity", "message", "value"]
SEVERITY_FILL = {"error": PatternFill("solid", fgColor="F8D7DA"),
                 "warning": PatternFill("solid", fgColor="FFF3CD")}


def write_outputs(out_dir, tidy, indicators, issues):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = pd.DataFrame(issues, columns=ISSUE_COLUMNS).sort_values(
        ["country_code", "severity", "sheet", "excel_row"], na_position="last")
    log["excel_row"] = log["excel_row"].astype("Int64")
    log["year"] = pd.to_numeric(log["year"], errors="coerce").astype("Int64")
    log.to_csv(out / "qc_log.csv", index=False)

    # Mark values that sit on a row with an error, so analysts can exclude them.
    errors = log[log["severity"] == "error"]
    bad_rows = set(zip(errors["country_code"], errors["sheet"], errors["excel_row"]))
    consolidated = tidy.copy()
    consolidated["has_error"] = [
        (c, s, r) in bad_rows for c, s, r in zip(consolidated["country_code"], consolidated["sheet"],
                                                 consolidated["excel_row"])]
    consolidated[["country_code", "sheet", "level", "year", "sex", "value", "has_error", "source_file"]] \
        .to_csv(out / "consolidated.csv", index=False)
    indicators.to_csv(out / "indicators.csv", index=False)

    for code in sorted(tidy["country_code"].dropna().unique()):
        _country_review(out / f"review_{code}.xlsx", code,
                        log[log["country_code"] == code],
                        indicators[indicators["country_code"] == code])
    return log


def _country_review(path, code, log, indicators):
    summary = pd.DataFrame({
        "Item": ["Country code", "Errors to fix", "Warnings to confirm"],
        "Value": [code, int((log["severity"] == "error").sum()), int((log["severity"] == "warning").sum())],
    })
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        log.drop(columns=["country_code"]).to_excel(xw, sheet_name="Issues", index=False)
        indicators.drop(columns=["country_code"]).to_excel(xw, sheet_name="Indicators", index=False)
        ws = xw.sheets["Issues"]
        sev_col = list(log.drop(columns=["country_code"]).columns).index("severity") + 1
        for row in range(2, ws.max_row + 1):
            fill = SEVERITY_FILL.get(ws.cell(row=row, column=sev_col).value)
            if fill:
                for c in range(1, ws.max_column + 1):
                    ws.cell(row=row, column=c).fill = fill
        for sheet in xw.sheets.values():
            for cell in sheet[1]:
                cell.font = Font(bold=True)
            for column in sheet.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in column)
                sheet.column_dimensions[column[0].column_letter].width = min(max(width + 2, 10), 70)
