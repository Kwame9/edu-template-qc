"""Create sample data for the demo.

Builds completed templates for five FICTIONAL countries (codes XA to XE) with
made-up numbers, then plants a few typical reporting mistakes so the
pipeline has something to find. It also builds one blank, pre-filled template
for the next cycle, to show how template updates can be automated.

Usage:
    python make_sample_data.py
"""
import random
from pathlib import Path

from openpyxl import load_workbook

from templateqc.config import LEVELS
from templateqc.templates import build_template

COUNTRIES = {"XA": "Country A", "XB": "Country B", "XC": "Country C", "XD": "Country D", "XE": "Country E"}
YEARS = [2025, 2026]
# Rough school-age population shares per level, used to make plausible numbers.
LEVEL_POP = {"Pre-primary": 0.6, "Primary": 1.6, "Lower secondary": 0.9, "Upper secondary": 0.8}
LEVEL_GER = {"Pre-primary": 0.55, "Primary": 0.98, "Lower secondary": 0.80, "Upper secondary": 0.60}
LEVEL_PTR = {"Pre-primary": 25, "Primary": 30, "Lower secondary": 22, "Upper secondary": 18}


def split(total, female_share):
    female = round(total * female_share)
    return female, total - female, total


def country_values(rng, size):
    values = {}
    for year in YEARS:
        growth = 1 + 0.03 * (year - YEARS[0])
        for level in LEVELS:
            pop = round(size * LEVEL_POP[level] * growth * rng.uniform(0.95, 1.05))
            enrol = round(pop * LEVEL_GER[level] * rng.uniform(0.95, 1.05))
            teachers = max(1, round(enrol / (LEVEL_PTR[level] * rng.uniform(0.9, 1.1))))
            values[("Population", level, year)] = split(pop, 0.49)
            values[("Enrolment", level, year)] = split(enrol, rng.uniform(0.47, 0.51))
            values[("Teachers", level, year)] = split(teachers, rng.uniform(0.45, 0.65))
    return values


def set_cell(path, sheet, row, col, value):
    wb = load_workbook(path)
    wb[sheet].cell(row=row, column=col).value = value  # assign directly so None clears the cell
    wb.save(path)


def scale_row(path, sheet, row, factor):
    """Divide Female, Male and Total on one row by `factor` (keeps them consistent)."""
    wb = load_workbook(path)
    ws = wb[sheet]
    for col in (3, 4, 5):
        ws.cell(row=row, column=col).value = round(ws.cell(row=row, column=col).value / factor)
    f, m = ws.cell(row=row, column=3).value, ws.cell(row=row, column=4).value
    ws.cell(row=row, column=5).value = f + m
    wb.save(path)


def main():
    rng = random.Random(2027)
    returns = Path("data/returns")
    returns.mkdir(parents=True, exist_ok=True)

    for code, name in COUNTRIES.items():
        path = returns / f"template_{code}.xlsx"
        values = country_values(rng, size=rng.randint(200_000, 900_000))
        build_template(path, code, name, YEARS, prefill=values)
        set_cell(path, "Metadata", 4, 2, "Statistics Unit, Ministry of Education")
        set_cell(path, "Metadata", 5, 2, "2027-03-01")

    # Plant typical mistakes (rows: 2-5 are 2025 levels, 6-9 are 2026 levels).
    set_cell(returns / "template_XB.xlsx", "Enrolment", 7, 5, 999_999)       # total doesn't match
    set_cell(returns / "template_XB.xlsx", "Metadata", 4, 2, None)           # respondent missing
    set_cell(returns / "template_XC.xlsx", "Teachers", 8, 3, "n/a")          # text in a number cell
    set_cell(returns / "template_XC.xlsx", "Enrolment", 9, 4, None)          # missing value
    scale_row(returns / "template_XD.xlsx", "Teachers", 7, 4.5)              # very high pupil-teacher ratio
    set_cell(returns / "template_XE.xlsx", "Population", 6, 3, -500)         # negative number

    # A blank template for the next cycle, pre-filled with Country A's 2026 figures.
    nxt = Path("data/next_cycle")
    nxt.mkdir(parents=True, exist_ok=True)
    values = {k: v for k, v in country_values(random.Random(1), 500_000).items() if k[2] == 2026}
    build_template(nxt / "template_XA_2027.xlsx", "XA", "Country A", [2026, 2027], prefill=values)

    print(f"Created {len(COUNTRIES)} sample returns in {returns}/ and a pre-filled 2027 template in {nxt}/")


if __name__ == "__main__":
    main()
