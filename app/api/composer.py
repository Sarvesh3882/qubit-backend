from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from app.services.simulation import run_simulation

router = APIRouter(prefix="/composer", tags=["composer"])


class Gate(BaseModel):
    gate: str
    qubits: list[int]
    params: list[float] = []
    moment: int = 0


class SimulateRequest(BaseModel):
    num_qubits: int = 2
    gates: list[Gate] = []
    shots: int = 1024
    include_statevector: bool = True
    framework: str = "qiskit"  # qiskit | pennylane | openqasm3 | cirq | qbraid | qpiai


class SimulateResponse(BaseModel):
    success: bool
    simulator: Optional[str] = None        # which engine ran
    probabilities: Optional[dict[str, float]] = None
    counts: Optional[dict[str, int]] = None
    statevector: Optional[list[dict[str, float]]] = None
    bloch_spheres: Optional[dict[str, dict[str, float]]] = None
    qsphere: Optional[list[dict[str, Any]]] = None
    circuit_qasm: Optional[str] = None
    num_qubits: Optional[int] = None
    shots: Optional[int] = None
    error: Optional[str] = None


@router.post("/simulate", response_model=SimulateResponse)
async def simulate_circuit(request: SimulateRequest):
    if request.num_qubits < 1 or request.num_qubits > 20:
        raise HTTPException(400, "num_qubits must be between 1 and 20")

    gates_data = [g.model_dump() for g in request.gates]
    result = run_simulation(
        num_qubits=request.num_qubits,
        gates=gates_data,
        shots=request.shots,
        include_statevector=request.include_statevector,
        framework=request.framework,
    )
    return result


@router.post("/validate-qasm")
async def validate_qasm(payload: dict):
    """Validate a QASM string and return circuit metadata."""
    try:
        from qiskit import QuantumCircuit
        qasm = payload.get("qasm", "")
        qc = QuantumCircuit.from_qasm_str(qasm)
        return {
            "valid": True,
            "num_qubits": qc.num_qubits,
            "num_clbits": qc.num_clbits,
            "depth": qc.depth(),
            "gate_count": len(qc.data),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
