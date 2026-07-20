# Quantum Power-Flow Teaching Lab

This context defines the language used to present the quantum power-flow application to students without prior quantum-computing or linear-algebra knowledge.

## Language

**Quantum power-flow workflow**:
The complete application process that turns electricity demand into calculated bus voltages while using an HHL simulation for numerical adjustment subproblems.
_Avoid_: Quantum power-flow circuit

**Classical reference**:
The trusted voltage result produced by a conventional power-flow calculation and used to evaluate the HHL simulation.
_Avoid_: Correct answer, classical truth

**HHL simulation**:
A classical execution of the Harrow–Hassidim–Lloyd quantum algorithm model used to study its numerical result and resource requirements.
_Avoid_: Quantum-computer result, hardware result

**Electricity demand level**:
A student-controlled multiplier applied to the consuming buses in the teaching case.
_Avoid_: Trained parameter, quantum input strength

**Quantum precision**:
A student-facing level that determines how much numerical detail the HHL simulation represents and how many quantum resources it requires.
_Avoid_: Model quality, training level

**Adjustment round**:
One application step that calculates and applies voltage corrections before checking the remaining power imbalance.
_Avoid_: Training step, quantum iteration

**Circuit depth**:
The number of sequential operation layers in the compiled quantum circuit, used as an approximate indicator of quantum resource cost.
_Avoid_: Runtime, execution time
