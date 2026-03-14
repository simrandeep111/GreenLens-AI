# Mock Supporting Documents

These PDFs now power GreenLens supporting-document assurance and fraud screening.
The backend parses them, extracts key fields, cross-checks them against the uploaded CSV,
and surfaces duplicate references, amount mismatches, unmatched documents, and evidence coverage gaps.

Recommended clean validation set for Maple Leaf Catering:
- `maple_leaf_catering/maple_leaf_toronto_hydro_july_2024.pdf`
- `maple_leaf_catering/maple_leaf_enbridge_statement_jan_2024.pdf`
- `maple_leaf_catering/maple_leaf_shell_fleet_receipt_aug_2024.pdf`
- `maple_leaf_catering/maple_leaf_sysco_invoice_sep_2024.pdf`

Fraud-signal add-ons for Maple Leaf Catering:
- `maple_leaf_catering/maple_leaf_shell_fleet_receipt_aug_2024_duplicate.pdf`
- `maple_leaf_catering/maple_leaf_sysco_invoice_sep_2024_duplicate.pdf`

Recommended clean validation set for TechNorth Solutions:
- `technorth_solutions/technorth_toronto_hydro_aug_2024.pdf`
- `technorth_solutions/technorth_enbridge_statement_dec_2024.pdf`
- `technorth_solutions/technorth_aws_invoice_oct_2024.pdf`

Fraud-signal add-ons for TechNorth Solutions:
- `technorth_solutions/technorth_aws_invoice_oct_2024_duplicate.pdf`
- `technorth_solutions/technorth_petro_canada_travel_receipt_sep_2024.pdf`

Notes:
- Company name, industry, province, and revenue still come from the intake form.
- The clean sets are chosen to produce stronger document-to-ledger matches.
- The fraud add-ons are intentionally suspicious and should raise duplicate, mismatch, or unmatched-document findings.
