import pandas as pd

from templateqc import checks, indicators


def make_tidy(rows):
    """rows: list of (sheet, level, year, female, male, total)."""
    records = []
    for i, (sheet, level, year, f, m, t) in enumerate(rows):
        for sex, v in (("Female", f), ("Male", m), ("Total", t)):
            records.append({"country_code": "XT", "source_file": "test.xlsx", "sheet": sheet,
                            "level": level, "year": year, "sex": sex, "excel_row": i + 2,
                            "raw_value": v, "value": pd.to_numeric(v, errors="coerce")})
    return pd.DataFrame(records)


def test_totals_match_passes():
    tidy = make_tidy([("Enrolment", "Primary", 2026, 40, 60, 100)])
    assert checks.check_totals(tidy) == []


def test_totals_mismatch_is_an_error():
    tidy = make_tidy([("Enrolment", "Primary", 2026, 40, 60, 120)])
    issues = checks.check_totals(tidy)
    assert len(issues) == 1 and issues[0]["severity"] == "error"


def test_text_and_missing_values_are_errors():
    tidy = make_tidy([("Teachers", "Primary", 2026, "n/a", None, 10)])
    found = {i["check"] for i in checks.check_values(tidy)}
    assert found == {"not_numeric", "missing_value"}


def test_large_year_on_year_change_is_a_warning():
    tidy = make_tidy([("Enrolment", "Primary", 2025, 50, 50, 100),
                      ("Enrolment", "Primary", 2026, 75, 75, 150)])
    issues = checks.check_year_on_year(tidy)
    assert len(issues) == 1 and issues[0]["severity"] == "warning"


def test_indicators():
    tidy = make_tidy([("Enrolment", "Primary", 2026, 45, 50, 95),
                      ("Population", "Primary", 2026, 50, 50, 100),
                      ("Teachers", "Primary", 2026, 2, 3, 5)])
    ind = indicators.calculate(tidy).iloc[0]
    assert ind["GER"] == 95.0
    assert ind["GPI"] == 0.9
    assert ind["PTR"] == 19.0
