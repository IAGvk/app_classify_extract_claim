"""Policy record schema (mock for v1.x)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PolicyHolder(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class PolicyVehicle(BaseModel):
    registration: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    colour: str | None = None


class PolicyRecord(BaseModel):
    policy_number: str
    policy_type: str  # "motor" | "non-motor"
    status: str = "active"  # "active" | "lapsed" | "cancelled"
    holder: PolicyHolder
    vehicle: PolicyVehicle | None = None
    inception_date: str | None = None  # YYYY-MM-DD
    expiry_date: str | None = None  # YYYY-MM-DD
    insurer: str = Field(default="GIO")
    extra_fields: dict = Field(default_factory=dict)
