"""Settings shared by every step of the pipeline.

Keeping the template layout and the validation thresholds in one place means
a change to next year's survey (a new education level, a stricter check) is
made here once, not hunted down across several scripts.
"""

# Education levels collected in every template, in the order they appear.
LEVELS = ["Pre-primary", "Primary", "Lower secondary", "Upper secondary"]

# Data sheets in each template. Every data sheet has the same columns.
DATA_SHEETS = ["Enrolment", "Teachers", "Population"]
DATA_COLUMNS = ["Level", "Year", "Female", "Male", "Total"]

# Cells on the Metadata sheet that must be filled in.
METADATA_FIELDS = ["Country code", "Country name", "Reference year", "Respondent", "Submission date"]

# Thresholds used by the plausibility checks (warnings, not errors).
GER_MAX = 150.0          # gross enrolment ratio above this is suspicious
PTR_MIN, PTR_MAX = 5.0, 100.0   # plausible pupil-teacher ratio range
MAX_YEAR_CHANGE = 0.20   # flag year-on-year changes larger than 20%
