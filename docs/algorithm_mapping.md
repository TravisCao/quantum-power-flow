# Mapping the paper to the implementation

## Fast-decoupled AC equations

For the four non-slack buses, the implementation evaluates the nonlinear AC mismatch from

```text
S_calc = V_complex * conj(Ybus @ V_complex)
Delta S = S_spec - S_calc.
```

It then applies the normalized equations printed in the paper:

```text
B'  (V * Delta theta) = Delta P / V
B'' Delta V           = Delta Q / V.
```

`B'` and `B''` are constant real-symmetric reduced matrices. In the primary reproduction both are
`-imag(Ybus[pq,pq])`, which best matches Table I. Both mismatches are evaluated at the beginning of
an iteration, as shown in Algorithm 1. The implementation is in `qpf_repro.powerflow`.

## HHL circuit

The reconstructed reduced matrix is 4-by-4, so its right-hand side and solution require two system
qubits. The circuit uses:

- four phase-register qubits, as specified by the paper;
- two system-register qubits;
- one reciprocal-rotation ancilla;
- seven logical qubits in total.

The custom modern-Qiskit HHL implementation performs:

1. **Amplitude preparation.** Normalize the classical right-hand side `b` and prepare `|b>`.
2. **Quantum phase estimation.** Apply QPE to
   `U = exp(2*pi*i*A/phase_scale)`.
3. **Reciprocal rotation.** For each phase basis state, apply a controlled `RY` whose ancilla
   amplitude is `C/lambda_est`.
4. **Inverse QPE.** Uncompute the phase register.
5. **Postselection and readout.** Select phase register `|0...0>` and ancilla `|1>`, then recover
   the simulator solution amplitudes and their classical scale.

For the reconstructed matrix, the distinct eigenvalues are approximately `4.950495` and
`14.851485`. The first-iteration spectral calibration maps them exactly to four-bit phase bins 5
and 15. QPE and reciprocal rotation are constructed once and cached for every subsequent power-flow
iteration, implementing the paper's reuse idea.

## Global phase and signed classical updates

A quantum state is unchanged by a global complex phase, but the power-flow update requires signed
real numbers. The simulator fixes this phase without consulting the direct solution. Since `A` is
positive definite, `b^T A^{-1} b > 0`; the projected state is rotated so its overlap with `b` is
positive real. This gives a reproducible sign convention.

## Finite-register precision experiment

For the lossless matrix, the two eigenvalues are exactly 5 and 15. With phase scale 16:

- 2 phase qubits produce about 25% relative solution error;
- 3 phase qubits produce about 24% error;
- 4 and 5 phase qubits reproduce the direct solve to floating-point precision.

This directly tests the paper's observation that fewer than four phase qubits can lose sufficient
eigenvalue accuracy.

## Stochastic experiment and batched circuit-equivalent map

Explicitly simulating two HHL circuits per power-flow iteration for 5,000 samples would repeat the
same fixed matrix circuit tens of thousands of times. Once the phase bins are exact, the finite-QPE
HHL core implements the linear map

```text
V_eig @ diag(1 / lambda_phase_bin) @ V_eig.T.
```

The stochastic experiment applies this same map in a vectorized batch. Five samples are rerun using
the full Aer circuit; final voltage differences are below machine precision. This is an analytical
simulation acceleration, not a claim that a classical batch calculation is a quantum execution.
