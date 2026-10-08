# Scientific models

Every implemented model is a simplified computational model. Software checks compare numerical output with analytical solutions where a solution exists. That status is "validated for software correctness." It is not clinical validation.

## Exponential decay

dC/dt = -kC, with solution C0 exp(-kt). Used to test RK4.

## One-compartment IV

C(t) = (Dose/V) exp(-(CL/V) t).

## One-compartment oral

First-order absorption. The closed form is used, including the ka = kel limit.

## Two-compartment IV

Central and peripheral amounts, elimination from the central compartment, fixed-step RK4. SciPy `solve_ivp` is used as a software check.

## Indirect glucose response

Production is inhibited by E = Emax C / (EC50 + C). Baseline production equals kout times baseline glucose, so glucose is steady at zero concentration. For a constant effect the glucose solution is analytical and tested.

Heart-rate change is applied only through the supplied `hr_effect_bpm` parameter.

Treatment A and Treatment B are names for parameter sets, not real drugs.

## Cardiovascular and respiratory bookkeeping

Cardiac output is heart rate times a constant stroke volume. Resistance is fixed from the initial pressures. There is no baroreflex.

The respiratory saturation index is not SpO2.

## Glucose state labels

Cut-points label a simulated glucose series. The labels are computational. They are not a diagnosis or a clinical stage.

## SIR and SEIR

Abstract fractions in a closed population. Not a forecast and not tied to a named organism.

## Synthetic ECG

A sum of Gaussian P, Q, R, S, and T waves. Not an electrocardiogram recording.
