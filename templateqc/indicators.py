"""Calculate simple education indicators from validated data.

GER (gross enrolment ratio)  = total enrolment / school-age population * 100
GPI (gender parity index)    = female GER / male GER
PTR (pupil-teacher ratio)    = total enrolment / total teachers

These are simplified versions for demonstration. A real survey would follow
the official indicator methodology exactly.
"""
import numpy as np
import pandas as pd


def calculate(tidy):
    table = tidy.pivot_table(index=["country_code", "level", "year"], columns=["sheet", "sex"],
                             values="value", aggfunc="first")

    def col(sheet, sex):
        return table[(sheet, sex)] if (sheet, sex) in table.columns else pd.Series(np.nan, index=table.index)

    def ratio(a, b):
        return (a / b.replace(0, np.nan)).astype(float)

    out = pd.DataFrame(index=table.index)
    out["GER"] = ratio(col("Enrolment", "Total"), col("Population", "Total")) * 100
    out["GER_female"] = ratio(col("Enrolment", "Female"), col("Population", "Female")) * 100
    out["GER_male"] = ratio(col("Enrolment", "Male"), col("Population", "Male")) * 100
    out["GPI"] = ratio(out["GER_female"], out["GER_male"])
    out["PTR"] = ratio(col("Enrolment", "Total"), col("Teachers", "Total"))
    return out.round(2).reset_index()
