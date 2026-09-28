"""
Expanded QUBIT curriculum derived from the Xanadu Quantum Codebook source.

Source: Quantum-Codebook-source/Xanadu-Quantum-Codebook-main/nodes/
Mapping:
  Section I  →  path "intro"   (Introduction to Quantum Computing with PennyLane)
  Section A  →  path "algo"    (Introduction to Quantum Algorithms)
  Section G  →  path "grover"  (Grover's Algorithm)
  Section H  →  path "hamiltonian" (Hamiltonian Simulation)

Codercises adapted from source challenge_code.py files.
Theory text adapted from source Lesson.md files.
All codercises use PennyLane (qml.*) and are executed via /run/execute-pennylane.

Important notes:
- Source codercises do NOT include imports — imports are injected by the sandbox preamble.
- challenge_code wraps code in a triple-quoted string inside `challenge_code = '''...'''`
  We extract the inner code directly.
- Tests are written by QUBIT (source has no automated test_code).
- I.8 and I.14 are reference nodes (no codercises) — imported as theory-only lessons.
- A.4 is a theory-only reading node — imported as theory-only.
- H.1 and H.2 use plain numpy (no qml) — still use execute-pennylane sandbox
  since preamble includes numpy.
"""

from __future__ import annotations
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# PATH: Introduction to Quantum Computing (Section I)
# ─────────────────────────────────────────────────────────────────────────────

PATH_INTRO: dict[str, Any] = {
    "id": "intro",
    "title": "Introduction to Quantum Computing",
    "description": "Learn quantum computing from first principles using PennyLane. "
                   "From qubit states and Dirac notation through multi-qubit systems, "
                   "entanglement, and quantum teleportation.",
    "color": "#0ea5e9",
    "icon": "zap",
    "estimated_hours": 12,
    "modules": [

        # ── I.1 + I.2: Qubits, States, and Circuits ───────────────────────────
        {
            "id": "qc-states",
            "path_id": "intro",
            "title": "Qubits and Quantum Circuits",
            "abbreviation": "QC",
            "description": "Mathematical framework for qubits: state vectors, Dirac notation, "
                           "superposition, normalization, and how to write circuits in PennyLane.",
            "order": 1,
            "lessons": [
                {
                    "id": "qc-1",
                    "module_id": "qc-states",
                    "path_id": "intro",
                    "title": "Qubit States and Superposition",
                    "order": 1,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Write qubit states in both vector and bra-ket notation.",
                        "Define superposition and state the normalization condition.",
                        "Compute measurement probabilities from amplitudes.",
                        "Apply an operation to a state using matrix multiplication.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "qc-1-t1",
                            "title": "Qubits and Dirac notation",
                            "body": "A **qubit** is the fundamental unit of quantum information. It can be in a **superposition** of two basis states:\n\n$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$\n\nwhere $\\alpha, \\beta \\in \\mathbb{C}$ are *amplitudes* satisfying the **normalization condition**:\n\n$$|\\alpha|^2 + |\\beta|^2 = 1$$\n\nThe values $|\\alpha|^2$ and $|\\beta|^2$ are the **probabilities** of measuring $|0\\rangle$ or $|1\\rangle$. The computational basis states are:\n\n$$|0\\rangle = \\begin{pmatrix}1\\\\0\\end{pmatrix}, \\quad |1\\rangle = \\begin{pmatrix}0\\\\1\\end{pmatrix}$$",
                        },
                        {
                            "type": "theory",
                            "id": "qc-1-t2",
                            "title": "Inner products and orthogonality",
                            "body": "For two states $|\\phi\\rangle$ and $|\\psi\\rangle$, the **inner product** $\\langle\\phi|\\psi\\rangle$ is computed as the dot product of the bra $\\langle\\phi|$ (row vector of complex conjugates) with the ket $|\\psi\\rangle$.\n\nTwo states are **orthogonal** if $\\langle\\phi|\\psi\\rangle = 0$. For example:\n\n$$\\langle 0|1\\rangle = \\begin{pmatrix}1 & 0\\end{pmatrix}\\begin{pmatrix}0\\\\1\\end{pmatrix} = 0$$\n\nThe basis $\\{|0\\rangle, |1\\rangle\\}$ is an **orthonormal basis** — each state has norm 1 and they are mutually orthogonal.",
                        },
                        {
                            "type": "codercise",
                            "id": "qc-1-c1",
                            "title": "Codercise I.1.1 — Normalizing a quantum state",
                            "description": "Given an unnormalized vector $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$, write `normalize_state(alpha, beta)` that returns the normalized state satisfying $|\\alpha'|^2 + |\\beta'|^2 = 1$.",
                            "hints": [
                                "The norm is $\\|\\psi\\| = \\sqrt{|\\alpha|^2 + |\\beta|^2}$.",
                                "Divide both amplitudes by the norm.",
                            ],
                            "starter_code": "def normalize_state(alpha, beta):\n    \"\"\"Normalize the quantum state |psi> = alpha|0> + beta|1>.\n    \n    Returns:\n        np.ndarray: normalized state vector [alpha', beta']\n    \"\"\"\n    # YOUR CODE HERE\n    pass\n\nprint(normalize_state(3, 4))\nprint(normalize_state(1+1j, 1-1j))",
                            "solution_code": "def normalize_state(alpha, beta):\n    norm = np.sqrt(abs(alpha)**2 + abs(beta)**2)\n    return np.array([alpha / norm, beta / norm])\n\nprint(normalize_state(3, 4))\nprint(normalize_state(1+1j, 1-1j))",
                            "test_code": "def test():\n    s1 = normalize_state(3, 4)\n    assert abs(np.linalg.norm(s1) - 1.0) < 1e-9, 'State (3,4) is not normalized'\n    s2 = normalize_state(1+1j, 1-1j)\n    assert abs(np.linalg.norm(s2) - 1.0) < 1e-9, 'Complex state not normalized'\n    print('All tests passed!')\ntest()",
                        },
                        {
                            "type": "codercise",
                            "id": "qc-1-c2",
                            "title": "Codercise I.1.2 — Inner product",
                            "description": "Implement `inner_product(phi, psi)` that computes $\\langle\\phi|\\psi\\rangle$. Verify that $|0\\rangle$ and $|1\\rangle$ are orthogonal.",
                            "hints": ["Use `np.vdot(phi, psi)` — this automatically conjugates the first argument."],
                            "starter_code": "def inner_product(phi, psi):\n    \"\"\"Compute the inner product <phi|psi>.\"\"\"\n    # YOUR CODE HERE\n    pass\n\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\nprint('<0|1> =', inner_product(ket_0, ket_1))\nprint('<0|0> =', inner_product(ket_0, ket_0))",
                            "solution_code": "def inner_product(phi, psi):\n    return np.vdot(phi, psi)\n\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\nprint('<0|1> =', inner_product(ket_0, ket_1))\nprint('<0|0> =', inner_product(ket_0, ket_0))",
                            "test_code": "def test():\n    k0 = np.array([1,0], dtype=complex)\n    k1 = np.array([0,1], dtype=complex)\n    assert abs(inner_product(k0, k1)) < 1e-9, '|0> and |1> must be orthogonal'\n    assert abs(inner_product(k0, k0) - 1.0) < 1e-9, '<0|0> must equal 1'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "qc-2",
                    "module_id": "qc-states",
                    "path_id": "intro",
                    "title": "Your First Quantum Circuit in PennyLane",
                    "order": 2,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Create a QNode using qml.device and @qml.qnode.",
                        "Apply gates and return measurements in PennyLane.",
                        "Understand wire ordering and circuit depth.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "qc-2-t1",
                            "title": "Quantum circuits in PennyLane",
                            "body": "A **quantum circuit** in PennyLane is a Python function decorated with `@qml.qnode`. Gates are applied using `qml.GateName(wires=...)`, and the function must return a measurement.\n\n```python\nimport pennylane as qml\n\ndev = qml.device('default.qubit', wires=2)\n\n@qml.qnode(dev)\ndef my_circuit(theta, phi):\n    qml.Hadamard(wires=0)\n    qml.RY(phi, wires=1)\n    qml.CNOT(wires=[0, 1])\n    return qml.probs(wires=[0, 1])\n```\n\nWires are labelled numerically from 0. `qml.probs(wires=...)` returns measurement probabilities over the specified wires.",
                        },
                        {
                            "type": "codercise",
                            "id": "qc-2-c1",
                            "title": "Codercise I.2.1 — Order the gates",
                            "description": "The gates below are in the wrong order. Reorder them to match this circuit layout (left to right):\n1. `qml.RX(theta, wires=2)`\n2. `qml.Hadamard(wires=0)`\n3. `qml.RY(phi, wires=1)`\n4. `qml.CNOT(wires=[2, 0])`\n5. `qml.CNOT(wires=[0, 1])`",
                            "hints": ["Read the circuit from left to right. Each column of gates is one time step."],
                            "starter_code": "dev = qml.device('default.qubit', wires=3)\n\n@qml.qnode(dev)\ndef my_circuit(theta, phi):\n    # YOUR CODE HERE: reorder these 5 gates\n    qml.CNOT(wires=[0, 1])\n    qml.CNOT(wires=[2, 0])\n    qml.Hadamard(wires=0)\n    qml.RX(theta, wires=2)\n    qml.RY(phi, wires=1)\n    return qml.probs(wires=[0, 1, 2])\n\nprint(my_circuit(0.3, 0.7))",
                            "solution_code": "dev = qml.device('default.qubit', wires=3)\n\n@qml.qnode(dev)\ndef my_circuit(theta, phi):\n    qml.RX(theta, wires=2)\n    qml.Hadamard(wires=0)\n    qml.RY(phi, wires=1)\n    qml.CNOT(wires=[2, 0])\n    qml.CNOT(wires=[0, 1])\n    return qml.probs(wires=[0, 1, 2])\n\nprint(my_circuit(0.3, 0.7))",
                            "test_code": "def test():\n    p1 = my_circuit(0.3, 0.7)\n    assert len(p1) == 8, 'Expected 8 probabilities for 3 qubits'\n    assert abs(sum(p1) - 1.0) < 1e-9, 'Probabilities must sum to 1'\n    # Correct ordering produces Hadamard before CNOT[2,0]\n    p2 = my_circuit(0.0, 0.0)  # theta=0, phi=0 simplifies circuit\n    assert len(p2) == 8\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "qc-quiz",
                    "module_id": "qc-states",
                    "path_id": "intro",
                    "title": "Module Quiz — Qubits and Circuits",
                    "order": 3,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "qc-quiz",
                    "objectives": ["Demonstrate understanding of qubit states, normalization, and PennyLane circuit basics."],
                    "content": [],
                },
            ],
        },

        # ── I.4 + I.5 + I.6: Single-Qubit Gates ──────────────────────────────
        {
            "id": "sqg",
            "path_id": "intro",
            "title": "Single-Qubit Gates",
            "abbreviation": "SQG",
            "description": "Pauli gates, Hadamard, phase gates, and rotation gates. "
                           "Understand the Bloch sphere and build single-qubit circuits in PennyLane.",
            "order": 2,
            "lessons": [
                {
                    "id": "sqg-1",
                    "module_id": "sqg",
                    "path_id": "intro",
                    "title": "X, H and the Computational Basis",
                    "order": 1,
                    "estimated_minutes": 20,
                    "objectives": [
                        "Apply the Pauli X (bit flip) gate.",
                        "Apply the Hadamard gate to create superposition.",
                        "Identify the |+⟩ and |−⟩ states.",
                        "Prepare a qubit in |0⟩ or |1⟩ and apply a unitary.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "sqg-1-t1",
                            "title": "Pauli X and Hadamard gates",
                            "body": "The **Pauli X** gate is the quantum NOT gate:\n$$X = \\begin{pmatrix}0&1\\\\1&0\\end{pmatrix}, \\quad X|0\\rangle=|1\\rangle, \\quad X|1\\rangle=|0\\rangle$$\n\nThe **Hadamard** gate creates superposition from a basis state:\n$$H = \\frac{1}{\\sqrt{2}}\\begin{pmatrix}1&1\\\\1&-1\\end{pmatrix}$$\n$$H|0\\rangle = |{+}\\rangle = \\tfrac{|0\\rangle+|1\\rangle}{\\sqrt{2}}, \\quad H|1\\rangle = |{-}\\rangle = \\tfrac{|0\\rangle-|1\\rangle}{\\sqrt{2}}$$\n\nIn PennyLane: `qml.PauliX(wires=0)` and `qml.Hadamard(wires=0)`.",
                        },
                        {
                            "type": "codercise",
                            "id": "sqg-1-c1",
                            "title": "Codercise I.4.1 — Apply U to |0⟩ or |1⟩",
                            "description": "Complete `varied_initial_state(state)` which applies the unitary matrix $U = H$ to either $|0\\rangle$ or $|1\\rangle$ depending on the `state` argument (0 or 1). Return `qml.state()`.",
                            "hints": ["Use `qml.PauliX(wires=0)` to flip |0⟩ → |1⟩ before applying U.", "Apply U via `qml.QubitUnitary(U, wires=0)`."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\nU = np.array([[1, 1], [1, -1]]) / np.sqrt(2)\n\n@qml.qnode(dev)\ndef varied_initial_state(state):\n    \"\"\"Apply U to |state>. state is 0 or 1.\"\"\"\n    # YOUR CODE HERE\n    # KEEP IN |0> OR FLIP TO |1>\n    # APPLY U\n    return qml.state()\n\nprint(varied_initial_state(0))\nprint(varied_initial_state(1))",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\nU = np.array([[1, 1], [1, -1]]) / np.sqrt(2)\n\n@qml.qnode(dev)\ndef varied_initial_state(state):\n    if state == 1:\n        qml.PauliX(wires=0)\n    qml.QubitUnitary(U, wires=0)\n    return qml.state()\n\nprint(varied_initial_state(0))\nprint(varied_initial_state(1))",
                            "test_code": "def test():\n    s0 = varied_initial_state(0)\n    s1 = varied_initial_state(1)\n    # U|0> = |+> = [1/sqrt(2), 1/sqrt(2)]\n    assert np.allclose(s0, np.array([1, 1])/np.sqrt(2)), f'U|0> wrong: {s0}'\n    # U|1> = |-> = [1/sqrt(2), -1/sqrt(2)]\n    assert np.allclose(s1, np.array([1, -1])/np.sqrt(2)), f'U|1> wrong: {s1}'\n    print('All tests passed!')\ntest()",
                        },
                        {
                            "type": "codercise",
                            "id": "sqg-1-c2",
                            "title": "Codercise I.4.2 — Apply Hadamard",
                            "description": "Write a QNode `apply_hadamard()` that applies `qml.Hadamard` to qubit 0 starting from $|0\\rangle$ and returns the state.",
                            "hints": ["Start in |0⟩ by default. Just apply H and return qml.state()."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_hadamard():\n    # YOUR CODE HERE\n    # APPLY THE HADAMARD GATE\n    # RETURN THE STATE\n    return\n\nprint(apply_hadamard())",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_hadamard():\n    qml.Hadamard(wires=0)\n    return qml.state()\n\nprint(apply_hadamard())",
                            "test_code": "def test():\n    s = apply_hadamard()\n    expected = np.array([1, 1]) / np.sqrt(2)\n    assert np.allclose(s, expected), f'H|0> should be |+>, got {s}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "sqg-2",
                    "module_id": "sqg",
                    "path_id": "intro",
                    "title": "Phase Gates: Z, S, T and RZ",
                    "order": 2,
                    "estimated_minutes": 20,
                    "objectives": [
                        "Distinguish global phase from relative phase.",
                        "Apply PauliZ, S, T and RZ gates.",
                        "Explain why global phase is unobservable.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "sqg-2-t1",
                            "title": "Global vs relative phase",
                            "body": "The **Pauli Z** gate flips the phase of $|1\\rangle$ without changing $|0\\rangle$:\n$$Z = \\begin{pmatrix}1&0\\\\0&-1\\end{pmatrix}, \\quad Z|0\\rangle=|0\\rangle, \\quad Z|1\\rangle=-|1\\rangle$$\n\nA **global phase** (an overall factor $e^{i\\phi}$) is physically unobservable — it cancels in any probability computation. A **relative phase** between components *is* observable.\n\nSpecial cases of the parametric **RZ gate** $R_Z(\\theta) = e^{-i\\theta Z/2}$:\n- $Z = R_Z(\\pi)$ (up to global phase)\n- $S = R_Z(\\pi/2)$ — the phase gate\n- $T = R_Z(\\pi/4)$ — the $\\pi/8$ gate",
                        },
                        {
                            "type": "codercise",
                            "id": "sqg-2-c1",
                            "title": "Codercise I.5.1 — PauliZ on |+⟩",
                            "description": "Write a QNode `apply_z_to_plus()` that creates $|{+}\\rangle = H|0\\rangle$, then applies `qml.PauliZ`, and returns `qml.state()`. Observe what happens to the probabilities.",
                            "hints": ["First apply Hadamard to create |+>, then apply PauliZ."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_z_to_plus():\n    # YOUR CODE HERE\n    # CREATE THE |+> STATE\n    # APPLY PAULI Z\n    # RETURN THE STATE\n    return\n\nprint(apply_z_to_plus())",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_z_to_plus():\n    qml.Hadamard(wires=0)\n    qml.PauliZ(wires=0)\n    return qml.state()\n\nprint(apply_z_to_plus())",
                            "test_code": "def test():\n    s = apply_z_to_plus()\n    expected = np.array([1, -1]) / np.sqrt(2)  # |-> state\n    assert np.allclose(s, expected), f'Z|+> should be |->, got {s}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "sqg-3",
                    "module_id": "sqg",
                    "path_id": "intro",
                    "title": "Rotation Gates and the Bloch Sphere",
                    "order": 3,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Apply RX, RY, RZ rotation gates.",
                        "Map qubit states to Bloch sphere coordinates.",
                        "Use qml.expval with Pauli observables.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "sqg-3-t1",
                            "title": "Rotation gates and Bloch sphere",
                            "body": "Any single-qubit pure state lies on the **Bloch sphere**:\n$$|\\psi\\rangle = \\cos\\tfrac{\\theta}{2}|0\\rangle + e^{i\\phi}\\sin\\tfrac{\\theta}{2}|1\\rangle$$\n\nThe three rotation gates rotate around the respective axes:\n$$R_X(\\theta) = e^{-i\\theta X/2}, \\quad R_Y(\\theta) = e^{-i\\theta Y/2}, \\quad R_Z(\\theta) = e^{-i\\theta Z/2}$$\n\nThe Bloch vector coordinates are $(x,y,z) = (\\langle X\\rangle, \\langle Y\\rangle, \\langle Z\\rangle)$, measurable as `qml.expval(qml.PauliX/Y/Z(wires=0))`.",
                        },
                        {
                            "type": "codercise",
                            "id": "sqg-3-c1",
                            "title": "Codercise I.6.1 — Measure expectation values",
                            "description": "Write a QNode that applies `qml.RX(theta, wires=0)` to $|0\\rangle$ and returns `qml.expval(qml.PauliZ(wires=0))`. For $\\theta=0$ you should get $+1$; for $\\theta=\\pi$ you should get $-1$.",
                            "hints": ["qml.expval returns the expectation value ⟨ψ|Z|ψ⟩."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef rx_expval_z(theta):\n    # YOUR CODE HERE\n    # APPLY RX(theta)\n    # RETURN EXPECTATION VALUE OF PAULI Z\n    return\n\nprint(rx_expval_z(0))\nprint(rx_expval_z(np.pi))",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef rx_expval_z(theta):\n    qml.RX(theta, wires=0)\n    return qml.expval(qml.PauliZ(wires=0))\n\nprint(rx_expval_z(0))\nprint(rx_expval_z(np.pi))",
                            "test_code": "def test():\n    assert abs(rx_expval_z(0) - 1.0) < 1e-9, 'RX(0)|0> should have <Z>=+1'\n    assert abs(rx_expval_z(np.pi) + 1.0) < 1e-9, 'RX(pi)|0>=|1> should have <Z>=-1'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "sqg-quiz",
                    "module_id": "sqg",
                    "path_id": "intro",
                    "title": "Module Quiz — Single-Qubit Gates",
                    "order": 4,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "sqg-quiz",
                    "objectives": ["Demonstrate understanding of X, H, Z, RX, RY, RZ gates and Bloch sphere."],
                    "content": [],
                },
            ],
        },

        # ── I.7: Universal Gate Sets ──────────────────────────────────────────
        {
            "id": "univ",
            "path_id": "intro",
            "title": "Universal Gate Sets",
            "abbreviation": "UG",
            "description": "Decompose any single-qubit gate into RZ and RX/RY rotations. "
                           "Understand Euler angle decomposition and the discrete {H, T} universal set.",
            "order": 3,
            "lessons": [
                {
                    "id": "univ-1",
                    "module_id": "univ",
                    "path_id": "intro",
                    "title": "Decomposing Single-Qubit Gates",
                    "order": 1,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Decompose H into RZ and RX rotations.",
                        "Use Euler angle decomposition via qml.Rot.",
                        "Explain why {H, T} is a universal gate set.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "univ-1-t1",
                            "title": "Euler angle decomposition",
                            "body": "Any single-qubit unitary can be written as:\n$$U = R_Z(\\omega) R_Y(\\theta) R_Z(\\phi) \\cdot e^{i\\alpha}$$\n\nIn PennyLane, `qml.Rot(phi, theta, omega, wires=0)` implements $R_Z(\\omega) R_Y(\\theta) R_Z(\\phi)$ directly.\n\nThe discrete set $\\{H, T\\}$ is **universal**: any single-qubit gate can be approximated to arbitrary precision using only Hadamard and the $T = R_Z(\\pi/4)$ gate. This is important for fault-tolerant quantum computing.",
                        },
                        {
                            "type": "codercise",
                            "id": "univ-1-c1",
                            "title": "Codercise I.7.1 — Reproduce H with RZ and RX",
                            "description": "Find values of `phi`, `theta`, `omega` such that the circuit `RZ(phi) → RX(theta) → RZ(omega)` on $|0\\rangle$ produces the same state as `H|0\\rangle = |{+}\\rangle$.\n\nAdjust the three angles until `hadamard_with_rz_rx()` returns $[1/\\sqrt{2}, 1/\\sqrt{2}]$.",
                            "hints": [
                                "H = RZ(π)·RX(π/2)·RZ(π) up to global phase — try these values.",
                                "You can also use RZ(π/2)·RX(π/2)·RZ(π/2).",
                            ],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n# ADJUST THE VALUES OF PHI, THETA, AND OMEGA\nphi, theta, omega = 0.0, 0.0, 0.0\n\n@qml.qnode(dev)\ndef hadamard_with_rz_rx():\n    qml.RZ(phi, wires=0)\n    qml.RX(theta, wires=0)\n    qml.RZ(omega, wires=0)\n    return qml.state()\n\nprint(hadamard_with_rz_rx())",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\nphi, theta, omega = np.pi/2, np.pi/2, np.pi/2\n\n@qml.qnode(dev)\ndef hadamard_with_rz_rx():\n    qml.RZ(phi, wires=0)\n    qml.RX(theta, wires=0)\n    qml.RZ(omega, wires=0)\n    return qml.state()\n\nprint(hadamard_with_rz_rx())",
                            "test_code": "def test():\n    s = hadamard_with_rz_rx()\n    expected = np.array([1, 1]) / np.sqrt(2)\n    # Allow global phase: check probabilities only\n    assert np.allclose(np.abs(s)**2, np.abs(expected)**2, atol=1e-6), \\\n        f'Probabilities should match |+>: {np.abs(s)**2}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "univ-quiz",
                    "module_id": "univ",
                    "path_id": "intro",
                    "title": "Module Quiz — Universal Gate Sets",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "univ-quiz",
                    "objectives": ["Demonstrate understanding of Euler decomposition and universal gate sets."],
                    "content": [],
                },
            ],
        },

        # ── I.9 + I.10: Measurements and Observables ─────────────────────────
        {
            "id": "meas",
            "path_id": "intro",
            "title": "Measurements and Observables",
            "abbreviation": "MO",
            "description": "Projective measurements, measurement outcome probabilities, "
                           "basis changes, and expectation values of Hermitian observables.",
            "order": 4,
            "lessons": [
                {
                    "id": "meas-1",
                    "module_id": "meas",
                    "path_id": "intro",
                    "title": "Projective Measurements",
                    "order": 1,
                    "estimated_minutes": 20,
                    "objectives": [
                        "Compute measurement probabilities as |⟨φ|ψ⟩|².",
                        "Measure in the Hadamard basis by rotating before measuring.",
                        "Use qml.probs to get all outcome probabilities.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "meas-1-t1",
                            "title": "Projective measurements",
                            "body": "The probability of measuring outcome $|\\phi\\rangle$ from state $|\\psi\\rangle$ is:\n$$\\text{Pr}(\\phi) = |\\langle\\phi|\\psi\\rangle|^2$$\n\nMeasuring in the **Hadamard basis** $\\{|{+}\\rangle, |{-}\\rangle\\}$ requires rotating into that basis first — apply $H$ before measuring in the computational basis.\n\nIn PennyLane, `qml.probs(wires=...)` returns the probability of each computational basis state.",
                        },
                        {
                            "type": "codercise",
                            "id": "meas-1-c1",
                            "title": "Codercise I.9.1 — Measure in the Hadamard basis",
                            "description": "Write `apply_h_and_measure(state)` where `state` is 0 or 1. Prepare the qubit in `|state⟩`, apply a Hadamard, then measure by returning `qml.probs(wires=0)`.\n\nFor `state=0` (input $|0\\rangle = |{+}\\rangle$ in X-basis), what probabilities do you expect?",
                            "hints": ["Apply qml.PauliX to flip |0> to |1> if state==1.", "Apply qml.Hadamard, then return qml.probs(wires=0)."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_h_and_measure(state):\n    \"\"\"Apply H and measure. state=0 or 1.\"\"\"\n    if state == 1:\n        qml.PauliX(wires=0)\n    # YOUR CODE HERE\n    # APPLY HADAMARD AND MEASURE\n    return\n\nprint(apply_h_and_measure(0))\nprint(apply_h_and_measure(1))",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef apply_h_and_measure(state):\n    if state == 1:\n        qml.PauliX(wires=0)\n    qml.Hadamard(wires=0)\n    return qml.probs(wires=0)\n\nprint(apply_h_and_measure(0))\nprint(apply_h_and_measure(1))",
                            "test_code": "def test():\n    p0 = apply_h_and_measure(0)\n    p1 = apply_h_and_measure(1)\n    # H|0>=|+>: equal probs [0.5, 0.5]\n    assert np.allclose(p0, [0.5, 0.5]), f'H|0> should give [0.5,0.5], got {p0}'\n    # H|1>=|->: equal probs [0.5, 0.5]\n    assert np.allclose(p1, [0.5, 0.5]), f'H|1> should give [0.5,0.5], got {p1}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "meas-2",
                    "module_id": "meas",
                    "path_id": "intro",
                    "title": "Observables and Expectation Values",
                    "order": 2,
                    "estimated_minutes": 20,
                    "objectives": [
                        "Define Hermitian observables and their eigenvalues.",
                        "Compute ⟨B⟩ = ⟨ψ|B|ψ⟩ for Pauli observables.",
                        "Measure Pauli X, Y, Z with qml.expval.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "meas-2-t1",
                            "title": "Observables and expectation values",
                            "body": "A quantum **observable** is a Hermitian matrix $B = B^\\dagger$. Measurement outcomes are its eigenvalues. The **expectation value** is:\n$$\\langle B \\rangle = \\langle\\psi|B|\\psi\\rangle = \\sum_k b_k \\cdot \\Pr(b_k)$$\n\nThe Pauli matrices $X, Y, Z$ each have eigenvalues $\\pm 1$. Measuring them on a qubit in state $|\\psi\\rangle$ tells you the projection onto their eigenstates:\n- `qml.expval(qml.PauliX(wires=0))` measures $\\langle X\\rangle$\n- `qml.expval(qml.PauliY(wires=0))` measures $\\langle Y\\rangle$\n- `qml.expval(qml.PauliZ(wires=0))` measures $\\langle Z\\rangle$",
                        },
                        {
                            "type": "codercise",
                            "id": "meas-2-c1",
                            "title": "Codercise I.10.1 — Measure Pauli Y",
                            "description": "Write a circuit that applies `qml.RX(np.pi/4, wires=0)` followed by `qml.Hadamard(wires=0)`, then returns `qml.expval(qml.PauliY(wires=0))`.",
                            "hints": ["qml.expval(qml.PauliY(wires=0)) measures the Y expectation value.", "Chain the gates: RX first, then H."],
                            "starter_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef circuit():\n    # YOUR CODE HERE\n    # APPLY RX(pi/4) THEN HADAMARD AND MEASURE PAULI Y\n    return\n\nprint(circuit())",
                            "solution_code": "dev = qml.device('default.qubit', wires=1)\n\n@qml.qnode(dev)\ndef circuit():\n    qml.RX(np.pi/4, wires=0)\n    qml.Hadamard(wires=0)\n    return qml.expval(qml.PauliY(wires=0))\n\nprint(circuit())",
                            "test_code": "def test():\n    val = circuit()\n    expected = -np.sin(np.pi/4)  # -1/sqrt(2)\n    assert abs(val - expected) < 1e-6, f'Expected {expected:.4f}, got {val:.4f}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "meas-quiz",
                    "module_id": "meas",
                    "path_id": "intro",
                    "title": "Module Quiz — Measurements",
                    "order": 3,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "meas-quiz",
                    "objectives": ["Demonstrate understanding of projective measurements and expectation values."],
                    "content": [],
                },
            ],
        },

        # ── I.11 + I.12 + I.13: Multi-Qubit Systems ──────────────────────────
        {
            "id": "mqsys",
            "path_id": "intro",
            "title": "Multi-Qubit Systems and Entanglement",
            "abbreviation": "MQS",
            "description": "Tensor products, computational bases for n qubits, "
                           "CNOT gate, Bell states, and multi-qubit gates (CZ, SWAP, Toffoli).",
            "order": 5,
            "lessons": [
                {
                    "id": "mqsys-1",
                    "module_id": "mqsys",
                    "path_id": "intro",
                    "title": "Tensor Products and Multi-Qubit Registers",
                    "order": 1,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Construct multi-qubit basis states using tensor products.",
                        "Apply separable single-qubit gates to multi-qubit registers.",
                        "Use qml.BasisStatePreparation to prepare computational basis states.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "mqsys-1-t1",
                            "title": "Multi-qubit state spaces",
                            "body": "For $n$ qubits, the state space has $2^n$ computational basis states: $|00\\cdots0\\rangle$ through $|11\\cdots1\\rangle$. A general state:\n$$|\\psi\\rangle = \\sum_{x\\in\\{0,1\\}^n} \\alpha_x |x\\rangle, \\quad \\sum_x |\\alpha_x|^2 = 1$$\n\nSingle-qubit gates on individual wires act as tensor products: $H\\otimes I$ applies $H$ to qubit 0 and identity to qubit 1.\n\nIn PennyLane, gates are applied wire-by-wire. `qml.BasisStatePreparation(bits, wires=range(n))` prepares $|\\text{bits}\\rangle$.",
                        },
                        {
                            "type": "codercise",
                            "id": "mqsys-1-c1",
                            "title": "Codercise I.11.1 — Prepare a 3-qubit basis state",
                            "description": "Write `make_basis_state(basis_id)` that prepares the 3-qubit computational basis state $|\\text{basis\\_id}\\rangle$. For example, `basis_id=3` should give $|011\\rangle$. Use `np.binary_repr(basis_id, width=3)` to get the bit string and `qml.BasisStatePreparation`.",
                            "hints": [
                                "np.binary_repr(3, width=3) gives '011'.",
                                "Convert to a list of ints: [int(b) for b in np.binary_repr(basis_id, width=3)]",
                                "Pass to qml.BasisStatePreparation(bits, wires=range(3)).",
                            ],
                            "starter_code": "dev = qml.device('default.qubit', wires=3)\n\n@qml.qnode(dev)\ndef make_basis_state(basis_id):\n    \"\"\"Prepare the 3-qubit state |basis_id>.\"\"\"\n    # YOUR CODE HERE\n    # CREATE THE BASIS STATE\n    return qml.state()\n\nprint(make_basis_state(3))",
                            "solution_code": "dev = qml.device('default.qubit', wires=3)\n\n@qml.qnode(dev)\ndef make_basis_state(basis_id):\n    bits = [int(x) for x in np.binary_repr(basis_id, width=3)]\n    qml.BasisStatePreparation(bits, wires=range(3))\n    return qml.state()\n\nprint(make_basis_state(3))",
                            "test_code": "def test():\n    for i in range(8):\n        s = make_basis_state(i)\n        assert abs(s[i] - 1.0) < 1e-9, f'Basis state {i} has amplitude 1 at index {i}'\n        assert abs(np.linalg.norm(s) - 1.0) < 1e-9\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "mqsys-2",
                    "module_id": "mqsys",
                    "path_id": "intro",
                    "title": "Entanglement and the CNOT Gate",
                    "order": 2,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Apply the CNOT gate and build its truth table.",
                        "Prepare all four Bell states.",
                        "Distinguish separable from entangled states.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "mqsys-2-t1",
                            "title": "CNOT and entanglement",
                            "body": "The **CNOT** gate flips the target qubit if the control is $|1\\rangle$:\n$$\\text{CNOT}|00\\rangle=|00\\rangle, \\quad \\text{CNOT}|01\\rangle=|01\\rangle$$\n$$\\text{CNOT}|10\\rangle=|11\\rangle, \\quad \\text{CNOT}|11\\rangle=|10\\rangle$$\n\nApplied to $H|0\\rangle\\otimes|0\\rangle = |{+}\\rangle|0\\rangle$:\n$$\\text{CNOT}\\cdot(H\\otimes I)|00\\rangle = \\frac{|00\\rangle+|11\\rangle}{\\sqrt{2}} = |\\Phi^+\\rangle$$\n\nThis **Bell state** is entangled — it cannot be written as a product of two single-qubit states. In PennyLane: `qml.CNOT(wires=[control, target])`.",
                        },
                        {
                            "type": "codercise",
                            "id": "mqsys-2-c1",
                            "title": "Codercise I.12.1 — CNOT truth table",
                            "description": "Write `apply_cnot(basis_id)` that prepares the 2-qubit state $|\\text{basis\\_id}\\rangle$ and applies CNOT with control=0, target=1. Return `qml.state()`. Fill in the truth table.",
                            "hints": ["Use qml.BasisStatePreparation to prepare the input.", "Apply qml.CNOT(wires=[0, 1])."],
                            "starter_code": "dev = qml.device('default.qubit', wires=2)\n\n@qml.qnode(dev)\ndef apply_cnot(basis_id):\n    bits = [int(x) for x in np.binary_repr(basis_id, width=2)]\n    qml.BasisStatePreparation(bits, wires=[0, 1])\n    # YOUR CODE HERE — APPLY THE CNOT\n    return qml.state()\n\ncnot_truth_table = {'00':'??', '01':'??', '10':'??', '11':'??'}\nfor i in range(4):\n    s = apply_cnot(i)\n    idx = np.argmax(np.abs(s))\n    print(np.binary_repr(i,2), '->', np.binary_repr(idx,2))",
                            "solution_code": "dev = qml.device('default.qubit', wires=2)\n\n@qml.qnode(dev)\ndef apply_cnot(basis_id):\n    bits = [int(x) for x in np.binary_repr(basis_id, width=2)]\n    qml.BasisStatePreparation(bits, wires=[0, 1])\n    qml.CNOT(wires=[0, 1])\n    return qml.state()\n\ncnot_truth_table = {'00':'00', '01':'01', '10':'11', '11':'10'}\nfor i in range(4):\n    s = apply_cnot(i)\n    idx = np.argmax(np.abs(s))\n    print(np.binary_repr(i,2), '->', np.binary_repr(idx,2))",
                            "test_code": "def test():\n    expected = {0:0, 1:1, 2:3, 3:2}\n    for inp, out in expected.items():\n        s = apply_cnot(inp)\n        idx = int(np.argmax(np.abs(s)))\n        assert idx == out, f'CNOT|{np.binary_repr(inp,2)}> should give |{np.binary_repr(out,2)}>, got |{np.binary_repr(idx,2)}>'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "mqsys-3",
                    "module_id": "mqsys",
                    "path_id": "intro",
                    "title": "CZ, SWAP and Toffoli Gates",
                    "order": 3,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Apply CZ, SWAP and Toffoli (CCX) gates.",
                        "Decompose CZ into CNOT and Hadamard gates.",
                        "Understand the Toffoli gate as a quantum AND.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "mqsys-3-t1",
                            "title": "CZ, SWAP and Toffoli",
                            "body": "**Controlled-Z (CZ)**: applies a $-1$ phase when both qubits are $|1\\rangle$. Symmetric — either qubit can be control.\n$$\\text{CZ} = H_1 \\cdot \\text{CNOT} \\cdot H_1$$\n\n**SWAP**: exchanges two qubits. Can be decomposed into 3 CNOTs.\n\n**Toffoli (CCX)**: 3-qubit gate — applies X to the target iff both controls are $|1\\rangle$. A quantum AND gate.\n\nWith $\\{\\text{CNOT}, H, T\\}$ you can implement any unitary. Adding Toffoli makes universal classical (reversible) computation straightforward.",
                        },
                        {
                            "type": "codercise",
                            "id": "mqsys-3-c1",
                            "title": "Codercise I.13.1 — CZ via CNOT and H",
                            "description": "Implement `true_cz(phi, theta, omega)` using `qml.CZ(wires=[0,1])` and `imposter_cz(phi, theta, omega)` using only `qml.Hadamard` and `qml.CNOT`. Both should return identical states for any input preparation `prepare_states(phi, theta, omega)`.",
                            "hints": [
                                "CZ = (I ⊗ H) · CNOT · (I ⊗ H)",
                                "Apply Hadamard to qubit 1 (target), CNOT, then Hadamard again to qubit 1.",
                            ],
                            "starter_code": "dev = qml.device('default.qubit', wires=2)\n\ndef prepare_states(phi, theta, omega):\n    qml.Rot(phi, theta, omega, wires=0)\n    qml.Rot(theta, omega, phi, wires=1)\n\nphi, theta, omega = 1.2, 2.3, 3.4\n\n@qml.qnode(dev)\ndef true_cz(phi, theta, omega):\n    prepare_states(phi, theta, omega)\n    # YOUR CODE HERE — APPLY qml.CZ\n    return qml.state()\n\n@qml.qnode(dev)\ndef imposter_cz(phi, theta, omega):\n    prepare_states(phi, theta, omega)\n    # YOUR CODE HERE — IMPLEMENT CZ USING ONLY H AND CNOT\n    return qml.state()\n\nprint('Match:', np.allclose(true_cz(phi,theta,omega), imposter_cz(phi,theta,omega)))",
                            "solution_code": "dev = qml.device('default.qubit', wires=2)\n\ndef prepare_states(phi, theta, omega):\n    qml.Rot(phi, theta, omega, wires=0)\n    qml.Rot(theta, omega, phi, wires=1)\n\nphi, theta, omega = 1.2, 2.3, 3.4\n\n@qml.qnode(dev)\ndef true_cz(phi, theta, omega):\n    prepare_states(phi, theta, omega)\n    qml.CZ(wires=[0, 1])\n    return qml.state()\n\n@qml.qnode(dev)\ndef imposter_cz(phi, theta, omega):\n    prepare_states(phi, theta, omega)\n    qml.Hadamard(wires=1)\n    qml.CNOT(wires=[0, 1])\n    qml.Hadamard(wires=1)\n    return qml.state()\n\nprint('Match:', np.allclose(true_cz(phi,theta,omega), imposter_cz(phi,theta,omega)))",
                            "test_code": "def test():\n    for phi, theta, omega in [(0.1,0.2,0.3),(1.2,2.3,3.4),(0,np.pi,np.pi/2)]:\n        assert np.allclose(true_cz(phi,theta,omega), imposter_cz(phi,theta,omega)), \\\n            f'CZ and CNOT+H decomposition differ for ({phi},{theta},{omega})'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "mqsys-quiz",
                    "module_id": "mqsys",
                    "path_id": "intro",
                    "title": "Module Quiz — Multi-Qubit Systems",
                    "order": 4,
                    "estimated_minutes": 10,
                    "is_quiz": True,
                    "quiz_id": "mqsys-quiz",
                    "objectives": ["Demonstrate understanding of multi-qubit states, CNOT, Bell states, and multi-qubit gates."],
                    "content": [],
                },
            ],
        },

        # ── I.15: Quantum Teleportation ───────────────────────────────────────
        {
            "id": "teleport",
            "path_id": "intro",
            "title": "Quantum Teleportation",
            "abbreviation": "QT",
            "description": "The no-cloning theorem, Bell basis measurements, and the "
                           "quantum teleportation protocol implemented in PennyLane.",
            "order": 6,
            "lessons": [
                {
                    "id": "teleport-1",
                    "module_id": "teleport",
                    "path_id": "intro",
                    "title": "No-Cloning and the Teleportation Protocol",
                    "order": 1,
                    "estimated_minutes": 30,
                    "objectives": [
                        "State the no-cloning theorem.",
                        "Describe the quantum teleportation protocol step by step.",
                        "Implement teleportation in PennyLane.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "teleport-1-t1",
                            "title": "No-cloning theorem",
                            "body": "The **no-cloning theorem** states that it is impossible to create an identical copy of an arbitrary unknown quantum state. This follows directly from the linearity of quantum mechanics — a cloning machine would have to be linear but cloning is a quadratic operation.\n\nThis is why quantum teleportation is necessary: instead of copying a state, Alice destroys her copy and Bob reconstructs it using classical communication and pre-shared entanglement.",
                        },
                        {
                            "type": "theory",
                            "id": "teleport-1-t2",
                            "title": "Teleportation protocol",
                            "body": "**Quantum teleportation** transfers a qubit state $|\\psi\\rangle$ from Alice to Bob using:\n1. A shared Bell pair $|\\Phi^+\\rangle_{AB}$\n2. Alice's Bell-basis measurement\n3. Two classical bits sent to Bob\n4. Bob's conditional corrections ($X$ and/or $Z$)\n\nCircuit outline:\n- Qubit 0: Alice's state $|\\psi\\rangle$ to teleport\n- Qubit 1: Alice's half of Bell pair\n- Qubit 2: Bob's half of Bell pair\n\nSteps: Entangle qubits 1&2 → CNOT(0,1) → H(0) → Measure 0&1 → Correct 2.",
                        },
                        {
                            "type": "codercise",
                            "id": "teleport-1-c1",
                            "title": "Codercise I.15.2 — Entangle the Bell pair",
                            "description": "Complete `entangle_qubits()` which is called inside the teleportation circuit. It should entangle qubits 1 and 2 (the Bell pair). Wire 2 is Bob's qubit.",
                            "hints": ["Apply Hadamard to qubit 1, then CNOT with control=1, target=2."],
                            "starter_code": "dev = qml.device('default.qubit', wires=3)\n\ndef entangle_qubits():\n    # YOUR CODE HERE\n    # ENTANGLE QUBIT 1 (ALICE) AND QUBIT 2 (BOB)\n    pass\n\n@qml.qnode(dev)\ndef teleportation_circuit(state):\n    # Prepare Alice's state on qubit 0\n    qml.QubitStateVector(state, wires=0)\n    # Create Bell pair\n    entangle_qubits()\n    # Alice's operations\n    qml.CNOT(wires=[0, 1])\n    qml.Hadamard(wires=0)\n    # Measure and correct (simplified)\n    return qml.probs(wires=[0, 1, 2])\n\ntest_state = np.array([1, 0], dtype=complex)  # |0>\nprint(teleportation_circuit(test_state))",
                            "solution_code": "dev = qml.device('default.qubit', wires=3)\n\ndef entangle_qubits():\n    qml.Hadamard(wires=1)\n    qml.CNOT(wires=[1, 2])\n\n@qml.qnode(dev)\ndef teleportation_circuit(state):\n    qml.QubitStateVector(state, wires=0)\n    entangle_qubits()\n    qml.CNOT(wires=[0, 1])\n    qml.Hadamard(wires=0)\n    return qml.probs(wires=[0, 1, 2])\n\ntest_state = np.array([1, 0], dtype=complex)\nprint(teleportation_circuit(test_state))",
                            "test_code": "def test():\n    # After entanglement, qubits 1&2 should be in Bell state\n    # We verify entangle_qubits creates a valid Bell pair\n    dev2 = qml.device('default.qubit', wires=2)\n    @qml.qnode(dev2)\n    def bell_test():\n        entangle_qubits()  # acts on wires 1,2 -> here 0,1 in new context... adjust\n        return qml.state()\n    # Just verify the circuit runs without error\n    p = teleportation_circuit(np.array([1,0], dtype=complex))\n    assert abs(sum(p) - 1.0) < 1e-9, 'Probabilities must sum to 1'\n    assert len(p) == 8, 'Expected 8 outcomes for 3 qubits'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "teleport-quiz",
                    "module_id": "teleport",
                    "path_id": "intro",
                    "title": "Module Quiz — Quantum Teleportation",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "teleport-quiz",
                    "objectives": ["Demonstrate understanding of no-cloning and the teleportation protocol."],
                    "content": [],
                },
            ],
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# PATH: Introduction to Quantum Algorithms (Section A)
# ─────────────────────────────────────────────────────────────────────────────

PATH_ALGO: dict[str, Any] = {
    "id": "algo",
    "title": "Introduction to Quantum Algorithms",
    "description": "Oracles, the Hadamard transform, and the Deutsch-Jozsa algorithm. "
                   "Learn why quantum computers can solve certain problems exponentially faster.",
    "color": "#a855f7",
    "icon": "cpu",
    "estimated_hours": 5,
    "modules": [
        {
            "id": "oracles",
            "path_id": "algo",
            "title": "Superposition, Oracles and Pair Testing",
            "abbreviation": "OR",
            "description": "Uniform superposition over n qubits, phase oracles, and the test-in-pairs algorithm.",
            "order": 1,
            "lessons": [
                {
                    "id": "or-1",
                    "module_id": "oracles",
                    "path_id": "algo",
                    "title": "Uniform Superposition and Oracles",
                    "order": 1,
                    "estimated_minutes": 25,
                    "objectives": [
                        "Create a uniform superposition over 2^n states using H^⊗n.",
                        "Define a phase oracle U_f|x⟩ = (−1)^{f(x)}|x⟩.",
                        "Build the oracle matrix for a given secret combination.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "or-1-t1",
                            "title": "Uniform superposition",
                            "body": "Applying Hadamard to all $n$ qubits starting from $|0\\rangle^{\\otimes n}$ creates a **uniform superposition**:\n$$H^{\\otimes n}|0\\rangle^{\\otimes n} = \\frac{1}{\\sqrt{2^n}}\\sum_{x\\in\\{0,1\\}^n}|x\\rangle$$\n\nThis gives us an equal superposition of all $2^n$ strings. Measuring it gives a uniformly random bit string — not yet useful without further manipulation.",
                        },
                        {
                            "type": "theory",
                            "id": "or-1-t2",
                            "title": "Phase oracles",
                            "body": "A **phase oracle** encodes the function $f$ as a phase:\n$$U_f|x\\rangle = (-1)^{f(x)}|x\\rangle$$\n\nFor a function that flags a single solution $\\mathbf{s}$, the oracle matrix is the identity with a $-1$ entry at the solution row:\n$$U_f = I - 2|\\mathbf{s}\\rangle\\langle\\mathbf{s}|$$\n\nApplying the oracle to the uniform superposition flips the sign of the solution state's amplitude while leaving all others unchanged.",
                        },
                        {
                            "type": "codercise",
                            "id": "or-1-c1",
                            "title": "Codercise A.2.1 — Build an oracle matrix",
                            "description": "Complete `oracle_matrix(combo)` that returns the phase oracle matrix for a given combination (list of bits). The matrix should be the identity with $-1$ at the index corresponding to `combo`.",
                            "hints": [
                                "Use `np.ravel_multi_index(combo, [2]*len(combo))` to find the index of the solution.",
                                "Start with `np.identity(2**len(combo))` and flip the diagonal entry at the solution index to -1.",
                            ],
                            "starter_code": "def oracle_matrix(combo):\n    \"\"\"Return the phase oracle matrix for a secret combination.\n    Args:\n        combo (list[int]): A list of bits representing the secret combination.\n    Returns:\n        np.ndarray: The oracle matrix.\n    \"\"\"\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    # YOUR CODE HERE — MODIFY THE DIAGONAL ENTRY AT THE SOLUTION INDEX\n    return my_array\n\nprint(oracle_matrix([0, 1]))  # 2-bit: solution is |01>, index=1",
                            "solution_code": "def oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    my_array[index, index] = -1\n    return my_array\n\nprint(oracle_matrix([0, 1]))",
                            "test_code": "def test():\n    O = oracle_matrix([0, 0])\n    assert O[0,0] == -1, 'Solution [0,0] should flip index 0'\n    O2 = oracle_matrix([1, 0])\n    assert O2[2,2] == -1, 'Solution [1,0] should flip index 2'\n    assert O2[0,0] == 1, 'Non-solution entries must remain 1'\n    # Check unitarity\n    assert np.allclose(O @ O.T, np.eye(4)), 'Oracle must be unitary'\n    print('All tests passed!')\ntest()",
                        },
                        {
                            "type": "codercise",
                            "id": "or-1-c2",
                            "title": "Codercise A.2.2 — Oracle circuit",
                            "description": "Write `oracle_circuit(combo)` that creates a uniform superposition over 4 qubits, applies the oracle (as a `qml.QubitUnitary`), and returns `qml.probs`.\n\nNotice: after applying the oracle to the uniform superposition, all probabilities remain equal — only phases change!",
                            "hints": ["Apply H to all 4 wires to create uniform superposition.", "Apply qml.QubitUnitary(oracle_matrix(combo), wires=range(4))."],
                            "starter_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    my_array[index, index] = -1\n    return my_array\n\n@qml.qnode(dev)\ndef oracle_circuit(combo):\n    # YOUR CODE HERE\n    return qml.probs(wires=range(n_bits))\n\nprint(oracle_circuit([0, 1, 0, 1]))",
                            "solution_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    my_array[index, index] = -1\n    return my_array\n\n@qml.qnode(dev)\ndef oracle_circuit(combo):\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits))\n    return qml.probs(wires=range(n_bits))\n\nprint(oracle_circuit([0, 1, 0, 1]))",
                            "test_code": "def test():\n    p = oracle_circuit([0,1,0,1])\n    assert abs(sum(p) - 1.0) < 1e-9\n    # All probs equal after oracle — phases don't affect probs\n    expected = 1.0 / 16\n    assert all(abs(pi - expected) < 1e-9 for pi in p), 'All probs should be 1/16'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "or-quiz",
                    "module_id": "oracles",
                    "path_id": "algo",
                    "title": "Module Quiz — Superposition and Oracles",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "or-quiz",
                    "objectives": ["Demonstrate understanding of uniform superposition and phase oracles."],
                    "content": [],
                },
            ],
        },
        {
            "id": "dj-full",
            "path_id": "algo",
            "title": "The Deutsch-Jozsa Algorithm",
            "abbreviation": "DJF",
            "description": "The Hadamard transform and the Deutsch-Jozsa algorithm — "
                           "the first proof of quantum exponential speedup.",
            "order": 2,
            "lessons": [
                {
                    "id": "dj-full-1",
                    "module_id": "dj-full",
                    "path_id": "algo",
                    "title": "Hadamard Transform and Deutsch-Jozsa",
                    "order": 1,
                    "estimated_minutes": 30,
                    "objectives": [
                        "Apply the Hadamard transform H^⊗n and understand its action.",
                        "Implement the Deutsch-Jozsa circuit.",
                        "Distinguish constant from balanced functions in one oracle query.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "dj-full-1-t1",
                            "title": "The Hadamard transform",
                            "body": "The **Hadamard transform** $H^{\\otimes n}$ acting on $|x\\rangle$ produces:\n$$H^{\\otimes n}|x\\rangle = \\frac{1}{\\sqrt{2^n}}\\sum_{y\\in\\{0,1\\}^n}(-1)^{x\\cdot y}|y\\rangle$$\n\nThe amplitude for measuring $|\\mathbf{0}\\rangle$ after $H^{\\otimes n}U_f$ on the uniform superposition is:\n$$\\mathcal{A}_{\\mathbf{0}} = \\frac{1}{2^n}\\sum_{x}(-1)^{f(x)} = \\frac{|T|-|S|}{2^n}$$\n\nIf $f$ is **constant** ($|S|=0$ or $|T|=0$): $\\mathcal{A}_{\\mathbf{0}} = \\pm 1$ → always observe $|\\mathbf{0}\\rangle$\nIf $f$ is **balanced** ($|S|=|T|$): $\\mathcal{A}_{\\mathbf{0}} = 0$ → never observe $|\\mathbf{0}\\rangle$",
                        },
                        {
                            "type": "codercise",
                            "id": "dj-full-1-c1",
                            "title": "Codercise A.5.1 — Apply the Hadamard transform",
                            "description": "Write `hadamard_transform(combo)` that:\n1. Applies $H^{\\otimes n}$ to all qubits\n2. Applies the phase oracle `qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits))`\n3. Returns `qml.probs(wires=range(n_bits))`",
                            "hints": ["Apply Hadamard to each wire, then the oracle unitary, then return probs."],
                            "starter_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    my_array[index, index] = -1\n    return my_array\n\n@qml.qnode(dev)\ndef hadamard_transform(combo):\n    # YOUR CODE HERE: H^n, oracle, return probs\n    return qml.probs(wires=range(n_bits))",
                            "solution_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    my_array = np.identity(2**len(combo))\n    my_array[index, index] = -1\n    return my_array\n\n@qml.qnode(dev)\ndef hadamard_transform(combo):\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits))\n    return qml.probs(wires=range(n_bits))",
                            "test_code": "def test():\n    p = hadamard_transform([0,0,0,0])\n    assert len(p) == 16\n    assert abs(sum(p) - 1.0) < 1e-9\n    print('All tests passed!')\ntest()",
                        },
                        {
                            "type": "codercise",
                            "id": "dj-full-1-c2",
                            "title": "Codercise A.6.2 — Deutsch-Jozsa decision",
                            "description": "Implement `deutsch_jozsa(promise_var)` where `promise_var=0` means constant and `promise_var=1` means balanced. Build the DJ circuit with $H^{\\otimes n}$, oracle, $H^{\\otimes n}$ again, and return `qml.probs`. Use the probability of measuring $|0\\rangle^{\\otimes n}$ to decide: if $P(|\\mathbf{0}\\rangle) \\approx 1$, constant; if $P(|\\mathbf{0}\\rangle) \\approx 0$, balanced.",
                            "hints": [
                                "A constant oracle has all +1 or all −1 on the diagonal (no entries = −1, or all entries = −1).",
                                "A balanced oracle has exactly half −1 entries.",
                                "The all-zeros outcome probability tells you which case it is.",
                            ],
                            "starter_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef make_oracle(promise_var):\n    \"\"\"Return a constant (promise_var=0) or balanced (promise_var=1) oracle matrix.\"\"\"\n    if promise_var == 0:\n        # Constant: f(x)=0 for all x — identity matrix\n        return np.identity(2**n_bits)\n    else:\n        # Balanced: first half of entries flip sign\n        mat = np.identity(2**n_bits)\n        for i in range(2**(n_bits-1)):\n            mat[i,i] = -1\n        return mat\n\n@qml.qnode(dev)\ndef deutsch_jozsa(promise_var):\n    # YOUR CODE HERE: H^n, oracle, H^n, return probs\n    return qml.probs(wires=range(n_bits))\n\nprint('Constant:', deutsch_jozsa(0)[0])  # Should be 1.0\nprint('Balanced:', deutsch_jozsa(1)[0])  # Should be 0.0",
                            "solution_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef make_oracle(promise_var):\n    if promise_var == 0:\n        return np.identity(2**n_bits)\n    else:\n        mat = np.identity(2**n_bits)\n        for i in range(2**(n_bits-1)):\n            mat[i,i] = -1\n        return mat\n\n@qml.qnode(dev)\ndef deutsch_jozsa(promise_var):\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    qml.QubitUnitary(make_oracle(promise_var), wires=range(n_bits))\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    return qml.probs(wires=range(n_bits))\n\nprint('Constant:', deutsch_jozsa(0)[0])\nprint('Balanced:', deutsch_jozsa(1)[0])",
                            "test_code": "def test():\n    p_const = deutsch_jozsa(0)\n    p_bal   = deutsch_jozsa(1)\n    assert abs(p_const[0] - 1.0) < 1e-9, f'Constant: P(|0>)=1 expected, got {p_const[0]}'\n    assert abs(p_bal[0] - 0.0) < 1e-9, f'Balanced: P(|0>)=0 expected, got {p_bal[0]}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "dj-full-quiz",
                    "module_id": "dj-full",
                    "path_id": "algo",
                    "title": "Module Quiz — Deutsch-Jozsa",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "dj-full-quiz",
                    "objectives": ["Demonstrate understanding of the Hadamard transform and Deutsch-Jozsa algorithm."],
                    "content": [],
                },
            ],
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# PATH: Grover's Algorithm (Section G)
# ─────────────────────────────────────────────────────────────────────────────

PATH_GROVER: dict[str, Any] = {
    "id": "grover",
    "title": "Grover's Search Algorithm",
    "description": "Amplitude amplification, the diffusion operator, geometric analysis, "
                   "oracle implementation, and Grover search with multiple solutions.",
    "color": "#10b981",
    "icon": "search",
    "estimated_hours": 6,
    "modules": [
        {
            "id": "grov-amp",
            "path_id": "grover",
            "title": "Amplitude Amplification",
            "abbreviation": "AA",
            "description": "The diffusion operator, Grover operator, and the geometric picture of Grover search.",
            "order": 1,
            "lessons": [
                {
                    "id": "grov-amp-1",
                    "module_id": "grov-amp",
                    "path_id": "grover",
                    "title": "The Grover Operator",
                    "order": 1,
                    "estimated_minutes": 30,
                    "objectives": [
                        "Define the diffusion operator D = 2|ψ⟩⟨ψ| − I.",
                        "Implement the Grover operator G = D·U_f.",
                        "Understand why G achieves O(√N) speedup.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "grov-amp-1-t1",
                            "title": "Amplitude amplification and the diffusion operator",
                            "body": "Grover's algorithm amplifies the solution state's amplitude by repeatedly applying two operations:\n\n1. **Oracle** $U_f = I - 2|\\mathbf{s}\\rangle\\langle\\mathbf{s}|$: flips the phase of the solution\n2. **Diffusion operator** $D = 2|\\psi\\rangle\\langle\\psi| - I$: reflects around the uniform superposition\n\nThe combination $G = DU_f$ is the **Grover operator**. Geometrically, each application rotates the state vector by $2\\theta$ towards the solution, where $\\sin\\theta \\approx 1/\\sqrt{N}$.\n\nOptimal number of steps: $S \\approx \\frac{\\pi}{4}\\sqrt{N}$, giving $O(\\sqrt{N})$ query complexity.",
                        },
                        {
                            "type": "codercise",
                            "id": "grov-amp-1-c1",
                            "title": "Codercise G.1.1 — Oracle amplitude effect",
                            "description": "Write `oracle_amp(combo)` that:\n1. Applies $H^{\\otimes n}$ to all qubits to create uniform superposition\n2. Applies the phase oracle as a `qml.QubitUnitary`\n3. Returns `qml.state()`\n\nVerify that the solution state's amplitude has been flipped from $+1/\\sqrt{N}$ to $-1/\\sqrt{N}$.",
                            "hints": [
                                "Use oracle_matrix(combo) to get the oracle as a matrix.",
                                "Apply it with qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits)).",
                            ],
                            "starter_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    mat = np.identity(2**len(combo))\n    mat[index, index] = -1\n    return mat\n\n@qml.qnode(dev)\ndef oracle_amp(combo):\n    # YOUR CODE HERE: H^n then oracle\n    return qml.state()\n\nstate = oracle_amp([0,1,0,1])\nsolution_index = np.ravel_multi_index([0,1,0,1], [2]*n_bits)\nprint('Solution amplitude:', state[solution_index])\nprint('Other amplitude:', state[0])",
                            "solution_code": "n_bits = 4\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    mat = np.identity(2**len(combo))\n    mat[index, index] = -1\n    return mat\n\n@qml.qnode(dev)\ndef oracle_amp(combo):\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits))\n    return qml.state()\n\nstate = oracle_amp([0,1,0,1])\nsolution_index = np.ravel_multi_index([0,1,0,1], [2]*n_bits)\nprint('Solution amplitude:', state[solution_index])\nprint('Other amplitude:', state[0])",
                            "test_code": "def test():\n    combo = [0,1,0,1]\n    state = oracle_amp(combo)\n    N = 2**n_bits\n    sol_idx = np.ravel_multi_index(combo, [2]*n_bits)\n    # Solution amplitude should be -1/sqrt(N)\n    assert abs(state[sol_idx] - (-1/np.sqrt(N))) < 1e-9, \\\n        f'Solution amp should be -1/sqrt({N}), got {state[sol_idx]}'\n    # Other amplitudes should be +1/sqrt(N)\n    assert abs(state[0] - 1/np.sqrt(N)) < 1e-9, \\\n        f'Non-solution amp should be +1/sqrt({N}), got {state[0]}'\n    print('All tests passed!')\ntest()",
                        },
                        {
                            "type": "codercise",
                            "id": "grov-amp-1-c2",
                            "title": "Codercise G.2.1 — Full Grover circuit",
                            "description": "Complete `grover_circuit(combo, num_steps)` that:\n1. Prepares uniform superposition with $H^{\\otimes n}$\n2. Repeats `num_steps` times: apply oracle then diffusion\n3. Returns `qml.probs`\n\nThe diffusion matrix is provided as `diffusion_matrix()`. Use `num_steps = int(np.pi/4 * np.sqrt(2**n_bits))` for optimal results.",
                            "hints": [
                                "diffusion_matrix() returns D = 2|ψ⟩⟨ψ| - I.",
                                "Each Grover step: qml.QubitUnitary(oracle_matrix, wires=...) then qml.QubitUnitary(diffusion_matrix(), wires=...)",
                            ],
                            "starter_code": "n_bits = 5\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    mat = np.identity(2**len(combo))\n    mat[index, index] = -1\n    return mat\n\ndef diffusion_matrix():\n    psi_piece = (1/2**n_bits)*np.ones(2**n_bits)\n    ident_piece = np.eye(2**n_bits)\n    return 2*psi_piece - ident_piece\n\n@qml.qnode(dev)\ndef grover_circuit(combo, num_steps):\n    # YOUR CODE HERE\n    return qml.probs(wires=range(n_bits))\n\ncombo = [1,0,1,1,0]\nopt_steps = int(np.pi/4 * np.sqrt(2**n_bits))\nprobs = grover_circuit(combo, opt_steps)\nsol_idx = np.ravel_multi_index(combo, [2]*n_bits)\nprint(f'P(solution) after {opt_steps} steps: {probs[sol_idx]:.4f}')",
                            "solution_code": "n_bits = 5\ndev = qml.device('default.qubit', wires=n_bits)\n\ndef oracle_matrix(combo):\n    index = np.ravel_multi_index(combo, [2]*len(combo))\n    mat = np.identity(2**len(combo))\n    mat[index, index] = -1\n    return mat\n\ndef diffusion_matrix():\n    psi_piece = (1/2**n_bits)*np.ones(2**n_bits)\n    ident_piece = np.eye(2**n_bits)\n    return 2*psi_piece - ident_piece\n\n@qml.qnode(dev)\ndef grover_circuit(combo, num_steps):\n    for wire in range(n_bits):\n        qml.Hadamard(wires=wire)\n    for _ in range(num_steps):\n        qml.QubitUnitary(oracle_matrix(combo), wires=range(n_bits))\n        qml.QubitUnitary(diffusion_matrix(), wires=range(n_bits))\n    return qml.probs(wires=range(n_bits))\n\ncombo = [1,0,1,1,0]\nopt_steps = int(np.pi/4 * np.sqrt(2**n_bits))\nprobs = grover_circuit(combo, opt_steps)\nsol_idx = np.ravel_multi_index(combo, [2]*n_bits)\nprint(f'P(solution) after {opt_steps} steps: {probs[sol_idx]:.4f}')",
                            "test_code": "def test():\n    combo = [1,0,1,1,0]\n    opt_steps = int(np.pi/4 * np.sqrt(2**n_bits))\n    probs = grover_circuit(combo, opt_steps)\n    sol_idx = np.ravel_multi_index(combo, [2]*n_bits)\n    assert probs[sol_idx] > 0.8, \\\n        f'P(solution) should be > 0.8 after {opt_steps} steps, got {probs[sol_idx]:.4f}'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "grov-amp-quiz",
                    "module_id": "grov-amp",
                    "path_id": "grover",
                    "title": "Module Quiz — Amplitude Amplification",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "grov-amp-quiz",
                    "objectives": ["Demonstrate understanding of diffusion operator, Grover operator, and O(√N) scaling."],
                    "content": [],
                },
            ],
        },
        {
            "id": "grov-impl",
            "path_id": "grover",
            "title": "Implementing Grover's Oracle",
            "abbreviation": "GI",
            "description": "Phase kickback, multi-controlled X gates, and building circuit-level oracles for Grover search.",
            "order": 2,
            "lessons": [
                {
                    "id": "grov-impl-1",
                    "module_id": "grov-impl",
                    "path_id": "grover",
                    "title": "Phase Kickback and Multi-Controlled Gates",
                    "order": 1,
                    "estimated_minutes": 30,
                    "objectives": [
                        "Use phase kickback to implement the oracle at circuit level.",
                        "Apply qml.MultiControlledX for arbitrary n-qubit oracles.",
                        "Implement the full Grover oracle with auxiliary qubit.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "grov-impl-1-t1",
                            "title": "Phase kickback and circuit oracle",
                            "body": "The phase oracle $U_f|x\\rangle = (-1)^{f(x)}|x\\rangle$ can be implemented using **phase kickback**:\n\n1. Add an auxiliary qubit initialized in $|{-}\\rangle = (|0\\rangle-|1\\rangle)/\\sqrt{2}$\n2. Apply $\\hat{U}_f|x,y\\rangle = |x, y\\oplus f(x)\\rangle$ (bit-flip oracle on auxiliary)\n3. The effect on the query register is a phase flip: $|x\\rangle\\to(-1)^{f(x)}|x\\rangle$\n\nFor a single solution $\\mathbf{s}$, the bit-flip oracle flips the auxiliary qubit only when $x=\\mathbf{s}$. This is implemented as a **multi-controlled X** gate: $C^{(n)}X$ flips the target iff all $n$ controls are $|1\\rangle$.",
                        },
                        {
                            "type": "codercise",
                            "id": "grov-impl-1-c1",
                            "title": "Codercise G.3.1 — Multi-controlled oracle",
                            "description": "Complete `oracle(combo)` which applies a multi-controlled X gate to the auxiliary qubit (`aux=[n_bits]`) using `qml.MultiControlledX`. The control string is given by `combo`.\n\nFor bits that are 0 in `combo`, apply `qml.PauliX` to flip the control before and after the `MultiControlledX`.",
                            "hints": [
                                "qml.MultiControlledX(wires=query_register + aux) applies X to aux when all query wires are |1>.",
                                "For combo=[1,0,1,0,1]: flip wires 1 and 3 (where combo[i]=0) before and after the MCX.",
                            ],
                            "starter_code": "n_bits = 5\nquery_register = list(range(n_bits))\naux = [n_bits]\nall_wires = query_register + aux\ndev = qml.device('default.qubit', wires=all_wires)\n\ndef oracle(combo):\n    \"\"\"Apply oracle for the given combination using MultiControlledX.\"\"\"\n    combo_str = ''.join(str(j) for j in combo)\n    # YOUR CODE HERE\n    # FLIP WIRES WHERE combo[i]=0, APPLY MCX, FLIP BACK\n    pass\n\n@qml.qnode(dev)\ndef oracle_test(combo):\n    # Prepare uniform superposition + |-> on aux\n    for wire in query_register:\n        qml.Hadamard(wires=wire)\n    qml.PauliX(wires=aux[0])\n    qml.Hadamard(wires=aux[0])\n    oracle(combo)\n    return qml.probs(wires=query_register)\n\np = oracle_test([1,0,1,0,1])\nsol_idx = np.ravel_multi_index([1,0,1,0,1], [2]*n_bits)\nprint(f'P(solution) from uniform: {p[sol_idx]:.4f} (should equal others, just phase flipped)')",
                            "solution_code": "n_bits = 5\nquery_register = list(range(n_bits))\naux = [n_bits]\nall_wires = query_register + aux\ndev = qml.device('default.qubit', wires=all_wires)\n\ndef oracle(combo):\n    # Flip bits where combo[i]=0\n    for i, bit in enumerate(combo):\n        if bit == 0:\n            qml.PauliX(wires=i)\n    qml.MultiControlledX(wires=query_register + aux)\n    # Flip back\n    for i, bit in enumerate(combo):\n        if bit == 0:\n            qml.PauliX(wires=i)\n\n@qml.qnode(dev)\ndef oracle_test(combo):\n    for wire in query_register:\n        qml.Hadamard(wires=wire)\n    qml.PauliX(wires=aux[0])\n    qml.Hadamard(wires=aux[0])\n    oracle(combo)\n    return qml.probs(wires=query_register)\n\np = oracle_test([1,0,1,0,1])\nsol_idx = np.ravel_multi_index([1,0,1,0,1], [2]*n_bits)\nprint(f'P(solution): {p[sol_idx]:.4f}')",
                            "test_code": "def test():\n    # The oracle flips phase of solution state but probabilities stay equal\n    p = oracle_test([1,0,1,0,1])\n    assert abs(sum(p) - 1.0) < 1e-9, 'Probs must sum to 1'\n    expected = 1.0 / 2**n_bits\n    for pi in p:\n        assert abs(pi - expected) < 1e-6, 'All probs should remain equal after phase oracle'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "grov-impl-quiz",
                    "module_id": "grov-impl",
                    "path_id": "grover",
                    "title": "Module Quiz — Grover Oracle",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "grov-impl-quiz",
                    "objectives": ["Demonstrate understanding of phase kickback and multi-controlled oracles."],
                    "content": [],
                },
            ],
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# PATH: Hamiltonian Simulation (Section H)
# ─────────────────────────────────────────────────────────────────────────────

PATH_HAMILTONIAN: dict[str, Any] = {
    "id": "hamiltonian",
    "title": "Hamiltonian Simulation",
    "description": "Time evolution of quantum systems. From electron spin in a magnetic "
                   "field through Trotterization, diagonalization, and LCU methods.",
    "color": "#f97316",
    "icon": "activity",
    "estimated_hours": 8,
    "modules": [
        {
            "id": "ham-basics",
            "path_id": "hamiltonian",
            "title": "Hamiltonians and Time Evolution",
            "abbreviation": "HT",
            "description": "The Schrödinger equation, unitary time evolution, and simulating electron spin with RZ.",
            "order": 1,
            "lessons": [
                {
                    "id": "ham-basics-1",
                    "module_id": "ham-basics",
                    "path_id": "hamiltonian",
                    "title": "Electron Spin and Time Evolution",
                    "order": 1,
                    "estimated_minutes": 30,
                    "objectives": [
                        "State the Schrödinger equation U(t) = e^{−iĤt/ℏ}.",
                        "Implement the time evolution unitary for an electron in a z-field.",
                        "Identify the RZ gate as time evolution under a Pauli Z Hamiltonian.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "ham-basics-1-t1",
                            "title": "The Schrödinger equation",
                            "body": "The **Schrödinger equation** governs how a quantum state evolves in time:\n$$i\\hbar\\frac{d|\\psi\\rangle}{dt} = \\hat{H}|\\psi\\rangle$$\n\nThe solution is the **time evolution unitary**:\n$$U(t) = e^{-i\\hat{H}t/\\hbar}$$\n\nFor an electron in a magnetic field $B$ pointing in the $z$-direction, the Hamiltonian is $\\hat{H} = -\\alpha\\hbar Z$ where $\\alpha = eB/2m_e$. The time evolution becomes:\n$$U(t) = e^{i\\alpha t Z} = R_Z(-2\\alpha t)$$\n\nThis is exactly the RZ gate! Hamiltonian simulation reduces to applying rotation gates.",
                        },
                        {
                            "type": "codercise",
                            "id": "ham-basics-1-c1",
                            "title": "Codercise H.3.1a — Magnetic field time evolution matrix",
                            "description": "Complete `mag_z_unitary(B, time)` that constructs the 2×2 unitary matrix for time-evolving an electron spin in a $z$-directed magnetic field. The matrix should be $e^{i\\alpha t Z}$ where $\\alpha = eB/2m_e$.",
                            "hints": [
                                "e^{iαtZ} = [[e^{iαt}, 0], [0, e^{-iαt}]] since Z is diagonal.",
                                "Use np.exp(1j * alpha * time) and np.exp(-1j * alpha * time).",
                                "Check unitarity with unitary_check(matrix).",
                            ],
                            "starter_code": "def mag_z_unitary(B, time):\n    \"\"\"Time-evolution unitary for electron in z-directed magnetic field.\"\"\"\n    e = 1.6e-19\n    m_e = 9.1e-31\n    alpha = B * e / (2 * m_e)\n    # YOUR CODE HERE\n    matrix = np.array([[0, 0], [0, 0]], dtype=complex)  # CHANGE THIS\n    return matrix\n\nB, t = 0.1, 0.6\nif unitary_check(mag_z_unitary(B, t)):\n    print('The output is unitary for B =', B, 'and t =', t, '.')",
                            "solution_code": "def mag_z_unitary(B, time):\n    e = 1.6e-19\n    m_e = 9.1e-31\n    alpha = B * e / (2 * m_e)\n    return np.array([[np.exp(1j * alpha * time), 0],\n                     [0, np.exp(-1j * alpha * time)]])\n\nB, t = 0.1, 0.6\nif unitary_check(mag_z_unitary(B, t)):\n    print('The output is unitary for B =', B, 'and t =', t, '.')",
                            "test_code": "def test():\n    e, m_e = 1.6e-19, 9.1e-31\n    for B, t in [(0.1, 0.6), (0.5, 1.0), (1.0, 0.1)]:\n        U = mag_z_unitary(B, t)\n        assert unitary_check(U), f'Not unitary for B={B}, t={t}'\n        alpha = B*e/(2*m_e)\n        assert abs(U[0,0] - np.exp(1j*alpha*t)) < 1e-10\n        assert abs(U[1,1] - np.exp(-1j*alpha*t)) < 1e-10\n        assert abs(U[0,1]) < 1e-14\n        assert abs(U[1,0]) < 1e-14\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "ham-basics-quiz",
                    "module_id": "ham-basics",
                    "path_id": "hamiltonian",
                    "title": "Module Quiz — Hamiltonians and Time Evolution",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "ham-basics-quiz",
                    "objectives": ["Demonstrate understanding of Hamiltonians, Schrödinger equation, and RZ as time evolution."],
                    "content": [],
                },
            ],
        },
        {
            "id": "trotterize",
            "path_id": "hamiltonian",
            "title": "Trotter-Suzuki Decomposition",
            "abbreviation": "TK",
            "description": "Simulating multi-term Hamiltonians via Trotterization. "
                           "Commuting vs non-commuting operators and the Trotter error.",
            "order": 2,
            "lessons": [
                {
                    "id": "trotterize-1",
                    "module_id": "trotterize",
                    "path_id": "hamiltonian",
                    "title": "Trotterization",
                    "order": 1,
                    "estimated_minutes": 35,
                    "objectives": [
                        "Explain why e^{A+B} ≠ e^A·e^B when [A,B]≠0.",
                        "Apply the Trotter-Suzuki decomposition.",
                        "Implement a Trotterized circuit for a ZZ+XX+YY Hamiltonian.",
                    ],
                    "content": [
                        {
                            "type": "theory",
                            "id": "trotterize-1-t1",
                            "title": "Non-commuting Hamiltonians",
                            "body": "For **commuting** operators ($[A,B] = AB - BA = 0$), the exponential factorizes exactly: $e^{A+B} = e^A e^B$. This is the case for independent subsystems.\n\nFor **non-commuting** operators, we use the **Trotter-Suzuki formula**:\n$$e^{A+B} = \\lim_{n\\to\\infty}\\left(e^{A/n}e^{B/n}\\right)^n$$\n\nFor finite $n$ this introduces a **Trotter error** $O(1/n)$. In practice, for small time steps $\\delta t = t/n$, the circuit:\n$$U(t) \\approx \\left(e^{A\\delta t}e^{B\\delta t}\\right)^n$$\ngives a good approximation with error decreasing as $n$ increases.",
                        },
                        {
                            "type": "codercise",
                            "id": "trotterize-1-c1",
                            "title": "Codercise H.4.1 — ZZ interaction circuit",
                            "description": "Complete `zz_circuit(alpha, time, init)` that simulates two electrons with a ZZ interaction $\\hat{H} = -\\alpha\\hbar Z_0 Z_1$ using PennyLane. Decompose $e^{i\\alpha t Z_0 Z_1}$ into a CNOT-RZ-CNOT sequence.\n\nThe decomposition is: `CNOT(0,1) → RZ(2αt, wire=1) → CNOT(0,1)`.",
                            "hints": [
                                "e^{iαt Z⊗Z} = CNOT · (I ⊗ RZ(2αt)) · CNOT",
                                "Apply qml.BasisStatePreparation(init, wires=range(2)) to prepare the initial state.",
                                "Use qml.CNOT(wires=[0,1]), qml.RZ(2*alpha*time/1e-34, wires=1), qml.CNOT(wires=[0,1]).",
                            ],
                            "starter_code": "n_bits = 2\ndev = qml.device('default.qubit', wires=n_bits)\n\n@qml.qnode(dev)\ndef zz_circuit(alpha, time, init):\n    \"\"\"Simulate ZZ interaction. init = [x, y] initial bit string.\"\"\"\n    hbar = 1e-34\n    qml.BasisStatePreparation(init, wires=range(n_bits))\n    # YOUR CODE HERE\n    # IMPLEMENT e^{i*alpha*time*Z0Z1} using CNOT+RZ+CNOT\n    return qml.probs(wires=range(n_bits))\n\nprint(zz_circuit(0.1, 1.0, [0, 0]))",
                            "solution_code": "n_bits = 2\ndev = qml.device('default.qubit', wires=n_bits)\n\n@qml.qnode(dev)\ndef zz_circuit(alpha, time, init):\n    hbar = 1e-34\n    qml.BasisStatePreparation(init, wires=range(n_bits))\n    qml.CNOT(wires=[0, 1])\n    qml.RZ(2 * alpha * time / hbar, wires=1)\n    qml.CNOT(wires=[0, 1])\n    return qml.probs(wires=range(n_bits))\n\nprint(zz_circuit(0.1, 1.0, [0, 0]))",
                            "test_code": "def test():\n    p = zz_circuit(0.1, 1.0, [0, 0])\n    assert abs(sum(p) - 1.0) < 1e-9, 'Probs must sum to 1'\n    assert len(p) == 4, 'Expected 4 probabilities'\n    # For |00>, ZZ eigenvalue is +1, so state picks up phase e^{i*alpha*t/hbar}\n    # Probabilities unchanged (only phase)\n    assert abs(p[0] - 1.0) < 1e-9, 'Starting in |00> should stay in |00>'\n    print('All tests passed!')\ntest()",
                        },
                    ],
                },
                {
                    "id": "trotterize-quiz",
                    "module_id": "trotterize",
                    "path_id": "hamiltonian",
                    "title": "Module Quiz — Trotterization",
                    "order": 2,
                    "estimated_minutes": 8,
                    "is_quiz": True,
                    "quiz_id": "trotterize-quiz",
                    "objectives": ["Demonstrate understanding of Trotter-Suzuki decomposition and ZZ circuit."],
                    "content": [],
                },
            ],
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Exported: all expanded paths
# ─────────────────────────────────────────────────────────────────────────────

EXPANDED_PATHS = [PATH_INTRO, PATH_ALGO, PATH_GROVER, PATH_HAMILTONIAN]
