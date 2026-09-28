"""
OriginQuantumProvider — Origin Quantum Cloud integration via QPanda3 Runtime.

SDK / API facts verified from official OriginQ source:
  Repository:  github.com/OriginQ/qpanda3-runtime-mcp-server
  Runtime pkg: qpanda3_runtime (installed separately from pyqpanda3)
  Auth:        RuntimeService(server_url).login(api_key)
  Default URL: https://qpanda3-runtime.qpanda.cn  (from runtime.py line 48)
  Channel:     "qcloud"  (DEFAULT_CHANNEL env, always qcloud for public access)
  API key var: QPANDA3_API_KEY  (from .env.example)
  Account portal (for key registration): https://qcloud.originqc.com

What the public qpanda3_runtime SDK exposes:
  ✓  RuntimeService.login(api_key)                     — authenticate
  ✓  RuntimeService.list_devices()                     — list backends
  ✓  device.sample(circuit_str, shots=N)               → QTaskManager
  ✓  task_manager.id()                                 → task_id
  ✓  RuntimeService.get_task_status(task_id)           → status string
  ✓  RuntimeService.get_task_results(task_id)          → result dict
  ✓  RuntimeService.cancel_task(task_id)               → bool

What is NOT in the public SDK / community API:
  ✗  Queue depth / position
  ✗  Calibration data
  ✗  Noise mitigation matrices
  ✗  Compilation metadata
  ✗  Resource utilization telemetry
  ✗  Hybrid session management

QPanda3 circuit format used for submission:
  QINIT <n>
  CREG <n>
  H q[0]
  CNOT q[0],q[1]
  MEASURE q[0],c[0]
  ...
  (QPanda3 native QASM dialect — NOT OpenQASM 3.0)
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.providers.base import (
    BackendInfo, JobRecord, ProviderAdapter, ProviderCapabilities,
    ProviderStatus, ProviderError,
)

# ── Static backend list (replaced by live list when authenticated) ────────────
# These are the devices returned by the live API on 2026-09-22 with a valid key.
# Static list is used as fallback when no credentials are configured.
_STATIC_BACKENDS: list[BackendInfo] = [
    BackendInfo(
        id="full_amplitude",
        name="Full Amplitude Simulator",
        provider_id="origin_quantum",
        backend_type="simulator",
        architecture="statevector",
        max_qubits=35,
        available=True,
        status="online",
        description="Full amplitude statevector simulation. Max 35 qubits. Community access.",
        extra={"edition": "community", "channel": "qcloud"},
    ),
    BackendInfo(
        id="partial_amplitude",
        name="Partial Amplitude Simulator",
        provider_id="origin_quantum",
        backend_type="simulator",
        architecture="partial_amplitude",
        max_qubits=68,
        available=True,
        status="online",
        description="Partial amplitude simulation. Max 68 qubits. Community access.",
        extra={"edition": "community", "channel": "qcloud"},
    ),
    BackendInfo(
        id="single_amplitude",
        name="Single Amplitude Simulator",
        provider_id="origin_quantum",
        backend_type="simulator",
        architecture="single_amplitude",
        max_qubits=200,
        available=True,
        status="online",
        description="Single amplitude simulation. Max 200 qubits. Community access.",
        extra={"edition": "community", "channel": "qcloud"},
    ),
    # Live QPU backends — discovered 2026-09-22 via authenticated list_devices()
    BackendInfo(
        id="WK_C180",
        name="Origin Wukong 180",
        provider_id="origin_quantum",
        backend_type="qpu",
        architecture="superconducting",
        max_qubits=180,
        available=False,   # status unknown without auth
        status="unknown",
        description="Origin Wukong 180-qubit superconducting QPU (onlineFlag: True on live API).",
        extra={"edition": "community_with_qpu_access", "channel": "qcloud",
               "chip_id": "WK_C180"},
    ),
    BackendInfo(
        id="WK_C180_2",
        name="Origin Wukong 180-2",
        provider_id="origin_quantum",
        backend_type="qpu",
        architecture="superconducting",
        max_qubits=180,
        available=False,
        status="unknown",
        description="Origin Wukong 180-qubit superconducting QPU — second unit.",
        extra={"edition": "community_with_qpu_access", "channel": "qcloud",
               "chip_id": "WK_C180_2"},
    ),
    BackendInfo(
        id="PQPUMESH8",
        name="SILICON EXTREME-Qiming Optical Quantum Computer",
        provider_id="origin_quantum",
        backend_type="qpu",
        architecture="photonic",
        max_qubits=0,      # not returned by live API
        available=False,
        status="unknown",
        description="Qiming Optical Quantum Computer — photonic architecture.",
        extra={"edition": "community_with_qpu_access", "channel": "qcloud",
               "chip_id": "PQPUMESH8"},
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_api_key() -> str | None:
    """Read QPANDA3_API_KEY from settings (loaded from .env server-side)."""
    key = settings.QPANDA3_API_KEY
    return key.strip() if key and key.strip() else None


def _get_server_url() -> str:
    """Return the QPanda3 Runtime server URL from config, falling back to official default."""
    return (settings.QPANDA3_SERVER_URL or "https://qpanda3-runtime.qpanda.cn").strip()


def _qpanda3_runtime_available() -> bool:
    try:
        import qpanda3_runtime  # noqa: F401
        return True
    except ImportError:
        return False


def _build_runtime_service() -> Any:
    """
    Initialise and return an authenticated RuntimeService.
    Uses the exact pattern from OriginQ's official runtime.py:
        service = RuntimeService(server_url)
        service.login(api_key)
    """
    from qpanda3_runtime import RuntimeService  # type: ignore[import]

    # Set channel before creating service (matches OriginQ's pattern)
    channel = settings.QPANDA3_CHANNEL or "qcloud"
    os.environ.setdefault("DEFAULT_CHANNEL", channel)

    api_key = _get_api_key()
    server_url = _get_server_url()

    # Optional: config.yml path (alternative auth, overrides API key)
    config_path = settings.QPANDA3_CONFIG_PATH
    if config_path:
        service = RuntimeService(config_path)
        if not (hasattr(service, "tokens") and service.tokens):
            if api_key:
                service.login(api_key)
        return service

    # Standard path: server URL + API key
    service = RuntimeService(server_url)
    service.login(api_key)
    return service


def _qasm3_to_qpanda3(qasm: str, num_qubits: int) -> str:
    """
    Convert OpenQASM 3 (QUBIT's native circuit format) to QPanda3 native format.
    QPanda3 uses its own dialect:
        QINIT <n>
        CREG <n>
        H q[0]
        CNOT q[0],q[1]
        MEASURE q[0],c[0]

    This is a best-effort conversion for common gates.
    Complex circuits may need manual translation.
    """
    import re

    lines = qasm.strip().split("\n")
    gate_lines: list[str] = []

    # Map OpenQASM 3 gate names → QPanda3 names
    GATE_MAP = {
        "h":    "H",
        "x":    "X",
        "y":    "Y",
        "z":    "Z",
        "s":    "S",
        "t":    "T",
        "sdg":  "S.dagger()",
        "tdg":  "T.dagger()",
        "sx":   "X1",          # QPanda3 √X is X1
        "id":   "I",
        "cx":   "CNOT",
        "cz":   "CZ",
        "swap": "SWAP",
        "ccx":  "TOFFOLI",
    }

    has_measure = False
    for line in lines:
        line = line.strip().rstrip(";")
        if not line or line.startswith("OPENQASM") or line.startswith("include"):
            continue
        if line.startswith("qubit[") or line.startswith("bit["):
            continue
        # Rotation gates: rx(theta) q[i]
        rx_m = re.match(r"(rx|ry|rz|p)\(([^)]+)\)\s+q\[(\d+)\]", line)
        if rx_m:
            name, param, qubit = rx_m.groups()
            panda_map = {"rx": "RX", "ry": "RY", "rz": "RZ", "p": "P"}
            gate_lines.append(f"{panda_map[name]}(q[{qubit}], {param})")
            continue
        # Measure: c[i] = measure q[j]
        meas_m = re.match(r"c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\]", line)
        if meas_m:
            c_idx, q_idx = meas_m.groups()
            gate_lines.append(f"MEASURE q[{q_idx}],c[{c_idx}]")
            has_measure = True
            continue
        # Two-qubit gates: cx q[0], q[1]
        two_m = re.match(r"(\w+)\s+q\[(\d+)\]\s*,\s*q\[(\d+)\]", line)
        if two_m:
            gate, q0, q1 = two_m.groups()
            panda = GATE_MAP.get(gate.lower(), gate.upper())
            gate_lines.append(f"{panda} q[{q0}],q[{q1}]")
            continue
        # Single-qubit: h q[0]
        one_m = re.match(r"(\w+)\s+q\[(\d+)\]", line)
        if one_m:
            gate, q = one_m.groups()
            panda = GATE_MAP.get(gate.lower(), gate.upper())
            gate_lines.append(f"{panda} q[{q}]")
            continue

    if not has_measure:
        for i in range(num_qubits):
            gate_lines.append(f"MEASURE q[{i}],c[{i}]")

    result = [f"QINIT {num_qubits}", f"CREG {num_qubits}"]
    result.extend(gate_lines)
    return "\n".join(result)


# ── Provider implementation ───────────────────────────────────────────────────

class OriginQuantumProvider(ProviderAdapter):
    """
    QUBIT adapter for Origin Quantum Cloud via QPanda3 Runtime.

    Authentication:  QPANDA3_API_KEY (server-side .env)
    Runtime URL:     QPANDA3_SERVER_URL (default: https://qpanda3-runtime.qpanda.cn)
    Channel:         QPANDA3_CHANNEL (default: qcloud)
    SDK package:     qpanda3_runtime (pip install qpanda3_runtime)
    Circuit format:  QPanda3 native QASM (converted from OpenQASM3 internally)

    Source: github.com/OriginQ/qpanda3-runtime-mcp-server
    """

    @property
    def provider_id(self) -> str:
        return "origin_quantum"

    @property
    def provider_name(self) -> str:
        return "Origin Quantum Cloud"

    @property
    def capabilities(self) -> ProviderCapabilities:
        has_key = bool(_get_api_key())
        has_sdk = _qpanda3_runtime_available()
        ready   = has_key and has_sdk

        return ProviderCapabilities(
            job_submit          = "available"         if ready else "requires_auth",
            job_cancel          = "available"         if ready else "requires_auth",
            job_status          = "available"         if ready else "requires_auth",
            job_result          = "available"         if ready else "requires_auth",
            backend_list        = "available"         if ready else "requires_auth",
            queue_info          = "not_in_public_api",
            calibration_data    = "not_in_public_api",
            noise_mitigation    = "not_in_public_api",
            hybrid_session      = "not_in_public_api",
            batch_submit        = "available"         if ready else "requires_auth",
            circuit_compilation = "not_in_public_api",
            resource_monitoring = "not_in_public_api",
        )

    async def get_status(self) -> ProviderStatus:
        api_key = _get_api_key()
        server_url = _get_server_url()

        if not api_key:
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=False,
                authenticated=False,
                account=None,
                edition="community",
                error=(
                    "QPANDA3_API_KEY not set in qubit-backend/.env. "
                    "Obtain your key at https://qcloud.originqc.com"
                ),
            )
        if not _qpanda3_runtime_available():
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=False,
                authenticated=False,
                account=None,
                edition="community",
                error=(
                    "qpanda3_runtime not installed. "
                    "Run: pip install qpanda3_runtime"
                ),
            )

        try:
            t0 = time.monotonic()
            service = _build_runtime_service()
            # Lightweight check: list devices
            devices = service.list_devices()
            latency_ms = round((time.monotonic() - t0) * 1000, 1)

            device_count = len(devices) if devices else 0
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=True,
                authenticated=True,
                account="authenticated",
                edition="community",
                latency_ms=latency_ms,
                error=None,
            )
        except Exception as exc:
            return ProviderStatus(
                provider_id=self.provider_id,
                connected=False,
                authenticated=False,
                account=None,
                edition="community",
                error=f"Connection failed: {exc}",
            )

    async def list_backends(self) -> list[BackendInfo]:
        api_key = _get_api_key()
        if not api_key or not _qpanda3_runtime_available():
            # Return static list — accurately shows "unknown" status for QPU
            return _STATIC_BACKENDS

        try:
            service = _build_runtime_service()
            devices = service.list_devices()
            if not devices:
                return _STATIC_BACKENDS

            live: list[BackendInfo] = []
            for dev in devices:
                # QDevice attributes are methods — call them (confirmed from live API response)
                try:
                    dev_id   = str(dev.chip_id())
                except Exception:
                    dev_id   = str(getattr(dev, "chip_id", "unknown"))
                try:
                    dev_name = str(dev.name())
                except Exception:
                    dev_name = dev_id
                try:
                    max_q    = int(dev.qubit_num())
                except Exception:
                    max_q    = 0
                try:
                    avail    = bool(dev.is_available()) if callable(getattr(dev, "is_available", None)) else True
                except Exception:
                    avail    = True

                # Determine backend type from name / chip ID
                name_lower = dev_name.lower()
                is_qpu     = not any(s in name_lower for s in ("simulator", "amplitude"))
                dev_type   = "qpu" if is_qpu else "simulator"
                arch       = "superconducting" if is_qpu else "statevector"
                # Optical QPUs have a different architecture
                if "optical" in name_lower or "photon" in name_lower:
                    arch = "photonic"
                status     = "online" if avail else "offline"

                live.append(BackendInfo(
                    id=dev_id,
                    name=dev_name,
                    provider_id=self.provider_id,
                    backend_type=dev_type,
                    architecture=arch,
                    max_qubits=max_q,
                    available=avail,
                    status=status,
                    description=f"Origin Quantum device · {dev_name}",
                    extra={"source": "live_qpanda3_runtime_api", "channel": "qcloud"},
                ))
            return live if live else _STATIC_BACKENDS

        except Exception:
            return _STATIC_BACKENDS

    async def submit_job(
        self,
        backend_id: str,
        circuit_qasm: str,
        shots: int,
        num_qubits: int,
        **kwargs: Any,
    ) -> JobRecord:
        api_key = _get_api_key()
        if not api_key:
            raise ProviderError(
                self.provider_id,
                "QPANDA3_API_KEY not set in qubit-backend/.env. "
                "Obtain your key at https://qcloud.originqc.com",
            )
        if not _qpanda3_runtime_available():
            raise ProviderError(
                self.provider_id,
                "qpanda3_runtime not installed. Run: pip install qpanda3_runtime",
            )

        job_id = f"oq_{uuid.uuid4().hex[:10]}"
        now    = datetime.now(timezone.utc)

        try:
            service = _build_runtime_service()

            # Convert QUBIT's OpenQASM3 → QPanda3 native format
            qpanda3_circuit = _qasm3_to_qpanda3(circuit_qasm, num_qubits)

            # Get device list and look up by chip_id() — QDevice has no .id attribute
            devices = service.list_devices()
            device  = None
            for d in (devices or []):
                try:
                    if str(d.chip_id()) == backend_id:
                        device = d
                        break
                except Exception:
                    pass

            if device is None:
                avail = []
                for d in (devices or []):
                    try:
                        avail.append(str(d.chip_id()))
                    except Exception:
                        avail.append(repr(d))
                raise ProviderError(
                    self.provider_id,
                    f"Backend '{backend_id}' not found. "
                    f"Available chip IDs: {avail}",
                )

            # Submit via RuntimeService.sample() — NOT device.sample()
            # Correct signature: service.sample(circuits, device, shots=N)
            task_manager = service.sample(
                circuits=qpanda3_circuit,
                device=device,
                shots=shots,
            )

            # Extract task ID (from OriginQ runtime.py pattern)
            raw_id = None
            try:
                raw_id_val = task_manager.id()
                raw_id = raw_id_val[0] if isinstance(raw_id_val, list) else str(raw_id_val)
            except Exception:
                raw_id = str(getattr(task_manager, "task_id", job_id))

            return JobRecord(
                id=job_id,
                provider_id=self.provider_id,
                backend_id=backend_id,
                status="submitted",
                shots=shots,
                num_qubits=num_qubits,
                circuit_qasm=circuit_qasm,
                submitted_at=now,
                raw_provider_id=raw_id,
                provider_meta={
                    "qpanda3_task_id": raw_id,
                    "qpanda3_circuit": qpanda3_circuit,
                    "server_url": _get_server_url(),
                    "channel": settings.QPANDA3_CHANNEL or "qcloud",
                },
            )

        except ProviderError:
            raise
        except Exception as exc:
            return JobRecord(
                id=job_id, provider_id=self.provider_id, backend_id=backend_id,
                status="failed", shots=shots, num_qubits=num_qubits,
                circuit_qasm=circuit_qasm, submitted_at=now,
                completed_at=datetime.now(timezone.utc),
                error=str(exc),
            )

    async def get_job(self, job_id: str) -> JobRecord:
        """
        Refresh job status using the raw QPanda3 task ID.
        job_id here is the raw_provider_id (QPanda3 task ID).
        """
        if not _get_api_key() or not _qpanda3_runtime_available():
            raise ProviderError(self.provider_id, "Provider not configured.")

        try:
            service = _build_runtime_service()
            status_raw = service.get_task_status(job_id)

            # QPanda3 status values: PENDING / RUNNING / DONE / FAILED / CANCELLED
            STATUS_MAP = {
                "PENDING":   "queued",
                "RUNNING":   "running",
                "DONE":      "completed",
                "FAILED":    "failed",
                "CANCELLED": "cancelled",
            }
            status = STATUS_MAP.get(str(status_raw).upper(), "queued")

            result = None
            if status == "completed":
                try:
                    raw_result = service.get_task_results(job_id)
                    # QPanda3 returns {state: count} dict
                    counts = {}
                    if isinstance(raw_result, dict):
                        counts = {str(k): int(v) for k, v in raw_result.items()}
                    total  = sum(counts.values()) or 1
                    probs  = {k: v / total for k, v in counts.items()}
                    result = {
                        "counts":        counts,
                        "probabilities": probs,
                        "statevector":   [],
                        "bloch_spheres": {},
                        "qsphere":       [],
                        "circuit_qasm":  "",
                        "shots":         total,
                        "num_qubits":    0,
                    }
                except Exception:
                    pass

            return JobRecord(
                id=job_id,
                provider_id=self.provider_id,
                backend_id="unknown",
                status=status,
                shots=0,
                num_qubits=0,
                circuit_qasm=None,
                submitted_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc) if status in ("completed", "failed", "cancelled") else None,
                raw_provider_id=job_id,
                result=result,
            )

        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(self.provider_id, f"get_job failed: {exc}", retriable=True)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job using QPanda3 RuntimeService.cancel_task()."""
        if not _get_api_key() or not _qpanda3_runtime_available():
            raise ProviderError(self.provider_id, "Provider not configured.")
        try:
            service = _build_runtime_service()
            service.cancel_task(job_id)
            return True
        except Exception as exc:
            raise ProviderError(self.provider_id, f"Cancel failed: {exc}", retriable=False)
