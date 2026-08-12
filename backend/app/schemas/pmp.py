"""Typed contracts for the decision-ready PMP dashboard."""

from typing import Literal

from pydantic import BaseModel, Field


class MetricDefinition(BaseModel):
    label: str
    formula: str
    source_fields: str


class PmpMetricValues(BaseModel):
    total_orders: int
    finalized_orders: int
    pending_orders: int
    planned_minutes: float
    completed_planned_minutes: float
    pending_planned_minutes: float
    planned_hours: float
    completed_planned_hours: float
    pending_planned_hours: float
    workload_completion_percent: float
    order_completion_percent: float
    target_gap_percentage_points: float
    additional_completed_minutes_lower_bound: float
    additional_completed_hours_lower_bound: float
    strict_target_note: str
    compliant: bool
    traffic_light: Literal["green", "yellow", "red"]
    risk_rank: int | None = None
    formatted: dict[str, str]


class PmpMetrics(BaseModel):
    global_: PmpMetricValues = Field(alias="global")
    by_area: dict[str, PmpMetricValues]
    area_ranking: list[str]
    highest_risk_area: str | None
    alerts: list[dict[str, str]]
    filter_application: dict[str, str | int | None]


class PmpCapacityRow(BaseModel):
    area: str
    week_start: str
    shift: str | None
    configured: bool
    available_minutes: float | None
    available_hours: float | None
    required_minutes: float | None
    required_hours: float | None
    gap_minutes: float | None
    gap_hours: float | None
    staffing_gap_equivalent: float | None
    status: Literal["not_configured", "demand_not_assigned_to_shift", "sufficient", "insufficient"]
    missing_inputs: list[str]


class PmpCapacity(BaseModel):
    week_start: str | None
    configured: bool
    rows: list[PmpCapacityRow]
    available_shifts: list[str]
    demand_shift_assignment_available: bool
    notice: str


class PmpDashboardResponse(BaseModel):
    metrics: PmpMetrics
    capacity: PmpCapacity
    metric_dictionary: dict[str, MetricDefinition]
    filters: dict[str, str | None]


class PmpOrderItem(BaseModel):
    id: int
    external_id: str
    area: str
    status: Literal["pending", "finalized"]
    planned_minutes: float
    planned_hours: float
    planned_start_date: str | None
    source: str
    source_row_number: int | None


class PmpOrdersResponse(BaseModel):
    items: list[PmpOrderItem]
    total: int
    offset: int
    limit: int
    filter_application: dict[str, str | int | None]
