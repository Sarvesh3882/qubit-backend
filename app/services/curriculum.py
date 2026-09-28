"""
Static curriculum data for QUBIT.
This module defines the full learning content tree:
  LearningPath → Module → Lesson → (Theory blocks + Codercises)

Content is stored here as Python dicts for now; a future iteration
can load from a database or CMS while preserving the same schema.
"""

from __future__ import annotations
from typing import Any
from app.services.curriculum_expanded import EXPANDED_PATHS

# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM
# ─────────────────────────────────────────────────────────────────────────────

CURRICULUM: list[dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════════
    # PATH 1 — Foundations of Quantum Computing
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "fqc",
        "title": "Foundations of Quantum Computing",
        "description": "Become familiar with qubits, quantum circuits, and the basic building blocks of quantum computation.",
        "color": "#6366f1",
        "icon": "atom",
        "estimated_hours": 6,
        "modules": [
            # ── Module IQC ────────────────────────────────────────────────────
            {
                "id": "iqc",
                "path_id": "fqc",
                "title": "Introduction to Quantum Computing",
                "abbreviation": "IQC",
                "description": "Learn the fundamental concepts in quantum computing.",
                "order": 1,
                "lessons": [
                    {
                        "id": "iqc-1",
                        "module_id": "iqc",
                        "path_id": "fqc",
                        "title": "All About Qubits",
                        "order": 1,
                        "estimated_minutes": 20,
                        "video": {
                            "src": "/videos/codebookvid1.mp4",
                            "title": "All About Qubits — video introduction",
                            "description": "A short video introduction to qubits, superposition, and quantum states before you dive into the theory and codercises.",
                        },
                        "objectives": [
                            "Write down a mathematical description of a qubit state in bra-ket notation.",
                            "Define superposition and explain what it means for a qubit.",
                            "State the relationship between amplitudes and measurement probabilities.",
                            "Explain what it means for a quantum state to be normalized.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "iqc-1-t1",
                                "title": "The notion of a qubit",
                                "body": "Quantum computers use **qubits** as their fundamental unit of information. Unlike classical bits that are either 0 or 1, a qubit can exist in a **superposition** of both states simultaneously.\n\nA qubit state is written in *bra-ket* notation as:\n$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$\nwhere $\\alpha$ and $\\beta$ are complex *amplitudes* satisfying the normalization condition:\n$$|\\alpha|^2 + |\\beta|^2 = 1$$\nThe values $|\\alpha|^2$ and $|\\beta|^2$ give the **probabilities** of measuring the qubit in state $|0\\rangle$ or $|1\\rangle$ respectively.",
                            },
                            {
                                "type": "theory",
                                "id": "iqc-1-t2",
                                "title": "Measurement and collapse",
                                "body": "When we **measure** a qubit, its superposition collapses to a definite classical state. If the qubit is in state $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$, measuring it gives:\n- Outcome $|0\\rangle$ with probability $|\\alpha|^2$\n- Outcome $|1\\rangle$ with probability $|\\beta|^2$\n\nAfter measurement, the qubit is **no longer** in superposition — it has collapsed to whichever outcome was observed. This irreversibility is a key feature of quantum mechanics.",
                            },
                            {
                                "type": "codercise",
                                "id": "iqc-1-c1",
                                "title": "Codercise I.1.1 — Normalizing a quantum state",
                                "description": "You are given an unnormalized vector\n$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle, \\quad |\\alpha|^2 + |\\beta|^2 \\neq 1.$$\nComplete the function `normalize_state` so that, given $\\alpha$ and $\\beta$, it returns a normalized state $|\\psi'\\rangle$ satisfying $|\\alpha'|^2 + |\\beta'|^2 = 1$.",
                                "hints": [
                                    "The norm of a vector is $\\sqrt{|\\alpha|^2 + |\\beta|^2}$.",
                                    "Divide both amplitudes by the norm.",
                                ],
                                "starter_code": "import numpy as np\n\n# The computational basis states\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\n\ndef normalize_state(alpha, beta):\n    \"\"\"Normalize the quantum state |psi> = alpha|0> + beta|1>.\n    \n    Args:\n        alpha (complex): amplitude for |0>\n        beta  (complex): amplitude for |1>\n    \n    Returns:\n        np.ndarray: normalized state vector of length 2\n    \"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\n\ndef normalize_state(alpha, beta):\n    norm = np.sqrt(abs(alpha)**2 + abs(beta)**2)\n    return np.array([alpha / norm, beta / norm])\n",
                                "test_code": "def test_normalize_state():\n    import numpy as np\n    state = normalize_state(3, 4)\n    assert abs(np.linalg.norm(state) - 1.0) < 1e-9, 'State is not normalized'\n    state2 = normalize_state(1+1j, 1-1j)\n    assert abs(np.linalg.norm(state2) - 1.0) < 1e-9, 'Complex state is not normalized'\n    print('All tests passed!')\n\ntest_normalize_state()\n",
                            },
                            {
                                "type": "codercise",
                                "id": "iqc-1-c2",
                                "title": "Codercise I.1.2 — Inner product and orthonormal bases",
                                "description": "The **inner product** of two states $|\\phi\\rangle$ and $|\\psi\\rangle$ is $\\langle\\phi|\\psi\\rangle$. Two states are **orthogonal** if their inner product is zero.\n\nComplete `inner_product` and verify that $|0\\rangle$ and $|1\\rangle$ are orthogonal.",
                                "hints": [
                                    "The inner product is $\\langle\\phi|\\psi\\rangle = \\sum_i \\phi_i^* \\psi_i$.",
                                    "Use `np.vdot` or `np.dot(phi.conj(), psi)`.",
                                ],
                                "starter_code": "import numpy as np\n\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\n\ndef inner_product(phi, psi):\n    \"\"\"Compute the inner product <phi|psi>.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\nket_0 = np.array([1, 0], dtype=complex)\nket_1 = np.array([0, 1], dtype=complex)\n\ndef inner_product(phi, psi):\n    return np.vdot(phi, psi)\n",
                                "test_code": "def test_inner_product():\n    import numpy as np\n    assert abs(inner_product(ket_0, ket_1)) < 1e-9, '|0> and |1> should be orthogonal'\n    assert abs(inner_product(ket_0, ket_0) - 1.0) < 1e-9, '<0|0> should be 1'\n    print('All tests passed!')\n\ntest_inner_product()\n",
                            },
                            {
                                "type": "codercise",
                                "id": "iqc-1-c3",
                                "title": "Codercise I.1.3 — Sampling measurement outcomes",
                                "description": "Given a normalized state $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$, simulate `num_shots` measurements and return an array of outcomes ('0' or '1') sampled according to the Born rule.",
                                "hints": [
                                    "The probability of measuring $|0\\rangle$ is $|\\alpha|^2$.",
                                    "Use `np.random.choice` or `np.random.binomial`.",
                                ],
                                "starter_code": "import numpy as np\n\ndef sample_measurements(alpha, beta, num_shots=100):\n    \"\"\"Sample measurement outcomes from state alpha|0> + beta|1>.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef sample_measurements(alpha, beta, num_shots=100):\n    prob_0 = abs(alpha)**2\n    outcomes = np.random.choice(['0', '1'], size=num_shots, p=[prob_0, 1-prob_0])\n    return outcomes\n",
                                "test_code": "def test_sampling():\n    import numpy as np\n    outcomes = sample_measurements(1/np.sqrt(2), 1/np.sqrt(2), num_shots=10000)\n    frac_0 = np.sum(outcomes == '0') / len(outcomes)\n    assert abs(frac_0 - 0.5) < 0.03, f'Expected ~0.5, got {frac_0}'\n    print('All tests passed!')\n\ntest_sampling()\n",
                            },
                        ],
                    },
                    {
                        "id": "iqc-2",
                        "module_id": "iqc",
                        "path_id": "fqc",
                        "title": "Quantum Circuits",
                        "order": 2,
                        "estimated_minutes": 25,
                        "video": {
                            "src": "/videos/codebookvid2.mp4",
                            "title": "Quantum Circuits — video walkthrough",
                            "description": "Walkthrough of quantum circuit structure, gate notation, and how to build your first circuit in Qiskit.",
                        },
                        "objectives": [
                            "Describe the structure of a quantum circuit.",
                            "Identify and apply single-qubit gates: H, X, Y, Z, S, T.",
                            "Build a simple circuit and trace its state evolution.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "iqc-2-t1",
                                "title": "What is a quantum circuit?",
                                "body": "A **quantum circuit** is a sequence of quantum operations (gates) applied to a set of qubits. Reading left to right, each gate transforms the quantum state.\n\nCircuits are the fundamental programming model for gate-based quantum computers. Every quantum algorithm can be expressed as a circuit.\n\nIn Qiskit:\n```python\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(2)  # 2-qubit circuit\nqc.h(0)               # Hadamard on qubit 0\nqc.cx(0, 1)           # CNOT: control=0, target=1\n```",
                            },
                            {
                                "type": "theory",
                                "id": "iqc-2-t2",
                                "title": "The Hadamard gate",
                                "body": "The **Hadamard gate** $H$ creates superposition from a basis state:\n$$H|0\\rangle = \\frac{|0\\rangle + |1\\rangle}{\\sqrt{2}} = |+\\rangle$$\n$$H|1\\rangle = \\frac{|0\\rangle - |1\\rangle}{\\sqrt{2}} = |-\\rangle$$\n\nAs a matrix:\n$$H = \\frac{1}{\\sqrt{2}}\\begin{pmatrix}1 & 1 \\\\ 1 & -1\\end{pmatrix}$$\n\nApplying $H$ twice returns the qubit to its original state: $H^2 = I$.",
                            },
                            {
                                "type": "codercise",
                                "id": "iqc-2-c1",
                                "title": "Codercise I.2.1 — Applying a gate",
                                "description": "Complete `apply_gate` to apply a 2×2 unitary matrix $U$ to a qubit state vector $|\\psi\\rangle$.",
                                "hints": ["Matrix-vector multiplication: $U|\\psi\\rangle$."],
                                "starter_code": "import numpy as np\n\ndef apply_gate(U, psi):\n    \"\"\"Apply unitary U to qubit state psi.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef apply_gate(U, psi):\n    return U @ psi\n",
                                "test_code": "def test_apply_gate():\n    import numpy as np\n    H = np.array([[1,1],[1,-1]]) / np.sqrt(2)\n    ket_0 = np.array([1, 0], dtype=complex)\n    result = apply_gate(H, ket_0)\n    expected = np.array([1/np.sqrt(2), 1/np.sqrt(2)])\n    assert np.allclose(result, expected), f'Got {result}'\n    print('All tests passed!')\n\ntest_apply_gate()\n",
                            },
                        ],
                    },
                    {
                        "id": "iqc-3",
                        "module_id": "iqc",
                        "path_id": "fqc",
                        "title": "Unitary Matrices",
                        "order": 3,
                        "estimated_minutes": 20,
                        "objectives": [
                            "Explain why quantum gates must be unitary.",
                            "Verify that a matrix is unitary.",
                            "Construct simple unitary matrices from rotations.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "iqc-3-t1",
                                "title": "Unitarity and quantum evolution",
                                "body": "Every quantum gate is represented by a **unitary matrix** $U$, satisfying:\n$$UU^\\dagger = U^\\dagger U = I$$\n\nThis guarantees two things:\n1. **Reversibility** — quantum evolution can always be undone.\n2. **Norm preservation** — the total probability remains 1.\n\nThe Pauli matrices $X$, $Y$, $Z$ and the Hadamard $H$ are all unitary and Hermitian ($U = U^\\dagger$):\n$$X = \\begin{pmatrix}0 & 1 \\\\ 1 & 0\\end{pmatrix}, \\quad Z = \\begin{pmatrix}1 & 0 \\\\ 0 & -1\\end{pmatrix}$$",
                            },
                            {
                                "type": "codercise",
                                "id": "iqc-3-c1",
                                "title": "Codercise I.3.1 — Verify unitarity",
                                "description": "Complete `is_unitary` to check whether a given matrix $U$ is unitary (i.e., $UU^\\dagger \\approx I$).",
                                "hints": ["Compute `U @ U.conj().T` and check if it's close to the identity."],
                                "starter_code": "import numpy as np\n\ndef is_unitary(U):\n    \"\"\"Return True if U is unitary.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef is_unitary(U):\n    n = U.shape[0]\n    return np.allclose(U @ U.conj().T, np.eye(n))\n",
                                "test_code": "def test_is_unitary():\n    import numpy as np\n    H = np.array([[1,1],[1,-1]]) / np.sqrt(2)\n    assert is_unitary(H), 'H should be unitary'\n    M = np.array([[1,1],[0,1]], dtype=complex)\n    assert not is_unitary(M), 'Shear matrix should not be unitary'\n    print('All tests passed!')\n\ntest_is_unitary()\n",
                            },
                        ],
                    },
                    {
                        "id": "iqc-quiz",
                        "module_id": "iqc",
                        "path_id": "fqc",
                        "title": "Module Quiz — Intro to QC",
                        "order": 4,
                        "estimated_minutes": 10,
                        "is_quiz": True,
                        "quiz_id": "iqc-quiz",
                        "objectives": [
                            "Demonstrate understanding of superposition, normalization, measurement, and basic gates.",
                        ],
                        "content": [],
                    },
                ],
            },
            # ── Module SQ ─────────────────────────────────────────────────────
            {
                "id": "sq",
                "path_id": "fqc",
                "title": "Single-Qubit Gates",
                "abbreviation": "SQ",
                "description": "Explore the full landscape of single-qubit operations and the Bloch sphere.",
                "order": 2,
                "lessons": [
                    {
                        "id": "sq-1",
                        "module_id": "sq",
                        "path_id": "fqc",
                        "title": "The Bloch Sphere",
                        "order": 1,
                        "estimated_minutes": 25,
                        "objectives": [
                            "Describe every pure qubit state as a point on the Bloch sphere.",
                            "Relate $\\theta$ and $\\phi$ in the Bloch representation to measurement probabilities.",
                            "Identify where common states ($|0\\rangle$, $|1\\rangle$, $|+\\rangle$, $|-\\rangle$) live on the sphere.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "sq-1-t1",
                                "title": "Bloch sphere representation",
                                "body": "Any single-qubit pure state can be written as:\n$$|\\psi\\rangle = \\cos\\frac{\\theta}{2}|0\\rangle + e^{i\\phi}\\sin\\frac{\\theta}{2}|1\\rangle$$\nwhere $\\theta \\in [0,\\pi]$ and $\\phi \\in [0, 2\\pi)$. This maps every qubit state to a unique point on the unit sphere — the **Bloch sphere**.\n\n- North pole: $|0\\rangle$\n- South pole: $|1\\rangle$  \n- Equator: equal superpositions",
                            },
                            {
                                "type": "theory",
                                "id": "sq-1-t2",
                                "title": "Rotations as gates",
                                "body": "Single-qubit gates correspond to rotations of the Bloch sphere.\n\n- $X$ gate: $\\pi$ rotation around the $x$-axis (bit flip)\n- $Z$ gate: $\\pi$ rotation around the $z$-axis (phase flip)\n- $H$ gate: $\\pi/2$ rotation that swaps $x$ and $z$ axes\n- $R_x(\\theta)$: rotation by $\\theta$ around $x$-axis\n\nThis geometric picture is powerful — it makes the effect of any single-qubit gate immediately intuitive.",
                            },
                            {
                                "type": "codercise",
                                "id": "sq-1-c1",
                                "title": "Codercise II.1.1 — Bloch coordinates",
                                "description": "Given a normalized state vector $|\\psi\\rangle = [\\alpha, \\beta]^T$, compute the Bloch sphere coordinates $(x, y, z)$ where $x = 2\\text{Re}(\\alpha^*\\beta)$, $y = 2\\text{Im}(\\alpha^*\\beta)$, $z = |\\alpha|^2 - |\\beta|^2$.",
                                "hints": [
                                    "Use `alpha.conj() * beta` for the off-diagonal of the density matrix.",
                                ],
                                "starter_code": "import numpy as np\n\ndef bloch_coordinates(state):\n    \"\"\"Return (x, y, z) Bloch coordinates for a single qubit state.\"\"\"\n    alpha, beta = state[0], state[1]\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef bloch_coordinates(state):\n    alpha, beta = state[0], state[1]\n    x = 2 * (alpha.conj() * beta).real\n    y = 2 * (alpha.conj() * beta).imag\n    z = abs(alpha)**2 - abs(beta)**2\n    return x, y, z\n",
                                "test_code": "def test_bloch():\n    import numpy as np\n    x, y, z = bloch_coordinates(np.array([1, 0], dtype=complex))\n    assert abs(z - 1.0) < 1e-9, 'North pole z should be 1'\n    x, y, z = bloch_coordinates(np.array([0, 1], dtype=complex))\n    assert abs(z + 1.0) < 1e-9, 'South pole z should be -1'\n    print('All tests passed!')\n\ntest_bloch()\n",
                            },
                        ],
                    },
                    {
                        "id": "sq-2",
                        "module_id": "sq",
                        "path_id": "fqc",
                        "title": "Rotation Gates",
                        "order": 2,
                        "estimated_minutes": 20,
                        "objectives": [
                            "Apply $R_x$, $R_y$, $R_z$ rotation gates.",
                            "Express any single-qubit gate as a product of rotations.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "sq-2-t1",
                                "title": "Parametric rotation gates",
                                "body": "The rotation gates are continuous-parameter generalizations of the Pauli gates:\n\n$$R_x(\\theta) = e^{-i\\theta X/2} = \\cos\\frac{\\theta}{2}I - i\\sin\\frac{\\theta}{2}X = \\begin{pmatrix}\\cos\\frac{\\theta}{2} & -i\\sin\\frac{\\theta}{2} \\\\ -i\\sin\\frac{\\theta}{2} & \\cos\\frac{\\theta}{2}\\end{pmatrix}$$\n\nSetting $\\theta = \\pi$ recovers the Pauli $X$ gate (up to global phase). These gates are essential for variational algorithms like VQE and QAOA.",
                            },
                            {
                                "type": "codercise",
                                "id": "sq-2-c1",
                                "title": "Codercise II.2.1 — Implement Rx gate",
                                "description": "Implement the $R_x(\\theta)$ gate matrix.",
                                "hints": ["$R_x(\\theta) = \\cos(\\theta/2)I - i\\sin(\\theta/2)X$"],
                                "starter_code": "import numpy as np\n\ndef rx_gate(theta):\n    \"\"\"Return the 2x2 Rx(theta) matrix.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef rx_gate(theta):\n    c = np.cos(theta / 2)\n    s = np.sin(theta / 2)\n    return np.array([[c, -1j*s], [-1j*s, c]])\n",
                                "test_code": "def test_rx():\n    import numpy as np\n    Rx = rx_gate(np.pi)\n    X = np.array([[0,1],[1,0]])\n    assert np.allclose(Rx, -1j * X), f'Rx(pi) should equal -iX, got {Rx}'\n    print('All tests passed!')\n\ntest_rx()\n",
                            },
                        ],
                    },
                    {
                        "id": "sq-quiz",
                        "module_id": "sq",
                        "path_id": "fqc",
                        "title": "Module Quiz — Single-Qubit Gates",
                        "order": 3,
                        "estimated_minutes": 10,
                        "is_quiz": True,
                        "quiz_id": "sq-quiz",
                        "objectives": [
                            "Demonstrate understanding of the Bloch sphere and rotation gates.",
                        ],
                        "content": [],
                    },
                ],
            },
            # ── Module MQ ─────────────────────────────────────────────────────
            {
                "id": "mq",
                "path_id": "fqc",
                "title": "Multi-Qubit Systems",
                "abbreviation": "MQ",
                "description": "Learn how multiple qubits combine and create entanglement.",
                "order": 3,
                "lessons": [
                    {
                        "id": "mq-1",
                        "module_id": "mq",
                        "path_id": "fqc",
                        "title": "Tensor Products & Multi-Qubit States",
                        "order": 1,
                        "estimated_minutes": 30,
                        "objectives": [
                            "Construct multi-qubit state spaces using the tensor product.",
                            "Write out the computational basis for 2 and 3-qubit systems.",
                            "Identify separable and entangled states.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "mq-1-t1",
                                "title": "Combining qubits",
                                "body": "When two qubits are combined, the joint state space is the **tensor product** of the individual spaces. A 2-qubit system has 4 basis states: $|00\\rangle, |01\\rangle, |10\\rangle, |11\\rangle$.\n\nA general 2-qubit state is:\n$$|\\psi\\rangle = \\alpha_{00}|00\\rangle + \\alpha_{01}|01\\rangle + \\alpha_{10}|10\\rangle + \\alpha_{11}|11\\rangle$$\nwith $\\sum|\\alpha_{ij}|^2 = 1$. An $n$-qubit system has $2^n$ basis states — the source of quantum computational power.",
                            },
                            {
                                "type": "theory",
                                "id": "mq-1-t2",
                                "title": "Entanglement",
                                "body": "A state is **entangled** if it cannot be written as a product of individual qubit states. The Bell state:\n$$|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$$\nis maximally entangled — measuring one qubit instantly determines the other, regardless of distance.\n\nCreate it with:\n```python\nqc = QuantumCircuit(2)\nqc.h(0)       # superposition on qubit 0  \nqc.cx(0, 1)   # CNOT entangles the pair\n```",
                            },
                            {
                                "type": "codercise",
                                "id": "mq-1-c1",
                                "title": "Codercise III.1.1 — Tensor product",
                                "description": "Implement `tensor_product` that takes two state vectors and returns their tensor product (Kronecker product).",
                                "hints": ["Use `np.kron(a, b)`."],
                                "starter_code": "import numpy as np\n\ndef tensor_product(psi_a, psi_b):\n    \"\"\"Return the tensor product |psi_a> ⊗ |psi_b>.\"\"\"\n    # FILL IN YOUR CODE BELOW\n    pass\n",
                                "solution_code": "import numpy as np\n\ndef tensor_product(psi_a, psi_b):\n    return np.kron(psi_a, psi_b)\n",
                                "test_code": "def test_tensor():\n    import numpy as np\n    ket_0 = np.array([1, 0])\n    ket_1 = np.array([0, 1])\n    ket_01 = tensor_product(ket_0, ket_1)\n    expected = np.array([0, 1, 0, 0])\n    assert np.allclose(ket_01, expected), f'|01> should be {expected}, got {ket_01}'\n    print('All tests passed!')\n\ntest_tensor()\n",
                            },
                        ],
                    },
                    {
                        "id": "mq-2",
                        "module_id": "mq",
                        "path_id": "fqc",
                        "title": "The CNOT Gate & Bell States",
                        "order": 2,
                        "estimated_minutes": 25,
                        "objectives": [
                            "Apply the CNOT gate and describe its action on basis states.",
                            "Prepare all four Bell states.",
                            "Understand why Bell states are maximally entangled.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "mq-2-t1",
                                "title": "The CNOT gate",
                                "body": "The **CNOT** (controlled-NOT) gate flips the target qubit if and only if the control qubit is $|1\\rangle$:\n\n$$\\text{CNOT}|00\\rangle = |00\\rangle, \\quad \\text{CNOT}|01\\rangle = |01\\rangle$$\n$$\\text{CNOT}|10\\rangle = |11\\rangle, \\quad \\text{CNOT}|11\\rangle = |10\\rangle$$\n\nCombined with single-qubit gates, CNOT forms a **universal gate set** — any quantum computation can be decomposed into CNOT and single-qubit gates.",
                            },
                            {
                                "type": "codercise",
                                "id": "mq-2-c1",
                                "title": "Codercise III.2.1 — Prepare a Bell state",
                                "description": "Create a Qiskit circuit that prepares the Bell state $|\\Phi^+\\rangle = (|00\\rangle + |11\\rangle)/\\sqrt{2}$.",
                                "hints": [
                                    "Apply H to qubit 0, then CNOT with control=0, target=1.",
                                ],
                                "starter_code": "from qiskit import QuantumCircuit\n\ndef prepare_bell_state():\n    \"\"\"Return a QuantumCircuit that prepares |Phi+>.\"\"\"\n    qc = QuantumCircuit(2)\n    # FILL IN YOUR CODE BELOW\n    return qc\n",
                                "solution_code": "from qiskit import QuantumCircuit\n\ndef prepare_bell_state():\n    qc = QuantumCircuit(2)\n    qc.h(0)\n    qc.cx(0, 1)\n    return qc\n",
                                "test_code": "def test_bell():\n    from qiskit import QuantumCircuit\n    from qiskit_aer import AerSimulator\n    from qiskit import transpile\n    import numpy as np\n    qc = prepare_bell_state()\n    qc.save_statevector()\n    sim = AerSimulator(method='statevector')\n    t = transpile(qc, sim)\n    sv = sim.run(t).result().get_statevector(t)\n    expected = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])\n    assert np.allclose(np.abs(sv), np.abs(expected)), 'Bell state mismatch'\n    print('All tests passed!')\n\ntest_bell()\n",
                            },
                        ],
                    },
                    {
                        "id": "mq-quiz",
                        "module_id": "mq",
                        "path_id": "fqc",
                        "title": "Module Quiz — Multi-Qubit Systems",
                        "order": 3,
                        "estimated_minutes": 10,
                        "is_quiz": True,
                        "quiz_id": "mq-quiz",
                        "objectives": [
                            "Demonstrate understanding of entanglement, Bell states, and the CNOT gate.",
                        ],
                        "content": [],
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # PATH 2 — Foundations of Quantum Algorithms
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "fqa",
        "title": "Foundations of Quantum Algorithms",
        "description": "Explore quantum algorithms that offer computational advantages over classical methods.",
        "color": "#8b5cf6",
        "icon": "zap",
        "estimated_hours": 8,
        "modules": [
            {
                "id": "qalgo-dj",
                "path_id": "fqa",
                "title": "Deutsch-Jozsa Algorithm",
                "abbreviation": "DJ",
                "description": "The first quantum algorithm to demonstrate exponential speedup.",
                "order": 1,
                "lessons": [
                    {
                        "id": "dj-1",
                        "module_id": "qalgo-dj",
                        "path_id": "fqa",
                        "title": "The Deutsch-Jozsa Problem",
                        "order": 1,
                        "estimated_minutes": 30,
                        "objectives": [
                            "State the Deutsch-Jozsa problem.",
                            "Explain why classical computers need exponentially many queries.",
                            "Trace through the quantum algorithm step by step.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "dj-1-t1",
                                "title": "Problem statement",
                                "body": "Given a function $f:\\{0,1\\}^n \\to \\{0,1\\}$ promised to be either **constant** (same output for all inputs) or **balanced** (exactly half 0s and half 1s), determine which case applies.\n\nClassically this requires $2^{n-1}+1$ queries in the worst case. The Deutsch-Jozsa algorithm solves it with **just one query** — the first demonstration of exponential quantum speedup.",
                            },
                            {
                                "type": "theory",
                                "id": "dj-1-t2",
                                "title": "The quantum algorithm",
                                "body": "The algorithm:\n1. Start all qubits in $|0\\rangle$, ancilla in $|1\\rangle$\n2. Apply $H^{\\otimes n+1}$ to create uniform superposition\n3. Apply the oracle $U_f$\n4. Apply $H^{\\otimes n}$ to input register\n5. Measure input register\n\nIf all measurements are $|0\\rangle$, the function is **constant**. Any other result means **balanced**.",
                            },
                            {
                                "type": "codercise",
                                "id": "dj-1-c1",
                                "title": "Codercise IV.1.1 — Implement the Deutsch-Jozsa circuit",
                                "description": "Build a Qiskit circuit that implements the Deutsch-Jozsa algorithm for a 2-qubit input ($n=2$).\n\nUse the **constant oracle** $U_f^{\\text{const}}$ which applies nothing (constant-zero function).\n\nYour circuit should:\n1. Initialise 3 qubits: 2 input + 1 ancilla\n2. Set ancilla to $|1\\rangle$ (apply X)\n3. Apply H to all qubits\n4. Apply the oracle (identity for constant-zero)\n5. Apply H to the 2 input qubits\n6. Measure the 2 input qubits\n\nA constant function should give $|00\\rangle$ with probability 1.",
                                "hints": [
                                    "Use `QuantumCircuit(3, 2)` — 3 qubits, 2 classical bits.",
                                    "Apply `qc.x(2)` to set the ancilla qubit (index 2) to $|1\\rangle$ before the first H layer.",
                                    "For the constant oracle, simply do nothing — apply no gates between the two H layers.",
                                    "Measure only qubits 0 and 1 into classical bits 0 and 1.",
                                ],
                                "starter_code": "from qiskit import QuantumCircuit\n\ndef deutsch_jozsa_constant(n=2):\n    \"\"\"Build a Deutsch-Jozsa circuit for the constant-zero oracle.\n    \n    Returns:\n        QuantumCircuit: n input qubits + 1 ancilla, n classical bits\n    \"\"\"\n    qc = QuantumCircuit(n + 1, n)\n    # FILL IN YOUR CODE BELOW\n    # 1. Set ancilla to |1>\n    # 2. Apply H to all qubits\n    # 3. Constant oracle — nothing to do\n    # 4. Apply H to input qubits only\n    # 5. Measure input qubits\n    return qc\n",
                                "solution_code": "from qiskit import QuantumCircuit\n\ndef deutsch_jozsa_constant(n=2):\n    qc = QuantumCircuit(n + 1, n)\n    qc.x(n)                  # ancilla to |1>\n    qc.h(range(n + 1))       # H on all\n    # constant oracle: no gates\n    qc.h(range(n))           # H on input register\n    qc.measure(range(n), range(n))\n    return qc\n",
                                "test_code": "def test_dj_constant():\n    from qiskit import QuantumCircuit, transpile\n    from qiskit_aer import AerSimulator\n    qc = deutsch_jozsa_constant(n=2)\n    assert qc.num_qubits == 3, 'Expected 3 qubits'\n    assert qc.num_clbits == 2, 'Expected 2 classical bits'\n    sim = AerSimulator()\n    t = transpile(qc, sim)\n    result = sim.run(t, shots=256).result()\n    counts = result.get_counts(t)\n    # Constant function → all measurements should be 00\n    assert '00' in counts, 'Expected |00> for constant function'\n    assert counts.get('00', 0) == 256, f'Expected all 00, got {counts}'\n    print('All tests passed!')\n\ntest_dj_constant()\n",
                            },
                        ],
                    },
                    {
                        "id": "dj-quiz",
                        "module_id": "qalgo-dj",
                        "path_id": "fqa",
                        "title": "Module Quiz — Deutsch-Jozsa",
                        "order": 2,
                        "estimated_minutes": 10,
                        "is_quiz": True,
                        "quiz_id": "dj-quiz",
                        "objectives": [
                            "Demonstrate understanding of the Deutsch-Jozsa problem and speedup.",
                            "Identify correct circuit steps and measurement outcomes.",
                        ],
                        "content": [],
                    },
                ],
            },
            {
                "id": "qalgo-grover",
                "path_id": "fqa",
                "title": "Grover's Search Algorithm",
                "abbreviation": "GR",
                "description": "Quadratic speedup for unstructured search problems.",
                "order": 2,
                "lessons": [
                    {
                        "id": "grover-1",
                        "module_id": "qalgo-grover",
                        "path_id": "fqa",
                        "title": "Amplitude Amplification",
                        "order": 1,
                        "estimated_minutes": 35,
                        "objectives": [
                            "Explain Grover's algorithm and its $O(\\sqrt{N})$ complexity.",
                            "Identify the oracle and diffusion operator.",
                            "Determine the optimal number of Grover iterations.",
                        ],
                        "content": [
                            {
                                "type": "theory",
                                "id": "grover-1-t1",
                                "title": "Searching without structure",
                                "body": "Given an unsorted database of $N$ items, find the item satisfying some criterion. Classically this requires $O(N)$ queries. Grover's algorithm needs only $O(\\sqrt{N})$ queries — a quadratic speedup.\n\nThe algorithm amplifies the amplitude of the target state while suppressing others through repeated application of two operators:\n1. **Oracle** $U_\\omega$: marks the target by flipping its phase\n2. **Diffusion** $D = 2|s\\rangle\\langle s| - I$: reflects around the mean amplitude",
                            },
                            {
                                "type": "theory",
                                "id": "grover-1-t2",
                                "title": "Optimal number of iterations",
                                "body": "The optimal number of Grover iterations is $\\lfloor\\frac{\\pi}{4}\\sqrt{N}\\rfloor$. After this many iterations the target state has amplitude $\\approx 1$ and is measured with near-certainty.\n\nOver-iterating causes the amplitude to overshoot and **decrease** again — the success probability oscillates sinusoidally. For $N = 4$ (2 qubits), exactly **1 iteration** is optimal.",
                            },
                            {
                                "type": "codercise",
                                "id": "grover-1-c1",
                                "title": "Codercise IV.2.1 — Build Grover's circuit for 2 qubits",
                                "description": "Implement one iteration of Grover's algorithm for $N = 4$ (2 qubits), searching for the target state $|11\\rangle$.\n\nThe **oracle** for target $|11\\rangle$ applies a controlled-Z (CZ) gate between the two qubits — this adds a $-1$ phase to $|11\\rangle$ only.\n\nThe **diffusion operator** for 2 qubits is:\n1. Apply $H$ to both qubits\n2. Apply $X$ to both qubits  \n3. Apply CZ\n4. Apply $X$ to both qubits\n5. Apply $H$ to both qubits\n\nAfter 1 Grover iteration starting from the uniform superposition, $|11\\rangle$ should be measured with probability 1.",
                                "hints": [
                                    "Start with `qc.h([0, 1])` to create the uniform superposition.",
                                    "The oracle for $|11\\rangle$ is simply `qc.cz(0, 1)`.",
                                    "For the diffusion: H → X → CZ → X → H on both qubits.",
                                    "Measure both qubits at the end.",
                                ],
                                "starter_code": "from qiskit import QuantumCircuit\n\ndef grover_2qubit():\n    \"\"\"One iteration of Grover's algorithm targeting |11> on 2 qubits.\"\"\"\n    qc = QuantumCircuit(2, 2)\n    # 1. Uniform superposition\n    # FILL IN YOUR CODE BELOW\n    \n    # 2. Oracle for |11>\n    \n    # 3. Diffusion operator\n    \n    # 4. Measure\n    return qc\n",
                                "solution_code": "from qiskit import QuantumCircuit\n\ndef grover_2qubit():\n    qc = QuantumCircuit(2, 2)\n    # Uniform superposition\n    qc.h([0, 1])\n    # Oracle for |11>: CZ adds phase -1 to |11>\n    qc.cz(0, 1)\n    # Diffusion operator\n    qc.h([0, 1])\n    qc.x([0, 1])\n    qc.cz(0, 1)\n    qc.x([0, 1])\n    qc.h([0, 1])\n    # Measure\n    qc.measure([0, 1], [0, 1])\n    return qc\n",
                                "test_code": "def test_grover():\n    from qiskit import transpile\n    from qiskit_aer import AerSimulator\n    qc = grover_2qubit()\n    assert qc.num_qubits == 2, 'Expected 2 qubits'\n    sim = AerSimulator()\n    t = transpile(qc, sim)\n    result = sim.run(t, shots=512).result()\n    counts = result.get_counts(t)\n    # After 1 Grover iteration, |11> should dominate\n    total = sum(counts.values())\n    prob_11 = counts.get('11', 0) / total\n    assert prob_11 > 0.9, f'Expected |11> with prob > 0.9, got {prob_11:.2f}. Counts: {counts}'\n    print('All tests passed!')\n\ntest_grover()\n",
                            },
                        ],
                    },
                    {
                        "id": "grover-quiz",
                        "module_id": "qalgo-grover",
                        "path_id": "fqa",
                        "title": "Module Quiz — Grover's Search",
                        "order": 2,
                        "estimated_minutes": 10,
                        "is_quiz": True,
                        "quiz_id": "grover-quiz",
                        "objectives": [
                            "Demonstrate understanding of amplitude amplification and Grover complexity.",
                            "Reason about oracle and diffusion operator effects.",
                        ],
                        "content": [],
                    },
                ],
            },
        ],
    },
]

# Extend with expanded paths from the Xanadu Quantum Codebook source
CURRICULUM.extend(EXPANDED_PATHS)



def get_all_paths() -> list[dict]:
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "description": p["description"],
            "color": p["color"],
            "icon": p["icon"],
            "estimated_hours": p["estimated_hours"],
            "module_count": len(p["modules"]),
            "lesson_count": sum(len(m["lessons"]) for m in p["modules"]),
        }
        for p in CURRICULUM
    ]


def get_path(path_id: str) -> dict | None:
    return next((p for p in CURRICULUM if p["id"] == path_id), None)


def get_module(path_id: str, module_id: str) -> dict | None:
    path = get_path(path_id)
    if not path:
        return None
    return next((m for m in path["modules"] if m["id"] == module_id), None)


def get_lesson(path_id: str, module_id: str, lesson_id: str) -> dict | None:
    module = get_module(path_id, module_id)
    if not module:
        return None
    return next((l for l in module["lessons"] if l["id"] == lesson_id), None)


def get_all_lessons_flat() -> list[dict]:
    lessons = []
    for path in CURRICULUM:
        for module in path["modules"]:
            for lesson in module["lessons"]:
                lessons.append({**lesson, "path_title": path["title"], "module_title": module["title"]})
    return lessons


def get_content_lessons_flat() -> list[dict]:
    """Return only non-quiz lessons (lessons with actual codercise/theory content)."""
    return [l for l in get_all_lessons_flat() if not l.get("is_quiz")]


def get_quiz_lessons_flat() -> list[dict]:
    """Return only quiz lessons."""
    return [l for l in get_all_lessons_flat() if l.get("is_quiz")]