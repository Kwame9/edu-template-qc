"""Build survey templates as Excel workbooks.

Each template has an Instructions sheet, a Metadata sheet and one sheet per
data table. Number cells carry Excel data validation (whole numbers >= 0), so
respondents get an error in Excel itself if they type text or a negative
number. A template can be pre-filled with last year's figures so countries
only need to update and extend them.
"""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from .config import DATA_COLUMNS, DATA_SHEETS, LEVELS, METADATA_FIELDS

HEADER_FILL = PatternFill("solid", fgColor="1F3A5F")
INPUT_FILL = PatternFill("solid", fgColor="FFF8DC")
PREFILL_FILL = PatternFill("solid", fgColor="E8EEF5")

INSTRUCTIONS = [
    "How to complete this template",
    "1. Fill in every field on the Metadata sheet.",
    "2. On each data sheet, enter whole numbers for Female, Male and Total.",
    "3. Total must equal Female + Male.",
    "4. Blue cells were pre-filled from last year's return. Check and correct them if needed.",
    "5. Yellow cells are for the new reference year.",
]


def build_template(path, country_code, country_name, years, prefill=None):
    """Create a blank (or pre-filled) template workbook at `path`.

    years   -- list of years to include, e.g. [2025, 2026]
    prefill -- optional dict {(sheet, level, year): (female, male, total)}
               holding last year's values to copy in.
    """
    prefill = prefill or {}
    wb = Workbook()

    ws = wb.active
    ws.title = "Instructions"
    for i, line in enumerate(INSTRUCTIONS, start=1):
        ws.cell(row=i, column=1, value=line).font = Font(bold=(i == 1))
    ws.column_dimensions["A"].width = 90

    meta = wb.create_sheet("Metadata")
    for i, field in enumerate(METADATA_FIELDS, start=1):
        meta.cell(row=i, column=1, value=field).font = Font(bold=True)
        cell = meta.cell(row=i, column=2)
        cell.fill = INPUT_FILL
    meta.cell(row=1, column=2, value=country_code)
    meta.cell(row=2, column=2, value=country_name)
    meta.cell(row=3, column=2, value=max(years))
    meta.column_dimensions["A"].width = 18
    meta.column_dimensions["B"].width = 30

    for sheet_name in DATA_SHEETS:
        ws = wb.create_sheet(sheet_name)
        for col, header in enumerate(DATA_COLUMNS, start=1):
            c = ws.cell(row=1, column=col, value=header)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HEADER_FILL
            c.alignment = Alignment(horizontal="center")
        row = 2
        for year in years:
            for level in LEVELS:
                ws.cell(row=row, column=1, value=level)
                ws.cell(row=row, column=2, value=year)
                values = prefill.get((sheet_name, level, year))
                for col in (3, 4, 5):
                    cell = ws.cell(row=row, column=col)
                    if values is not None:
                        cell.value = values[col - 3]
                        cell.fill = PREFILL_FILL
                    else:
                        cell.fill = INPUT_FILL
                row += 1
        last_row = row - 1
        # Excel-side validation: whole numbers, zero or more.
        dv = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0",
                            showErrorMessage=True, errorTitle="Invalid value",
                            error="Please enter a whole number of zero or more.")
        ws.add_data_validation(dv)
        dv.add(f"C2:E{last_row}")
        ws.column_dimensions["A"].width = 18
        ws.freeze_panes = "A2"

    wb.save(path)


def prefill_from_return(tidy_df, country_code):
    """Turn last cycle's validated data (tidy format) into a prefill dict."""
    rows = tidy_df[tidy_df["country_code"] == country_code]
    prefill = {}
    for (sheet, level, year), grp in rows.groupby(["sheet", "level", "year"]):
        v = grp.set_index("sex")["value"]
        prefill[(sheet, level, int(year))] = (v.get("Female"), v.get("Male"), v.get("Total"))
    return prefill
