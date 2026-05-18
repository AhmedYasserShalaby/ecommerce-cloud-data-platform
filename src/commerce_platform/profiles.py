from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataProfile:
    name: str
    seed: int
    customers: int
    products: int
    warehouses: int
    orders: int
    web_events: int
    event_chunk_size: int


PROFILES: dict[str, DataProfile] = {
    "ci": DataProfile(
        name="ci",
        seed=42,
        customers=40,
        products=25,
        warehouses=4,
        orders=600,
        web_events=2_500,
        event_chunk_size=1_000,
    ),
    "demo": DataProfile(
        name="demo",
        seed=2026,
        customers=1_000,
        products=250,
        warehouses=8,
        orders=20_000,
        web_events=120_000,
        event_chunk_size=10_000,
    ),
    "full": DataProfile(
        name="full",
        seed=9001,
        customers=50_000,
        products=1_200,
        warehouses=12,
        orders=250_000,
        web_events=5_000_000,
        event_chunk_size=100_000,
    ),
}


def get_profile(name: str) -> DataProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown profile {name!r}. Expected one of: {valid}") from exc
