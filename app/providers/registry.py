"""
Provider registry — single place to get a ProviderAdapter by ID.
Add new providers here without touching the API layer.
"""
from app.providers.base import ProviderAdapter
from app.providers.local_aer import LocalAerProvider
from app.providers.origin_quantum import OriginQuantumProvider

_PROVIDERS: dict[str, ProviderAdapter] = {
    "local_aer":      LocalAerProvider(),
    "origin_quantum": OriginQuantumProvider(),
}


def get_provider(provider_id: str) -> ProviderAdapter:
    p = _PROVIDERS.get(provider_id)
    if p is None:
        raise KeyError(f"Unknown provider: {provider_id!r}")
    return p


def list_providers() -> list[ProviderAdapter]:
    return list(_PROVIDERS.values())
