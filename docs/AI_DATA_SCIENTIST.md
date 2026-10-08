# AI Data Scientist

The data analyst answers from a loaded table:

- missingness by column
- Pearson correlation, plus an ordinary least-squares fit when statsmodels is installed
- first-to-last change of a numeric column
- a numeric summary and workflow suggestions that still require a confirmed mapping

Unsupported questions return a refusal instead of a guessed result.

The analyst does not run a simulation. Mapping is a separate call and requires `confirmed: true`.
