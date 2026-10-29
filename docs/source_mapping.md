# Mapping the supplied KAPDA source files to the application

## Requirements document
The KAPDA Digital Database Data Requirements and Tracking Matrix calls for a persistent person ID; 
linked projects/indicators/activity data/evidence; learner enrolment,
attendance, retention, assessments, completion and transition; MHM/WASH; SMC/PTA; BSLFSR agriculture,
VSLA and peacebuilding; dashboards and disaggregation; verification, audit trails, backups and role-based access. The models in this starter provide a foundation for these domains.

## Excel workbook: `Data Based for IK Education Project`
The `Data_Source` sheet includes the fields `ID`, `Name`, `Sex`, `Age`, `Class`, `School/Institution`, `Level of Education`, `Completion Status`, `Year of Completion`, `Employer`, and `Home/Village`. It contains a mixture of primary/secondary education, post-secondary qualifications, vocational courses and employment details, including adults and records that appear to describe alumni. It is therefore not safe to import every row directly as a currently enrolled P1–S6 learner.

Recommended controlled import:
1. Keep the original workbook unchanged as source evidence.
2. Deduplicate by name plus school/year and review duplicate legacy IDs.
3. Classify each record as current learner, historical learner/alumnus, or non-school post-secondary/vocational record.
4. Map Sex to F/M only after checking source values; map `Age` to `estimated_age` when date of birth is unavailable.
5. Map `Class` only where it matches P1–P7 or S1–S6; retain other course/qualification labels in a separate legacy-history field or import staging table.
6. Map `School/Institution`, `Completion Status`, `Year of Completion`, `Employer`, and `Home/Village` only after review; do not treat completion as current enrolment.
7. Match existing people before creating records and issue the permanent KAPDA ID only after duplicate checks.
8. Validate a sample with programme/M&E staff before bulk import.

The `Dash_Board` sheet contains summaries/pivot-like counts. Dashboard totals should be recalculated from normalized records after migration rather than copied as authoritative totals.

## Suggested additional production step
Build a reviewed staging/import tool with row-level validation errors and a duplicate-review queue before uploading legacy records. This avoids corrupting longitudinal learner histories.
