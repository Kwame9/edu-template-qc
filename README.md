# Education survey template QC

A small Python toolkit that automates the data-processing cycle for Excel-based survey templates: building and pre-filling templates, validating completed returns, calculating indicators, and producing QC logs, country review reports and a consolidated dataset.

It is a demonstration project. All data is **synthetic**, generated for five fictional countries (codes `XA` to `XE`), with typical reporting mistakes planted on purpose so the pipeline has something to find.

## What it does

```
make_sample_data.py           run_pipeline.py
        │                            │
        ▼                            ▼
Excel templates  ──►  read  ──►  validate  ──►  indicators  ──►  outputs
(with built-in                (tidy table)  (errors and                   qc_log.csv
 Excel validation,                           warnings)                    consolidated.csv
 pre-filled with                                                          indicators.csv
 last year's data)                                                        review_<country>.xlsx
```

1. **Template generation** (`templateqc/templates.py`). Builds a workbook with Instructions, Metadata and data sheets (Enrolment, Teachers, Population). Number cells carry Excel data validation, so respondents see an error in Excel if they enter text or a negative number. Templates can be pre-filled from last cycle's validated data, so countries only update and extend them.
2. **Reading** (`templateqc/reader.py`). Reads every template in a folder into one tidy table (one row per value), keeping the source file and Excel row of every value so any issue can be traced back.
3. **Validation** (`templateqc/checks.py`). Each check returns issues with a severity:

   | Check | Severity | Example |
   |---|---|---|
   | Metadata field empty | error | Respondent not filled in |
   | Missing value | error | Male enrolment blank |
   | Not a number | error | "n/a" typed in a number cell |
   | Negative value | error | Population of -500 |
   | Duplicate row | error | Same level and year entered twice |
   | Female + Male ≠ Total | error | 488,409 vs 999,999 |
   | Year-on-year change > 20% | warning | Teachers down 78% from last year |
   | Gross enrolment ratio > 150% | warning | GER of 207% |
   | Pupil-teacher ratio outside 5–100 | warning | PTR of 124 |

   Errors must be fixed before the data is used. Warnings may be genuine and are sent to the country to confirm.
4. **Indicators** (`templateqc/indicators.py`). Gross enrolment ratio (total, female, male), gender parity index and pupil-teacher ratio. These are simplified for demonstration; a real survey would follow the official indicator methodology exactly.
5. **Outputs** (`templateqc/report.py`).
   - `output/qc_log.csv`: every issue across all countries, with file, sheet and row.
   - `output/consolidated.csv`: all values in one table, with a `has_error` flag so analysts can exclude rows that failed validation.
   - `output/indicators.csv`: calculated indicators.
   - `output/review_<CODE>.xlsx`: one report per country (summary, issues highlighted by severity, indicators), ready to send back for corrections.

All layout settings and thresholds live in `templateqc/config.py`, so a change to next year's survey is made in one place.

## Run it

```bash
pip install -r requirements.txt
python make_sample_data.py      # creates data/returns/ and data/next_cycle/
python run_pipeline.py          # validates data/returns/ and writes output/
pytest                          # runs the unit tests
```

Sample output:

```
Read 5 templates. Found 6 errors and 5 warnings.
severity      error  warning
country_code
XA                0        1
XB                2        2
XC                2        0
XD                0        2
XE                2        0
```

Every planted mistake is caught. The one warning for `XA` comes from the random sample data itself (a 20% drop in teachers), which is exactly the kind of value a country would be asked to confirm.

## Project structure

```
templateqc/
  config.py       template layout and validation thresholds
  templates.py    build and pre-fill Excel templates
  reader.py       read templates into a tidy table
  checks.py       validation checks
  indicators.py   indicator calculations
  report.py       QC log, consolidated data, country review reports
make_sample_data.py   synthetic data for five fictional countries
run_pipeline.py       command-line entry point
tests/                unit tests (pytest)
```

## Author

Kwame Opoku, data analyst, Accra, Ghana.
