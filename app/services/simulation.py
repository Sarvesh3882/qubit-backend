"""
Quantum simulation service — multi-framework dispatcher.

Supported simulation backends:
  qiskit     — Qiskit 2.x + Qiskit Aer  (always available)
  pennylane  — PennyLane default.qubit   (installed, pure Python)
  openqasm3  — Qiskit QASM3 loader → Aer (always available)
  cirq       — falls back to Qiskit Aer  (cirq not installed)
  qbraid     — falls back to Qiskit Aer  (qbraid runtime not installed)
  qpiai      — falls back to Qiskit Aer  (qpiai not installed)

All engines return the same response shape so the frontend
can render probabilities, statevector, Bloch spheres, and Q-sphere
identically regardless of which simulator ran.
"""
from __future__ import annotations

import math
import traceback
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps as qasm3_dumps
from qiskit_aer import AerSimulator


# ══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════════════════

def _bloch(sv: np.ndarray, qubit: int) -> dict[str, float]:
    """Bloch-sphere (x, y, z) for one qubit via partial trace."""
    n = int(math.log2(len(sv)))
    dm = np.outer(sv, sv.conj())
    axes = list(range(n))
    axes.remove(qubit)
    dm_r = dm.reshape([2] * n + [2] * n)
    for ax in sorted(axes, reverse=True):
        dm_r = np.trace(dm_r, axis1=ax, axis2=ax + n)
        n -= 1
    rho = dm_r.reshape(2, 2)
    return {
        "x": float(2 * rho[0, 1].real),
        "y": float(2 * rho[0, 1].imag),
        "z": float((rho[0, 0] - rho[1, 1]).real),
    }


def _qsphere_points(sv: np.ndarray, num_qubits: int) -> list[dict]:
    return [
        {
            "state": format(i, f"0{num_qubits}b"),
            "prob":  float(abs(a) ** 2),
            "phase": float(np.angle(a)),
        }
        for i, a in enumerate(sv)
    ]


def _std_response(
    sv: np.ndarray,
    counts: dict[str, int],
    num_qubits: int,
    shots: int,
    qasm: str,
    include_statevector: bool,
    simulator_name: str,
) -> dict[str, Any]:
    probabilities = {
        format(i, f"0{num_qubits}b"): float(abs(a) ** 2)
        for i, a in enumerate(sv)
    }
    statevector = [{"re": float(a.real), "im": float(a.imag)} for a in sv]
    bloch_spheres: dict[str, Any] = {}
    if num_qubits <= 8:
        for q in range(num_qubits):
            bloch_spheres[f"q{q}"] = _bloch(sv, q)
    return {
        "success": True,
        "simulator": simulator_name,
        "probabilities": probabilities,
        "counts": counts,
        "statevector": statevector if include_statevector else [],
        "bloch_spheres": bloch_spheres,
        "qsphere": _qsphere_points(sv, num_qubits),
        "circuit_qasm": qasm,
        "num_qubits": num_qubits,
        "shots": shots,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Qiskit / Aer engine  (used by qiskit, qbraid, qpiai, cirq fallback)
# ══════════════════════════════════════════════════════════════════════════════

_GATE_MAP = {
    "H":    lambda qc, q, _: qc.h(q),
    "X":    lambda qc, q, _: qc.x(q),
    "Y":    lambda qc, q, _: qc.y(q),
    "Z":    lambda qc, q, _: qc.z(q),
    "S":    lambda qc, q, _: qc.s(q),
    "T":    lambda qc, q, _: qc.t(q),
    "SDG":  lambda qc, q, _: qc.sdg(q),
    "TDG":  lambda qc, q, _: qc.tdg(q),
    "I":    lambda qc, q, _: qc.id(q),
    "SX":   lambda qc, q, _: qc.sx(q),
    "P":    lambda qc, q, p: qc.p(p[0] if p else 0, q),
    "RX":   lambda qc, q, p: qc.rx(p[0] if p else 0, q),
    "RY":   lambda qc, q, p: qc.ry(p[0] if p else 0, q),
    "RZ":   lambda qc, q, p: qc.rz(p[0] if p else 0, q),
    "CNOT": lambda qc, q, _: qc.cx(q[0], q[1]),
    "CX":   lambda qc, q, _: qc.cx(q[0], q[1]),
    "CZ":   lambda qc, q, _: qc.cz(q[0], q[1]),
    "SWAP": lambda qc, q, _: qc.swap(q[0], q[1]),
    "CCX":  lambda qc, q, _: qc.ccx(q[0], q[1], q[2]),
    "M":    lambda qc, q, _: qc.measure(q, q),
}


def _build_qiskit_circuit(num_qubits: int, gates: list[dict]) -> QuantumCircuit:
    qc = QuantumCircuit(num_qubits)
    for gate in gates:
        name   = gate.get("gate", "").upper()
        qubits = gate.get("qubits", [])
        params = gate.get("params", [])
        fn = _GATE_MAP.get(name)
        if fn is None:
            continue
        if len(qubits) > 1:
            fn(qc, qubits, params)
        elif len(qubits) == 1:
            fn(qc, qubits[0], params)
    return qc


def _run_aer(
    num_qubits: int,
    gates: list[dict],
    shots: int,
    include_statevector: bool,
    simulator_name: str = "Qiskit Aer",
) -> dict[str, Any]:
    """Core Aer runner — shared by Qiskit, Cirq-fallback, qBraid-fallback, QpiAI-fallback."""
    qc = _build_qiskit_circuit(num_qubits, gates)
    sv_sim = AerSimulator(method="statevector")

    # statevector pass (no transpile — avoids NumPy __array__ copy=None bug)
    sv_qc = QuantumCircuit(num_qubits)
    for instr in qc.data:
        sv_qc.append(instr)
    sv_qc.save_statevector()
    sv = sv_sim.run(sv_qc, shots=1).result().get_statevector(sv_qc).data

    # shot-based counts
    meas_qc = QuantumCircuit(num_qubits)
    for instr in qc.data:
        meas_qc.append(instr)
    meas_qc.measure_all()
    raw = sv_sim.run(meas_qc, shots=shots).result().get_counts(meas_qc)
    counts = {k.replace(" ", ""): v for k, v in raw.items()}

    try:
        qasm = qasm3_dumps(qc)
    except Exception:
        qasm = str(qc)

    return _std_response(sv, counts, num_qubits, shots, qasm, include_statevector, simulator_name)


# ══════════════════════════════════════════════════════════════════════════════
# PennyLane engine
# ══════════════════════════════════════════════════════════════════════════════

# PennyLane gate name → (op_class_or_callable, needs_param)
_PL_GATE_MAP = {
    "H":    ("Hadamard",    False),
    "X":    ("PauliX",      False),
    "Y":    ("PauliY",      False),
    "Z":    ("PauliZ",      False),
    "S":    ("S",           False),
    "T":    ("T",           False),
    "SDG":  ("_SDG",        False),   # handled specially
    "TDG":  ("_TDG",        False),   # handled specially
    "SX":   ("SX",          False),
    "I":    ("Identity",    False),
    "RX":   ("RX",          True),
    "RY":   ("RY",          True),
    "RZ":   ("RZ",          True),
    "P":    ("PhaseShift",  True),
    "CNOT": ("CNOT",        False),
    "CX":   ("CNOT",        False),
    "CZ":   ("CZ",          False),
    "SWAP": ("SWAP",        False),
    "CCX":  ("Toffoli",     False),
}


def _run_pennylane(
    num_qubits: int,
    gates: list[dict],
    shots: int,
    include_statevector: bool,
) -> dict[str, Any]:
    import pennylane as qml  # lazy import — only when needed

    dev_sv    = qml.device("default.qubit", wires=num_qubits)
    dev_shots = qml.device("default.qubit", wires=num_qubits, shots=shots)

    def _apply_gates():
        for gate in sorted(gates, key=lambda g: g.get("moment", 0)):
            name   = gate.get("gate", "").upper()
            qubits = gate.get("qubits", [])
            params = gate.get("params", [])

            if name == "M":
                continue  # measurements handled by return statement

            mapping = _PL_GATE_MAP.get(name)
            if mapping is None:
                continue

            op_name, needs_param = mapping

            # Special adjoint gates
            if op_name == "_SDG":
                qml.adjoint(qml.S)(wires=qubits[0])
                continue
            if op_name == "_TDG":
                qml.adjoint(qml.T)(wires=qubits[0])
                continue

            op_cls = getattr(qml, op_name, None)
            if op_cls is None:
                continue

            wires = qubits if len(qubits) > 1 else qubits[0]
            if needs_param and params:
                op_cls(params[0], wires=wires)
            else:
                op_cls(wires=wires)

    # ── statevector ──────────────────────────────────────────────────────────
    @qml.qnode(dev_sv)
    def sv_circuit():
        _apply_gates()
        return qml.state()

    sv_raw = sv_circuit()
    sv = np.array(sv_raw, dtype=complex)

    # ── probabilities from statevector ───────────────────────────────────────
    probs_arr = np.abs(sv) ** 2
    probabilities = {
        format(i, f"0{num_qubits}b"): float(p)
        for i, p in enumerate(probs_arr)
    }

    # ── shot-based counts ─────────────────────────────────────────────────────
    @qml.qnode(dev_shots)
    def shot_circuit():
        _apply_gates()
        return qml.sample(wires=list(range(num_qubits)))

    samples = shot_circuit()
    # samples shape varies:
    #   multi-qubit : (shots, num_qubits) array of 0/1 integers
    #   single-qubit: (shots,)  flat array of 0/1 integers
    if samples.ndim == 1:
        if num_qubits == 1:
            # flat array of 0/1 — each element is one shot result
            from collections import Counter
            raw_counts = Counter(str(int(b)) for b in samples)
        else:
            # single shot edge case — reshape to (1, num_qubits)
            samples = samples.reshape(1, -1)
            from collections import Counter
            raw_counts = Counter(
                "".join(str(int(b)) for b in row) for row in samples
            )
    else:
        from collections import Counter
        raw_counts = Counter(
            "".join(str(int(b)) for b in row) for row in samples
        )
    counts = dict(raw_counts)

    # ── QASM for display (use Qiskit to generate it) ─────────────────────────
    try:
        qc = _build_qiskit_circuit(num_qubits, gates)
        qasm = qasm3_dumps(qc)
    except Exception:
        qasm = "# QASM generation failed"

    return _std_response(sv, counts, num_qubits, shots, qasm, include_statevector, "PennyLane default.qubit")


# ══════════════════════════════════════════════════════════════════════════════
# OpenQASM 3 engine  (load QASM string → Qiskit → Aer)
# ══════════════════════════════════════════════════════════════════════════════

def _run_openqasm3(
    num_qubits: int,
    gates: list[dict],
    shots: int,
    include_statevector: bool,
) -> dict[str, Any]:
    """
    Build an OpenQASM 3 string from the gate list, load it back via
    Qiskit's QASM3 loader, then simulate with Aer.
    This proves the QASM code shown in the editor is actually runnable.
    """
    from qiskit.qasm3 import loads as qasm3_loads

    # Generate QASM string from gates
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        "",
        f"qubit[{num_qubits}] q;",
        f"bit[{num_qubits}]   c;",
        "",
    ]
    _QASM_GATE = {
        "H": "h", "X": "x", "Y": "y", "Z": "z",
        "S": "s", "T": "t", "SDG": "sdg", "TDG": "tdg",
        "SX": "sx", "I": "id",
        "RX": "rx", "RY": "ry", "RZ": "rz", "P": "p",
        "CX": "cx", "CNOT": "cx", "CZ": "cz",
        "SWAP": "swap", "CCX": "ccx",
    }
    for gate in sorted(gates, key=lambda g: g.get("moment", 0)):
        name   = gate.get("gate", "").upper()
        qubits = gate.get("qubits", [])
        params = gate.get("params", [])
        if name == "M":
            lines.append(f"c[{qubits[0]}] = measure q[{qubits[0]}];")
            continue
        qasm_name = _QASM_GATE.get(name)
        if qasm_name is None:
            continue
        q_str = ", ".join(f"q[{i}]" for i in qubits)
        p_str = f"({', '.join(f'{p:.6f}' for p in params)})" if params else ""
        lines.append(f"{qasm_name}{p_str} {q_str};")

    qasm_src = "\n".join(lines)

    try:
        qc_loaded = qasm3_loads(qasm_src)
        num_qubits = qc_loaded.num_qubits
    except Exception:
        # QASM3 loader failed — fall back to Aer directly
        return _run_aer(num_qubits, gates, shots, include_statevector,
                        simulator_name="Qiskit Aer (QASM3 fallback)")

    sv_sim = AerSimulator(method="statevector")

    sv_qc = QuantumCircuit(num_qubits)
    for instr in qc_loaded.data:
        sv_qc.append(instr)
    sv_qc.save_statevector()
    sv = sv_sim.run(sv_qc, shots=1).result().get_statevector(sv_qc).data

    meas_qc = QuantumCircuit(num_qubits)
    for instr in qc_loaded.data:
        meas_qc.append(instr)
    meas_qc.measure_all()
    raw = sv_sim.run(meas_qc, shots=shots).result().get_counts(meas_qc)
    counts = {k.replace(" ", ""): v for k, v in raw.items()}

    return _std_response(sv, counts, num_qubits, shots, qasm_src,
                         include_statevector, "Qiskit Aer via QASM3")


# ══════════════════════════════════════════════════════════════════════════════
# Public dispatcher
# ══════════════════════════════════════════════════════════════════════════════

def run_simulation(
    num_qubits: int,
    gates: list[dict],
    shots: int = 1024,
    include_statevector: bool = True,
    framework: str = "qiskit",
) -> dict[str, Any]:
    """
    Dispatch to the appropriate simulator for the given framework.

    framework values (matching frontend Framework type):
      "qiskit"     → Qiskit Aer statevector
      "pennylane"  → PennyLane default.qubit  (installed)
      "openqasm3"  → Qiskit QASM3 loader → Aer
      "cirq"       → Qiskit Aer  (cirq not installed on server)
      "qbraid"     → Qiskit Aer  (qbraid runtime not installed on server)
      "qpiai"      → Qiskit Aer  (qpiai not installed on server)
    """
    try:
        if framework == "pennylane":
            return _run_pennylane(num_qubits, gates, shots, include_statevector)

        if framework == "openqasm3":
            return _run_openqasm3(num_qubits, gates, shots, include_statevector)

        # qiskit / cirq / qbraid / qpiai / default → Aer
        label_map = {
            "qiskit":    "Qiskit Aer",
            "cirq":      "Qiskit Aer (Cirq code shown — Cirq not on server)",
            "qbraid":    "Qiskit Aer (qBraid code shown — qBraid not on server)",
            "qpiai":     "Qiskit Aer (QpiAI code shown — QpiAI not on server)",
        }
        label = label_map.get(framework, "Qiskit Aer")
        return _run_aer(num_qubits, gates, shots, include_statevector, label)

    except Exception as exc:
        return {
            "success":   False,
            "error":     str(exc),
            "traceback": traceback.format_exc(),
        }
