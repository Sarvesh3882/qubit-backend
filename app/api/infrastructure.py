"""
/api/infrastructure  — Quantum Infrastructure API

Providers
  GET  /api/infrastructure/providers                 list all providers + status
  GET  /api/infrastructure/providers/{id}            single provider + capabilities
  GET  /api/infrastructure/providers/{id}/backends   list backends for a provider
  GET  /api/infrastructure/providers/{id}/status     live connection/auth check

Jobs (in-process store — sufficient for Phase 1; swap for DB later)
  GET  /api/infrastructure/jobs                      all jobs for current user
  POST /api/infrastructure/jobs                      submit new job
  GET  /api/infrastructure/jobs/{job_id}             get one job
  POST /api/infrastructure/jobs/{job_id}/cancel      cancel a job
  POST /api/infrastructure/jobs/{job_id}/refresh     re-fetch status from provider
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models.user import User
from app.providers.base import ProviderError
from app.providers.registry import get_provider, list_providers

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])

# ── In-process job store (keyed by user_id → list[JobRecord]) ─────────────────
# Replace with SQLModel persistence in a future phase.
_JOB_STORE: dict[int, list[dict]] = {}


def _user_jobs(user_id: int) -> list[dict]:
    return _JOB_STORE.setdefault(user_id, [])


def _find_job(user_id: int, job_id: str) -> dict | None:
    return next((j for j in _user_jobs(user_id) if j["id"] == job_id), None)


# ── Provider endpoints ─────────────────────────────────────────────────────────

@router.get("/providers")
async def list_all_providers():
    """Return all registered providers with static metadata."""
    result = []
    for p in list_providers():
        result.append({
            "id":           p.provider_id,
            "name":         p.provider_name,
            "capabilities": p.capabilities.to_dict(),
        })
    return result


@router.get("/providers/{provider_id}")
async def get_provider_detail(provider_id: str):
    try:
        p = get_provider(provider_id)
    except KeyError:
        raise HTTPException(404, f"Provider '{provider_id}' not found")
    return {
        "id":           p.provider_id,
        "name":         p.provider_name,
        "capabilities": p.capabilities.to_dict(),
    }


@router.get("/providers/{provider_id}/status")
async def get_provider_status(provider_id: str):
    """Live connectivity + auth check. Always calls the provider."""
    try:
        p = get_provider(provider_id)
    except KeyError:
        raise HTTPException(404, f"Provider '{provider_id}' not found")
    status = await p.get_status()
    return status.to_dict()


@router.get("/providers/{provider_id}/backends")
async def list_provider_backends(provider_id: str):
    try:
        p = get_provider(provider_id)
    except KeyError:
        raise HTTPException(404, f"Provider '{provider_id}' not found")
    backends = await p.list_backends()
    return [b.to_dict() for b in backends]


# ── Job endpoints ─────────────────────────────────────────────────────────────

class SubmitJobRequest(BaseModel):
    provider_id:  str
    backend_id:   str
    circuit_qasm: str
    shots:        int = 1024
    num_qubits:   int = 2


@router.get("/jobs")
async def get_jobs(current_user: User = Depends(get_current_user)):
    """Return all jobs belonging to the authenticated user, newest first."""
    return sorted(_user_jobs(current_user.id), key=lambda j: j["submitted_at"], reverse=True)


@router.post("/jobs", status_code=201)
async def submit_job(
    req: SubmitJobRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        p = get_provider(req.provider_id)
    except KeyError:
        raise HTTPException(404, f"Provider '{req.provider_id}' not found")

    if p.capabilities.job_submit not in ("available",):
        cap = p.capabilities.job_submit
        reason = {
            "requires_auth":       "Configure provider credentials first.",
            "not_in_public_api":   "Job submission is not available through the public API for this provider.",
            "requires_enterprise": "Requires Enterprise access.",
        }.get(cap, f"Not available ({cap}).")
        raise HTTPException(503, f"Job submission unavailable: {reason}")

    try:
        job_record = await p.submit_job(
            backend_id=req.backend_id,
            circuit_qasm=req.circuit_qasm,
            shots=req.shots,
            num_qubits=req.num_qubits,
        )
    except ProviderError as exc:
        raise HTTPException(502, str(exc))

    job_dict = job_record.to_dict()
    _user_jobs(current_user.id).append(job_dict)
    return job_dict


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    job = _find_job(current_user.id, job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    job = _find_job(current_user.id, job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")

    if job["status"] in ("completed", "failed", "cancelled", "expired"):
        raise HTTPException(400, f"Job is already in terminal state: {job['status']}")

    try:
        p = get_provider(job["provider_id"])
        await p.cancel_job(job["raw_provider_id"] or job_id)
    except ProviderError as exc:
        raise HTTPException(502, str(exc))

    job["status"] = "cancelled"
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "cancelled", "job_id": job_id}


@router.post("/jobs/{job_id}/refresh")
async def refresh_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Re-fetch job state from provider (for async providers like Origin QCloud)."""
    job = _find_job(current_user.id, job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")

    if job["status"] in ("completed", "failed", "cancelled"):
        return job  # already terminal

    try:
        p    = get_provider(job["provider_id"])
        updated = await p.get_job(job["raw_provider_id"] or job_id)
        job.update(updated.to_dict())
    except ProviderError as exc:
        # Don't fail the request — return current state with note
        job["_refresh_error"] = str(exc)

    return job
