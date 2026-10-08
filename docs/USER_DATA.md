# User data

CSV, TSV, and JSON tables can be uploaded. The original file is stored as version 1 and is not overwritten.

Profiling reports row and column counts, numeric / categorical / datetime guesses, missingness, duplicate rows, a preview, and a sensitivity heuristic. The quality score is a heuristic, not a certification.

Possible emails, phone-like strings, SSN-like strings, long numeric ids, and identifier-like column names raise a warning. The scan does not claim complete de-identification. Using a flagged table in a mapping requires an explicit acknowledgement.

Usage flags:

- use in my experiments
- allow model training (default off)
- allow anonymized analytics (default off)

This build does not train on an uploaded table even if training is allowed. The permission is stored for a later, explicit training path.

DICOM, NIfTI, FASTA, FASTQ, VCF, images, and SDF are not accepted. The API returns an error instead of pretending to parse them.
