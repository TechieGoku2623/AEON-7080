# Simulation engine

`SimulationModel` implements parameter validation, `run`, observables, assumptions, equations, and metadata.

`SimulationRegistry` is the only list the API will execute. Unknown names return 404.

`SimulationResult` carries model name and version, parameters, units, duration, time step, seed, assumptions, limitations, results, and a creation time.

Monte Carlo uses lognormal multipliers. A coefficient of variation of zero returns the baseline parameters.

One-at-a-time sensitivity moves one parameter by ±20% and does not edit the caller's configuration.

Replay re-executes the stored configuration. It does not copy the previous numeric arrays back as the answer.
