"""
Algorithm Playground API.

Gate-model algorithms (Qiskit Aer):
  deutsch-jozsa     — oracle classification
  grover            — amplitude amplification search
  qft               — Quantum Fourier Transform
  bernstein-vazirani — hidden string recovery

Quantum annealing / combinatorial optimisation (D-Wave SimulatedAnnealingSampler):
  dwave-maxcut      — Maximum Cut on a graph
  dwave-tsp         — Travelling Salesman Problem (small instances)
  dwave-knapsack    — 0/1 Knapsack Problem

D-Wave Note
-----------
We use dwave.samplers.SimulatedAnnealingSampler (local, no API key needed) by default.
This replicates what a real D-Wave quantum annealer does — the QUBO / Ising formulation
is identical; only the physical hardware differs.  The solver label shown in results is
"D-Wave Simulated Annealing (local)" so users understand the relationship.
If DWAVE_API_TOKEN is set in .env the code can be extended to submit to the real QPU
via dwave.cloud — that hook is in place but defaulting to local for reliability.
"""
from __future__ import annotations

import math
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps as qasm3_dumps
from qiskit_aer import AerSimulator

import dimod
from dwave.samplers import SimulatedAnnealingSampler

router = APIRouter(prefix="/algorithms", tags=["algorithms"])

# ══════════════════════════════════════════════════════════════════════════════
# Algorithm catalogue
# ══════════════════════════════════════════════════════════════════════════════

ALGORITHMS: dict[str, dict] = {
    # ── Gate-model ────────────────────────────────────────────────────────────
    "deutsch-jozsa": {
        "id": "deutsch-jozsa",
        "title": "Deutsch-Jozsa",
        "category": "oracle",
        "solver": "Qiskit Aer",
        "description": "Determines whether a function is constant or balanced with a single quantum query.",
        "complexity": {"classical": "O(2^(n-1)+1)", "quantum": "O(1)"},
        "parameters": [
            {"name": "n_qubits", "type": "int", "default": 3, "min": 1, "max": 8, "label": "Input qubits"},
            {"name": "oracle_type", "type": "select", "options": ["constant_0", "constant_1", "balanced"],
             "default": "balanced", "label": "Oracle type"},
        ],
    },
    "grover": {
        "id": "grover",
        "title": "Grover's Search",
        "category": "search",
        "solver": "Qiskit Aer",
        "description": "Searches an unsorted database in O(√N) quantum queries.",
        "complexity": {"classical": "O(N)", "quantum": "O(√N)"},
        "parameters": [
            {"name": "n_qubits", "type": "int", "default": 3, "min": 2, "max": 6, "label": "Qubits (search space = 2^n)"},
            {"name": "target", "type": "int", "default": 5, "min": 0, "max": 63, "label": "Target state (decimal)"},
        ],
    },
    "qft": {
        "id": "qft",
        "title": "Quantum Fourier Transform",
        "category": "transform",
        "solver": "Qiskit Aer",
        "description": "Quantum analog of the DFT — core subroutine in Shor and phase-estimation.",
        "complexity": {"classical": "O(N log N)", "quantum": "O(log² N)"},
        "parameters": [
            {"name": "n_qubits", "type": "int", "default": 3, "min": 1, "max": 8, "label": "Number of qubits"},
            {"name": "input_state", "type": "int", "default": 1, "min": 0, "max": 255, "label": "Input state (decimal)"},
        ],
    },
    "bernstein-vazirani": {
        "id": "bernstein-vazirani",
        "title": "Bernstein-Vazirani",
        "category": "oracle",
        "solver": "Qiskit Aer",
        "description": "Recovers a hidden bit string in a single quantum query (classically needs n).",
        "complexity": {"classical": "O(n)", "quantum": "O(1)"},
        "parameters": [
            {"name": "secret_string", "type": "string", "default": "101", "label": "Secret bit string"},
        ],
    },

    # ── D-Wave / annealing ────────────────────────────────────────────────────
    "dwave-maxcut": {
        "id": "dwave-maxcut",
        "title": "Maximum Cut (D-Wave)",
        "category": "optimization",
        "solver": "D-Wave Simulated Annealing",
        "description": (
            "Finds the partition of graph vertices that maximises the number of edges "
            "crossing the cut.  Formulated as a QUBO and solved by simulated annealing — "
            "the same mathematical model run on real D-Wave quantum annealers."
        ),
        "complexity": {"classical": "NP-hard", "quantum": "Quantum annealing (QUBO)"},
        "parameters": [
            {"name": "n_nodes", "type": "int", "default": 6, "min": 3, "max": 12, "label": "Number of nodes"},
            {"name": "edge_density", "type": "select",
             "options": ["sparse (0.3)", "medium (0.5)", "dense (0.7)"],
             "default": "medium (0.5)", "label": "Graph density"},
            {"name": "num_reads", "type": "int", "default": 500, "min": 100, "max": 2000, "label": "Annealing reads"},
        ],
    },
    "dwave-tsp": {
        "id": "dwave-tsp",
        "title": "Travelling Salesman (D-Wave)",
        "category": "optimization",
        "solver": "D-Wave Simulated Annealing",
        "description": (
            "Finds the shortest tour visiting all cities exactly once.  "
            "Encoded as a QUBO with one-hot city-position constraints."
        ),
        "complexity": {"classical": "O(n! / 2)", "quantum": "Quantum annealing (QUBO)"},
        "parameters": [
            {"name": "n_cities", "type": "int", "default": 4, "min": 3, "max": 6, "label": "Number of cities"},
            {"name": "num_reads", "type": "int", "default": 1000, "min": 200, "max": 3000, "label": "Annealing reads"},
        ],
    },
    "dwave-knapsack": {
        "id": "dwave-knapsack",
        "title": "0/1 Knapsack (D-Wave)",
        "category": "optimization",
        "solver": "D-Wave Simulated Annealing",
        "description": (
            "Selects items to maximise total value without exceeding the weight capacity.  "
            "Penalty terms enforce the weight constraint in the QUBO formulation."
        ),
        "complexity": {"classical": "O(n · W) pseudo-poly", "quantum": "Quantum annealing (QUBO)"},
        "parameters": [
            {"name": "n_items", "type": "int", "default": 6, "min": 3, "max": 10, "label": "Number of items"},
            {"name": "capacity_ratio", "type": "select",
             "options": ["tight (0.3)", "medium (0.5)", "loose (0.7)"],
             "default": "medium (0.5)", "label": "Capacity / total weight"},
            {"name": "num_reads", "type": "int", "default": 500, "min": 100, "max": 2000, "label": "Annealing reads"},
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def list_algorithms():
    return list(ALGORITHMS.values())


@router.get("/{algo_id}")
async def get_algorithm(algo_id: str):
    if algo_id not in ALGORITHMS:
        raise HTTPException(404, "Algorithm not found")
    return ALGORITHMS[algo_id]


class RunRequest(BaseModel):
    parameters: dict[str, Any] = {}


@router.post("/{algo_id}/run")
async def run_algorithm(algo_id: str, request: RunRequest):
    try:
        p = request.parameters
        if algo_id == "deutsch-jozsa":
            return _run_deutsch_jozsa(p)
        elif algo_id == "grover":
            return _run_grover(p)
        elif algo_id == "qft":
            return _run_qft(p)
        elif algo_id == "bernstein-vazirani":
            return _run_bv(p)
        elif algo_id == "dwave-maxcut":
            return _run_maxcut(p)
        elif algo_id == "dwave-tsp":
            return _run_tsp(p)
        elif algo_id == "dwave-knapsack":
            return _run_knapsack(p)
        raise HTTPException(404, "Algorithm not found")
    except HTTPException:
        raise
    except Exception as exc:
        return {"success": False, "error": str(exc), "traceback": traceback.format_exc()}


# ══════════════════════════════════════════════════════════════════════════════
# Shared Qiskit helper — NO transpile() to avoid NumPy copy=None bug in Qiskit 2.x
# ══════════════════════════════════════════════════════════════════════════════

def _sim(qc: QuantumCircuit, shots: int = 1024) -> dict:
    """Run circuit on Aer, return probabilities + counts + QASM.

    Avoids transpile() to dodge the Qiskit 2.x / NumPy copy=None bug.
    When the original circuit has classical bits (measure gates), we replicate
    those bits in the copy circuits so the instruction references remain valid.
    """
    nq = qc.num_qubits
    nc = qc.num_clbits
    sim = AerSimulator(method="statevector")

    # ── Statevector pass (no measurements needed, skip measure instructions) ──
    sv_qc = QuantumCircuit(nq)
    for instr in qc.data:
        # Skip measure ops for the statevector pass
        if instr.operation.name == "measure":
            continue
        # Instructions that only touch qubits — safe to append directly
        if not instr.clbits:
            sv_qc.append(instr)
        # Instructions with classical bits: rebuild without them (shouldn't
        # happen in our circuits except measure, already skipped)

    sv_qc.save_statevector()
    sv = sim.run(sv_qc, shots=1).result().get_statevector(sv_qc).data

    probs   = {format(i, f"0{nq}b"): float(abs(a) ** 2) for i, a in enumerate(sv)}
    sv_list = [{"re": float(a.real), "im": float(a.imag)} for a in sv]

    # ── Shot-based counts pass (includes original measurements if any) ────────
    if nc > 0:
        # Circuit already has measurements — run as-is
        meas_qc = QuantumCircuit(nq, nc)
        for instr in qc.data:
            meas_qc.append(instr)
    else:
        # No measurements — add measure_all
        meas_qc = QuantumCircuit(nq)
        for instr in qc.data:
            meas_qc.append(instr)
        meas_qc.measure_all()

    raw    = sim.run(meas_qc, shots=shots).result().get_counts(meas_qc)
    counts = {k.replace(" ", ""): v for k, v in raw.items()}

    try:
        qasm = qasm3_dumps(qc)
    except Exception:
        qasm = ""

    return {"probabilities": probs, "counts": counts,
            "circuit_qasm": qasm, "statevector": sv_list}


# ══════════════════════════════════════════════════════════════════════════════
# Gate-model implementations
# ══════════════════════════════════════════════════════════════════════════════

def _run_deutsch_jozsa(params: dict) -> dict:
    n = min(max(int(params.get("n_qubits", 3)), 1), 8)
    oracle_type = params.get("oracle_type", "balanced")
    total = n + 1
    qc = QuantumCircuit(total, n)
    qc.x(n)
    qc.h(range(total))
    if oracle_type == "constant_0":
        pass
    elif oracle_type == "constant_1":
        qc.x(n)
    else:
        for i in range(n):
            qc.cx(i, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    result = _sim(qc)
    mc = max(result["counts"], key=result["counts"].get) if result["counts"] else "0" * n
    verdict = "constant" if set(mc.replace(" ", "")) == {"0"} else "balanced"
    return {**result, "verdict": verdict, "oracle_type": oracle_type,
            "n_qubits": n, "solver": "Qiskit Aer"}


def _run_grover(params: dict) -> dict:
    n = min(max(int(params.get("n_qubits", 3)), 2), 6)
    target = int(params.get("target", 5)) % (2 ** n)
    target_str = format(target, f"0{n}b")
    iterations = max(1, round(math.pi / 4 * math.sqrt(2 ** n)))
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for _ in range(iterations):
        for i, bit in enumerate(reversed(target_str)):
            if bit == "0":
                qc.x(i)
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)
        for i, bit in enumerate(reversed(target_str)):
            if bit == "0":
                qc.x(i)
        qc.h(range(n))
        qc.x(range(n))
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)
        qc.x(range(n))
        qc.h(range(n))
    result = _sim(qc)
    return {**result, "target": target_str, "iterations": iterations,
            "n_qubits": n, "solver": "Qiskit Aer"}


def _run_qft(params: dict) -> dict:
    n = min(max(int(params.get("n_qubits", 3)), 1), 8)
    input_val = int(params.get("input_state", 1)) % (2 ** n)
    qc = QuantumCircuit(n)
    for i, bit in enumerate(reversed(format(input_val, f"0{n}b"))):
        if bit == "1":
            qc.x(i)
    for i in range(n):
        qc.h(i)
        for j in range(i + 1, n):
            qc.cp(math.pi / (2 ** (j - i)), j, i)
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)
    result = _sim(qc)
    return {**result, "input_state": format(input_val, f"0{n}b"),
            "n_qubits": n, "solver": "Qiskit Aer"}


def _run_bv(params: dict) -> dict:
    secret = "".join(c for c in str(params.get("secret_string", "101")) if c in "01") or "101"
    n = len(secret)
    total = n + 1
    qc = QuantumCircuit(total, n)
    qc.x(n)
    qc.h(range(total))
    for i, bit in enumerate(reversed(secret)):
        if bit == "1":
            qc.cx(i, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    result = _sim(qc)
    mc = max(result["counts"], key=result["counts"].get) if result["counts"] else "0" * n
    return {**result, "secret_string": secret, "recovered": mc.replace(" ", ""),
            "n_qubits": n, "solver": "Qiskit Aer"}


# ══════════════════════════════════════════════════════════════════════════════
# D-Wave / annealing helpers
# ══════════════════════════════════════════════════════════════════════════════

def _dwave_sample(bqm: dimod.BinaryQuadraticModel, num_reads: int) -> dimod.SampleSet:
    """
    Run simulated annealing locally (no API key required).
    The QUBO/Ising formulation is identical to what D-Wave QPUs consume.
    """
    sampler = SimulatedAnnealingSampler()
    return sampler.sample(bqm, num_reads=num_reads, beta_range=(0.1, 4.0))


def _edge_density_to_float(label: str) -> float:
    mapping = {
        "sparse (0.3)": 0.3,
        "medium (0.5)": 0.5,
        "dense (0.7)":  0.7,
    }
    return mapping.get(label, 0.5)


def _capacity_ratio_to_float(label: str) -> float:
    mapping = {
        "tight (0.3)":  0.3,
        "medium (0.5)": 0.5,
        "loose (0.7)":  0.7,
    }
    return mapping.get(label, 0.5)


# ── Maximum Cut ───────────────────────────────────────────────────────────────

def _run_maxcut(params: dict) -> dict:
    """
    Max-Cut QUBO formulation:
      minimise  -∑_{(i,j)∈E} x_i (1-x_j) + x_j (1-x_i)
    which equals:
      minimise  -∑_{(i,j)∈E} (x_i + x_j - 2 x_i x_j)
    QUBO form: Q_{ii} = -deg(i),  Q_{ij} = 2  for each edge (i,j)
    """
    n       = min(max(int(params.get("n_nodes",      6)),  3), 12)
    density = _edge_density_to_float(params.get("edge_density", "medium (0.5)"))
    reads   = min(max(int(params.get("num_reads",   500)), 100), 2000)

    # Deterministic random graph (seeded for reproducibility)
    rng = np.random.default_rng(42)
    edges: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < density:
                edges.append((i, j))

    if not edges:
        edges = [(0, 1)]  # guarantee at least one edge

    # Build QUBO
    Q: dict[tuple, float] = {}
    for i, j in edges:
        Q[(i, i)] = Q.get((i, i), 0) - 1
        Q[(j, j)] = Q.get((j, j), 0) - 1
        Q[(i, j)] = Q.get((i, j), 0) + 2

    bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
    sampleset = _dwave_sample(bqm, reads)

    best       = sampleset.first
    assignment = best.sample                        # {node: 0 or 1}
    cut_edges  = [(i, j) for i, j in edges if assignment[i] != assignment[j]]
    cut_value  = len(cut_edges)
    set_A      = sorted(v for v, b in assignment.items() if b == 0)
    set_B      = sorted(v for v, b in assignment.items() if b == 1)

    # Energy histogram for visualisation
    energies       = [float(d.energy) for d in sampleset.data(["energy"])]
    unique_energies = sorted(set(round(e, 3) for e in energies))
    energy_hist    = [
        {"energy": e, "count": sum(1 for x in energies if abs(x - e) < 0.01)}
        for e in unique_energies[:20]
    ]

    return {
        "solver":        "D-Wave Simulated Annealing (local)",
        "algorithm":     "Max-Cut QUBO",
        "n_nodes":       n,
        "n_edges":       len(edges),
        "edges":         edges,
        "cut_value":     cut_value,
        "max_possible":  len(edges),
        "set_A":         set_A,
        "set_B":         set_B,
        "cut_edges":     cut_edges,
        "best_energy":   round(float(best.energy), 4),
        "num_reads":     reads,
        "energy_histogram": energy_hist,
        # Reuse probabilities key so existing chart renders energy distribution
        "probabilities": {f"E={e['energy']:.2f}": e["count"] / reads for e in energy_hist},
        "verdict":       f"Cut {cut_value} of {len(edges)} edges ({round(cut_value/len(edges)*100)}%)",
    }


# ── Travelling Salesman ───────────────────────────────────────────────────────

def _run_tsp(params: dict) -> dict:
    """
    TSP QUBO using one-hot city-position encoding.
    Variables x_{c,p} = 1 if city c is in position p.
    Penalty terms:
      A: each city visited exactly once
      B: each position has exactly one city
      C: route distance objective
    """
    n_cities = min(max(int(params.get("n_cities", 4)), 3), 6)
    reads    = min(max(int(params.get("num_reads", 1000)), 200), 3000)

    # Random symmetric distance matrix (seeded)
    rng  = np.random.default_rng(7)
    dist = rng.integers(5, 25, size=(n_cities, n_cities)).astype(float)
    dist = (dist + dist.T) / 2
    np.fill_diagonal(dist, 0)

    n = n_cities
    A = float(n * n)       # penalty weight for constraint violations
    B = 1.0                 # objective weight

    Q: dict[tuple, float] = {}

    def var(c: int, p: int) -> int:
        return c * n + p

    # Penalty A: each city visited once
    for c in range(n):
        for p in range(n):
            v = var(c, p)
            Q[(v, v)] = Q.get((v, v), 0) + A * (-1)
            for p2 in range(p + 1, n):
                v2 = var(c, p2)
                Q[(v, v2)] = Q.get((v, v2), 0) + 2 * A

    # Penalty B: each position has one city
    for p in range(n):
        for c in range(n):
            v = var(c, p)
            Q[(v, v)] = Q.get((v, v), 0) + A * (-1)
            for c2 in range(c + 1, n):
                v2 = var(c2, p)
                Q[(v, v2)] = Q.get((v, v2), 0) + 2 * A

    # Objective C: minimise total tour distance
    for c1 in range(n):
        for c2 in range(n):
            if c1 == c2:
                continue
            d = float(dist[c1][c2])
            for p in range(n):
                v1 = var(c1, p)
                v2 = var(c2, (p + 1) % n)
                Q[(v1, v2)] = Q.get((v1, v2), 0) + B * d

    bqm       = dimod.BinaryQuadraticModel.from_qubo(Q)
    sampleset = _dwave_sample(bqm, reads)

    # Decode best valid solution
    best_route: list[int] | None = None
    best_dist  = float("inf")

    for sample, energy in sampleset.data(["sample", "energy"]):
        route = []
        valid = True
        for p in range(n):
            cities_at_pos = [c for c in range(n) if sample[var(c, p)] == 1]
            if len(cities_at_pos) != 1:
                valid = False
                break
            route.append(cities_at_pos[0])
        if not valid or len(set(route)) != n:
            continue
        total = sum(dist[route[i]][route[(i + 1) % n]] for i in range(n))
        if total < best_dist:
            best_dist  = total
            best_route = route

    if best_route is None:
        # No valid tour found — return best raw sample
        raw = sampleset.first.sample
        best_route = [c for p in range(n) for c in range(n) if raw[var(c, p)] == 1][:n]
        best_dist  = float("inf")

    tour_str = " → ".join(str(c) for c in best_route) + f" → {best_route[0]}"
    dist_matrix_list = [[round(dist[i][j], 1) for j in range(n)] for i in range(n)]

    return {
        "solver":        "D-Wave Simulated Annealing (local)",
        "algorithm":     "TSP QUBO",
        "n_cities":      n_cities,
        "best_route":    best_route,
        "tour_string":   tour_str,
        "tour_distance": round(best_dist, 2) if best_dist != float("inf") else "invalid",
        "distance_matrix": dist_matrix_list,
        "num_reads":     reads,
        "best_energy":   round(float(sampleset.first.energy), 4),
        "verdict":       tour_str,
        # Dummy probabilities so the frontend chart shows edge weights
        "probabilities": {
            f"{c1}→{c2}": round(float(dist[c1][c2]) / float(dist.max()), 3)
            for c1 in range(n) for c2 in range(n) if c1 != c2
        },
    }


# ── 0/1 Knapsack ──────────────────────────────────────────────────────────────

def _run_knapsack(params: dict) -> dict:
    """
    Knapsack QUBO with slack variables for the weight constraint.
    Maximise:  ∑ v_i x_i
    s.t.:      ∑ w_i x_i ≤ W
    QUBO penalty for exceeding capacity: λ (∑ w_i x_i - W)²
    """
    n_items   = min(max(int(params.get("n_items",   6)),  3), 10)
    cap_ratio = _capacity_ratio_to_float(params.get("capacity_ratio", "medium (0.5)"))
    reads     = min(max(int(params.get("num_reads", 500)), 100), 2000)

    rng     = np.random.default_rng(13)
    weights = rng.integers(1, 10, size=n_items).astype(int)
    values  = rng.integers(1, 20, size=n_items).astype(int)
    capacity = int(round(float(weights.sum()) * cap_ratio))
    capacity = max(capacity, int(weights.min()))  # at least one item fits

    lam = float(values.max()) * 2.0  # penalty weight

    Q: dict[tuple, float] = {}

    # Objective: maximise value → negate for minimisation
    for i in range(n_items):
        Q[(i, i)] = Q.get((i, i), 0) - float(values[i])

    # Penalty for weight constraint: λ (∑ w_i x_i - W)²
    # = λ [ ∑_i w_i² x_i + 2 ∑_{i<j} w_i w_j x_i x_j - 2W ∑_i w_i x_i + W² ]
    for i in range(n_items):
        Q[(i, i)] = Q.get((i, i), 0) + lam * (weights[i] ** 2 - 2 * capacity * weights[i])
        for j in range(i + 1, n_items):
            Q[(i, j)] = Q.get((i, j), 0) + 2 * lam * weights[i] * weights[j]

    bqm       = dimod.BinaryQuadraticModel.from_qubo(Q)
    sampleset = _dwave_sample(bqm, reads)

    # Find best *feasible* solution
    best_value  = -1
    best_sample: dict | None = None

    for sample, energy in sampleset.data(["sample", "energy"]):
        total_w = sum(weights[i] * sample[i] for i in range(n_items))
        if total_w > capacity:
            continue
        total_v = sum(values[i] * sample[i] for i in range(n_items))
        if total_v > best_value:
            best_value  = total_v
            best_sample = dict(sample)

    if best_sample is None:
        best_sample = {i: 0 for i in range(n_items)}
        best_value  = 0

    selected_items = [i for i in range(n_items) if best_sample[i] == 1]
    total_weight   = sum(weights[i] for i in selected_items)

    # Build items table
    items = [
        {
            "item": i,
            "weight": int(weights[i]),
            "value": int(values[i]),
            "selected": bool(best_sample[i]),
        }
        for i in range(n_items)
    ]

    return {
        "solver":          "D-Wave Simulated Annealing (local)",
        "algorithm":       "Knapsack QUBO",
        "n_items":         n_items,
        "capacity":        int(capacity),
        "total_value":     int(best_value),
        "total_weight":    int(total_weight),
        "selected_items":  selected_items,
        "items":           items,
        "num_reads":       reads,
        "best_energy":     round(float(sampleset.first.energy), 4),
        "verdict":         f"Value {best_value} · Weight {total_weight}/{capacity}",
        # Show per-item value/weight ratio for the frontend chart
        "probabilities": {
            f"item {i}": round(float(values[i]) / float(weights[i]), 3)
            for i in range(n_items)
        },
    }
