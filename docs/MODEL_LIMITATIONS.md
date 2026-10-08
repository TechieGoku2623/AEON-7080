# Model limitations

- Constants in the glucose and insulin equations are illustrative. They are not fitted human parameters.
- Allometric scaling of clearance and volume is an assumption, not a measured relationship for a product.
- Monte Carlo bands are parameter uncertainty or synthetic-population spread. They are not clinical confidence intervals.
- The morphology classifier's accuracy is on a synthetic held-out split from the same generator.
- Cardiovascular pressure uses a fixed resistance. Respiratory "saturation" is an index of ventilation, not oxygen saturation.
- SIR/SEIR coefficients are whatever the user enters. The model does not know about a pathogen.
- No binding affinity, toxicity, ADME, genomic risk, image diagnosis, or trial result is computed.
- Reports do not contain citations unless a future retrieval provider returns one. None is configured.
