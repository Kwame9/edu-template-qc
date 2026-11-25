"""Validate a folder of completed templates and produce QC outputs.

Usage:
    python run_pipeline.py --input data/returns --output output
"""
import argparse

import pandas as pd

from templateqc import checks, indicators, reader, report


def main(input_dir, output_dir):
    all_tidy, issues = [], []
    for path, meta, tidy, problems in reader.read_folder(input_dir):
        issues += checks.check_metadata(meta, path.name)
        for p in problems:
            issues.append({"country_code": meta.get("Country code"), "source_file": path.name,
                           "sheet": p["sheet"], "check": "structure", "severity": "error",
                           "message": p["message"]})
        if tidy.empty:
            continue
        issues += checks.check_values(tidy)
        issues += checks.check_duplicates(tidy)
        issues += checks.check_totals(tidy)
        issues += checks.check_year_on_year(tidy)
        all_tidy.append(tidy)

    tidy = pd.concat(all_tidy, ignore_index=True)
    ind = indicators.calculate(tidy.drop_duplicates(["country_code", "sheet", "level", "year", "sex"]))
    issues += checks.check_indicators(ind)
    log = report.write_outputs(output_dir, tidy, ind, issues)

    countries = tidy["country_code"].nunique()
    print(f"Read {countries} templates. Found {(log['severity'] == 'error').sum()} errors "
          f"and {(log['severity'] == 'warning').sum()} warnings.")
    print(log.groupby(["country_code", "severity"]).size().unstack(fill_value=0).to_string())
    print(f"Outputs written to {output_dir}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="data/returns")
    ap.add_argument("--output", default="output")
    args = ap.parse_args()
    main(args.input, args.output)
