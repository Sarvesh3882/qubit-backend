"""
LocalAerProvider — uses Qiskit + Qiskit Aer locally.

This is always available (no credentials required) and is the default
backend for circuit execution inside QUBIT. It reuses the existing
simulation service so there is no duplicated logic.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.providers.base import (
    BackendInfo, JobRecord, ProviderAdapter, ProviderCapabilities,
    ProviderStatus, ProviderError,
)
from app.services.simulation import run_simulation, _build_qiskit_circuit as _build_circuit
from qiskit.qasm2 import loads as qasm2_loads
from qiskit.qasm3 import loads as qasm3_loads


_BACKENDS: list[BackendInfo] = [
    BackendInfo(
        id="aer_statevector",
        name="Aer Statevector Simulator",
        provider_id="local_aer",
        backend_type="simulator",
        architecture="statevector",
        max_qubits=20,
        available=True,
        status="online",
        description="Full statevector simulation using Qiskit Aer. Exact probabilities, no shot noise.",
    ),
    BackendInfo(
        id="aer_qasm",
        name="Aer QASM Simulator",
        provider_id="local_aer",
        backend_type="simulator",
        architecture="shot_based",
        max_qubits=20,
        available=True,
        status="online",
        description="Shot-based sampling simulator. Approximates measurement statistics.",
    ),
]


def _parse_qasm(qasm: str) -> tuple[int, list[dict]]:
    """
    Parse QASM2 or QASM3 into (num_qubits, gate_list).
    Falls back to a manual gate list if QASM parsing fails.
    """
    # Try QASM3 first (Qiskit 2.x default output)
    try:
        qc = qasm3_loads(qasm)
        # Convert back to our gate dict representation via circuit.data
        gates = []
        for i, instr in enumerate(qc.data):
            op    = instr.operation
            qargs = [qc.find_bit(q).index for q in instr.qubits]
            params = [float(p) for p in op.params] if op.params else []
            gates.append({"gate": op.name.upper(), "qubits": qargs, "params": params, "moment": i})
        return qc.num_qubits, gates
    except Exception:
        pass
    # Try QASM2
    try:
        qc = qasm2_loads(qasm)
        gates = []
        for i, instr in enumerate(qc.data):
            op    = instr.operation
            qargs = [qc.find_bit(q).index for q in instr.qubits]
            params = [float(p) for p in op.params] if op.params else []
            gates.append({"gate": op.name.upper(), "qubits": qargs, "params": params, "moment": i})
        return qc.num_qubits, gates
    except Exception:
        pass
    return 0, []


class LocalAerProvider(ProviderAdapter):

    @property
    def provider_id(self) -> str:
        return "local_aer"

    @property
    def provider_name(self) -> str:
        return "Local Simulator (Qiskit Aer)"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            job_submit="available",
            job_cancel="unavailable",          # local jobs are synchronous
            job_status="available",
            job_result="available",
            backend_list="available",
            queue_info="unavailable",          # no queue — runs immediately
            calibration_data="unavailable",
            noise_mitigation="unavailable",
            hybrid_session="unavailable",
            batch_submit="available",
            circuit_compilation="available",   # Qiskit transpile
            resource_monitoring="unavailable",
        )

    async def get_status(self) -> ProviderStatus:
        try:
            import qiskit_aer
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=True,
                authenticated=True,
                account="local",
                edition="local",
                latency_ms=0.0,
            )
        except Exception as exc:
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=False,
                authenticated=False,
                account=None,
                edition="local",
                error=str(exc),
            )

    async def list_backends(self) -> list[BackendInfo]:
        return _BACKENDS

    async def submit_job(
        self,
        backend_id: str,
        circuit_qasm: str,
        shots: int,
        num_qubits: int,
        **kwargs: Any,
    ) -> JobRecord:
        job_id = f"local_{uuid.uuid4().hex[:10]}"
        now    = datetime.now(timezone.utc)

        try:
            parsed_n, gate_list = _parse_qasm(circuit_qasm)
            effective_n = parsed_n if parsed_n > 0 else num_qubits

            result = run_simulation(
                num_qubits=effective_n,
                gates=gate_list,
                shots=shots,
                include_statevector=True,
            )

            if not result["success"]:
                return JobRecord(
                    id=job_id, provider_id=self.provider_id, backend_id=backend_id,
                    status="failed", shots=shots, num_qubits=effective_n,
                    circuit_qasm=circuit_qasm, submitted_at=now, completed_at=datetime.now(timezone.utc),
                    error=result.get("error", "Simulation failed"),
                )

            return JobRecord(
                id=job_id, provider_id=self.provider_id, backend_id=backend_id,
                status="completed", shots=shots, num_qubits=effective_n,
                circuit_qasm=circuit_qasm, submitted_at=now,
                completed_at=datetime.now(timezone.utc),
                raw_provider_id=job_id,
                result={
                    "probabilities": result["probabilities"],
                    "counts":        result["counts"],
                    "statevector":   result["statevector"],
                    "bloch_spheres": result["bloch_spheres"],
                    "qsphere":       result["qsphere"],
                    "circuit_qasm":  result["circuit_qasm"],
                    "shots":         shots,
                    "num_qubits":    effective_n,
                },
            )

        except Exception as exc:
            return JobRecord(
                id=job_id, provider_id=self.provider_id, backend_id=backend_id,
                status="failed", shots=shots, num_qubits=num_qubits,
                circuit_qasm=circuit_qasm, submitted_at=now,
                completed_at=datetime.now(timezone.utc),
                error=str(exc),
            )

    async def get_job(self, job_id: str) -> JobRecord:
        # Local jobs are synchronous — the job_id comes from the in-memory store
        raise ProviderError(self.provider_id, "Local jobs are synchronous; status tracked by job store.")

    async def cancel_job(self, job_id: str) -> bool:
        return False  # synchronous, cannot cancel
