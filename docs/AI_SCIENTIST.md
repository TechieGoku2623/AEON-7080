# AI Scientist

The planner is deterministic and testable. It accepts a small set of intents:

- compare hypothetical treatments
- generate a synthetic patient
- generate a synthetic ECG
- run the abstract SIR model
- refuse diagnosis, prescribing, and other medical-advice questions

Execution calls allowlisted tools only. There is no unrestricted code execution.

The critic inspects ranges, seeds, uncertainty, and clinical-claim language. It records flags and leaves the submitted parameters unchanged.

The report quotes stored endpoints. The references section states that no external citations were retrieved.

Autonomous iteration is capped at one cycle. A suggested next experiment is text the user can choose to run.

Set `AEON_LLM_BASE_URL` and `AEON_LLM_API_KEY` to attach an OpenAI-compatible narrator. Narration that contains a number missing from the tool evidence is dropped.
