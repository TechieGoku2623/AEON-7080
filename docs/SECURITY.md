# Security

The model behind the scientist cannot execute shell, Python, or SQL. Tool names are an allowlist.

Passwords are stored as PBKDF2-HMAC-SHA256. Tokens are HMAC-signed with `AEON_SECRET` and expire.

Datasets are stored under the workspace id. Uploaded files are chmod 600. Deletion removes the version directory and writes an audit log.

Training and analytics permissions default to off. Nothing in this build copies an upload into a training set automatically.

The identifier scan is a heuristic. It is not de-identification and it is not a HIPAA claim.

Deployments should add TLS, a private database, a real secret, and encryption at rest. This repository does not claim those controls are active on a laptop SQLite file.

Redis and Celery are not connected. There is no background worker with broader privileges than the API.
