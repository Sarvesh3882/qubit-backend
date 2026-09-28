"""
Provider abstraction layer for QUBIT Quantum Infrastructure.

Every quantum backend provider (local simulator, Origin Quantum Cloud,
future providers) implements ProviderAdapter. The rest of the application
talks only to this interface — never to provider-specific SDKs directly.

Capability flags use literal strings so they can be serialised to JSON
and shown in the UI without a separate enum lookup.

Capability availability levels
--------------------------------
  "available"           — Can be invoked right now through this adapter.
  "unavailable"         — Not exposed by the current provider API version.
  "requires_auth"       — Requires a valid API credential to be configured.
  "requires_enterprise" — Documented as Enterprise-only by the provider.
  "not_in_public_api"   — The provider capability exists internally but is
                          not exposed through the public/community API.
  "coming_later"        — Planned for a future QUBIT release.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

CapabilityLevel = Literal[
    "available",
    "unavailable",
    "requires_auth",
    "requires_enterprise",
    "not_in_public_api",
    "coming_later",
]

# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class BackendInfo:
    """Describes a single executable backend returned by a provider."""
    id: str                              # stable identifier, e.g. "full_amplitude"
    name: str                            # human-readable name
    provider_id: str                     # parent provider id
    backend_type: str                    # "simulator" | "qpu" | "annealer"
    architecture: str                    # "statevector" | "superconducting" | etc.
    max_qubits: int
    available: bool                      # can jobs be submitted right now
    status: str                          # "online" | "maintenance" | "offline" | "unknown"
    queue_depth: int | None = None       # None = not exposed by API
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider_id": self.provider_id,
            "backend_type": self.backend_type,
            "architecture": self.architecture,
            "max_qubits": self.max_qubits,
            "available": self.available,
            "status": self.status,
            "queue_depth": self.queue_depth,
            "description": self.description,
            **self.extra,
        }


@dataclass
class JobRecord:
    """Normalised job state, independent of provider-specific fields."""
    id: str
    provider_id: str
    backend_id: str
    status: str   # submitted|queued|compiling|scheduled|running|completed|failed|cancelled|expired
    shots: int
    num_qubits: int
    circuit_qasm: str | None
    submitted_at: datetime
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    raw_provider_id: str | None = None  # provider's own job ID
    provider_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "backend_id": self.backend_id,
            "status": self.status,
            "shots": self.shots,
            "num_qubits": self.num_qubits,
            "circuit_qasm": self.circuit_qasm,
            "submitted_at": self.submitted_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "raw_provider_id": self.raw_provider_id,
            "provider_meta": self.provider_meta,
        }


@dataclass
class ProviderCapabilities:
    """What this provider can actually do through the QUBIT adapter."""
    job_submit: CapabilityLevel = "unavailable"
    job_cancel: CapabilityLevel = "unavailable"
    job_status: CapabilityLevel = "unavailable"
    job_result: CapabilityLevel = "unavailable"
    backend_list: CapabilityLevel = "unavailable"
    queue_info: CapabilityLevel = "unavailable"
    calibration_data: CapabilityLevel = "unavailable"
    noise_mitigation: CapabilityLevel = "unavailable"
    hybrid_session: CapabilityLevel = "unavailable"
    batch_submit: CapabilityLevel = "unavailable"
    circuit_compilation: CapabilityLevel = "unavailable"
    resource_monitoring: CapabilityLevel = "unavailable"

    def to_dict(self) -> dict:
        return {
            "job_submit": self.job_submit,
            "job_cancel": self.job_cancel,
            "job_status": self.job_status,
            "job_result": self.job_result,
            "backend_list": self.backend_list,
            "queue_info": self.queue_info,
            "calibration_data": self.calibration_data,
            "noise_mitigation": self.noise_mitigation,
            "hybrid_session": self.hybrid_session,
            "batch_submit": self.batch_submit,
            "circuit_compilation": self.circuit_compilation,
            "resource_monitoring": self.resource_monitoring,
        }


@dataclass
class ProviderStatus:
    provider_id: str
    connected: bool
    authenticated: bool
    account: str | None            # username / email if returned by provider
    edition: str                   # "community" | "enterprise" | "local" | "unknown"
    error: str | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "connected": self.connected,
            "authenticated": self.authenticated,
            "account": self.account,
            "edition": self.edition,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


# ── Abstract base ─────────────────────────────────────────────────────────────

class ProviderAdapter(ABC):
    """
    All quantum backend integrations implement this interface.
    The API layer calls these methods — never provider SDKs directly.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Stable snake_case identifier, e.g. 'origin_quantum'."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name, e.g. 'Origin Quantum Cloud'."""

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """What this adapter can actually do right now."""

    @abstractmethod
    async def get_status(self) -> ProviderStatus:
        """Connectivity / authentication check."""

    @abstractmethod
    async def list_backends(self) -> list[BackendInfo]:
        """Return all backends accessible with the current credentials."""

    @abstractmethod
    async def submit_job(
        self,
        backend_id: str,
        circuit_qasm: str,
        shots: int,
        num_qubits: int,
        **kwargs: Any,
    ) -> JobRecord:
        """Submit a circuit. Raises ProviderError on failure."""

    @abstractmethod
    async def get_job(self, job_id: str) -> JobRecord:
        """Fetch current state of a job."""

    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Attempt to cancel a queued/running job. Returns True if accepted."""


# ── Shared exception ──────────────────────────────────────────────────────────

class ProviderError(Exception):
    def __init__(self, provider_id: str, message: str, retriable: bool = False):
        super().__init__(message)
        self.provider_id = provider_id
        self.retriable   = retriable
