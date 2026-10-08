# Reproducibility

Each drug-response configuration is fingerprinted with SHA-256 over canonical JSON of the config, seed, model versions, and software version.

The experiment row stores the config. Replay calls the same runner. The API compares the 12-hour glucose change and the fingerprint with the previous result.

Virtual patients use NumPy's Generator with the supplied seed. The same seed and condition return the same record.

Lineage for a run is a directed graph from input parameters through PK, PD, uncertainty, analysis, and the report. If a dataset name is supplied, it is the first node.
