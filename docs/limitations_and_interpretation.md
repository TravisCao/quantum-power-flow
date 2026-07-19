# Limitations and interpretation

## This is a simulator reproduction

The numerical experiments use Qiskit Aer statevectors. They do not run on noisy hardware. The HHL
output is read by inspecting/postselecting statevector amplitudes; a hardware implementation would
need measurements or tomography, with additional sampling and sign-reconstruction costs.

## State preparation and readout are included conceptually, not as an asymptotic speedup proof

The circuit prepares a dense amplitude-encoded right-hand side using Qiskit's `StatePreparation`.
For a general dense vector, loading that state is not free. Likewise, recovering every component of
the solution vector is not logarithmic-time readout. The repository therefore reproduces the
paper's proof-of-concept numerical pipeline but does not repeat its `O(log N)` statement as an
end-to-end complexity guarantee.

## Matrix simulation is exact and small

`exp(2*pi*i*A/s)` is compiled as a dense unitary for the 4-by-4 test matrix. This is reasonable for a
seven-qubit reproduction and makes the algorithm transparent. It is not a scalable sparse
Hamiltonian-simulation oracle.

## Four-bit spectral alignment uses classical calibration

The paper says the phase-estimation and reciprocal-rotation parameters are set at the beginning.
Here, the small matrix spectrum is classically inspected once to select a phase scale whose bins are
exact. This isolates the HHL logic and reproduces the reported high accuracy. In a large system,
obtaining a similarly favorable scale or eigenvalue grid would itself require care.

## No empirical quantum advantage is claimed

The generated circuit transpiles to hundreds of entangling gates even for the 4-dimensional linear
system. Classical `numpy.linalg.solve` is overwhelmingly faster at this size. The useful result of
this repository is methodological reproducibility: it shows exactly which quantum state, phase
encoding, controlled reciprocal rotation, postselection, and classical scaling are needed to make
the paper's QPF iteration numerically work.
