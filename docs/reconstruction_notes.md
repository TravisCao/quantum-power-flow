# Reconstruction notes: what the paper does not specify

The paper is a four-page proof-of-concept letter. Its topology, injections, initialization, slack
voltage, iteration table, stressed load, Monte Carlo sample count, and injection correlation are
printed. Two inputs needed for a literal numerical rerun are not printed:

1. the six line impedances/admittances of the five-bus network;
2. the marginal variances of the two Gaussian injections in the stochastic experiment.

This repository does not hide those gaps. It reconstructs them explicitly and stores every
assumption in `configs/paper_case5.yaml`.

## 1. Inferring the omitted line impedance

The lower part of Fig. 2 is a triangle connecting buses 3, 4, and slack bus 5. Suppose its three
branches share a series admittance `y`. With complex bus voltages `v3`, `v4`, and `v5`,

```text
S3 = v3 * conj(y * (2 v3 - v4 - v5))
S4 = v4 * conj(y * (2 v4 - v3 - v5)).
```

Insert the final values printed in Table I:

```text
V3 = 0.9948, theta3 = -0.1144 rad, S3 = -0.95 - j0.01
V4 = 1.0182, theta4 = -0.0393 rad, S4 =  0.20 + j0.20
V5 = 1.002,  theta5 = 0.
```

A complex least-squares solution gives

```text
y = 0.49715945 - j4.95112784
z = 1/y = 0.02007846 + j0.19995804 p.u.
```

The discrepancy from `0.02 + j0.20` is at the level expected from four-decimal rounding. Solving
the AC equations with exactly `z = 0.02 + j0.20` gives

```text
V3 = 0.99485955, theta3 = -0.11437526 rad
V4 = 1.01824660, theta4 = -0.03924774 rad,
```

which reproduces the printed terminal solution. Because both triangles in Fig. 2 are drawn with the
same branch convention and the stressed voltage endpoints also agree, the same impedance is used
on all six branches. Run `python scripts/infer_missing_line_data.py` to repeat the inference.

## 2. Table-I internal inconsistencies

The reconstructed fast-decoupled trace agrees within about `6.2e-5` everywhere except the printed
second-iteration value `theta4 = -0.0340`. The physical iteration gives approximately `-0.03993`;
iteration 1 is `-0.0368` and iteration 3 is `-0.0393`. Extensive fitting with independent physical
branch parameters cannot generate the isolated `-0.0340` excursion while retaining the printed
terminal solution. It is therefore retained as a suspected table typo, not silently overwritten.

The printed first Newton iterate also differs from a conventional polar Newton-Raphson step under
the line data that exactly reproduce the final AC solution. The repository writes both traces to
`results/tables/test_i_newton_comparison.csv`. No damping factor or nonstandard Newton variant is
introduced merely to force the intermediate row.

## 3. Stressed-case iteration count

With the paper equations, reconstructed line data, and `1e-5` maximum-mismatch stopping criterion,
the stressed case converges in 32 updates. The paper reports 34. Small changes in stopping norm,
rounding, or the omitted original line data can account for this two-iteration difference near the
solvability boundary. The final voltage endpoints match the figure.

## 4. Gaussian marginal variance

Fig. 4 shows bus-3 active-power magnitude approximately over `0.90--1.00` p.u. and bus-4 active
power approximately over `0.19--0.21` p.u. A 1% relative standard deviation gives approximately
those three-to-four-sigma ranges. The implementation therefore samples positive magnitudes

```text
mean(P3 load magnitude) = 0.95, sigma = 0.0095
mean(P4 injection)      = 0.20, sigma = 0.0020
correlation             = 0.75,
```

then converts the bus-3 load magnitude to a negative net injection in the AC equations. This
convention reproduces the positive-slope injection scatter in Fig. 4(c). The assumption is exposed
as `active_power_relative_standard_deviation` in the YAML configuration.
