import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PmpDashboard, PmpDashboardResponse, PmpFilters, PmpOrdersResponse, validatePmpDateRange } from "./PmpDashboard";

function metric(overrides = {}) {
  return {
    total_orders: 10, finalized_orders: 9, pending_orders: 1, planned_minutes: 600, completed_planned_minutes: 540, pending_planned_minutes: 60,
    planned_hours: 10, completed_planned_hours: 9, pending_planned_hours: 1, workload_completion_percent: 90, order_completion_percent: 90,
    target_gap_percentage_points: 0, additional_completed_hours_lower_bound: 0, strict_target_note: "90 % exacto no cumple.", compliant: false, traffic_light: "yellow" as const,
    risk_rank: 1, formatted: {}, ...overrides,
  };
}

const dictionary = {
  total_orders: { label: "Órdenes totales", formula: "count", source_fields: "pmp_orders.id" }, planned_hours: { label: "Horas programadas", formula: "minutos / 60", source_fields: "planned_minutes" },
  completed_planned_hours: { label: "Horas completadas", formula: "finalizadas / 60", source_fields: "planned_minutes" }, pending_planned_hours: { label: "Horas pendientes", formula: "pendientes / 60", source_fields: "planned_minutes" },
  workload_completion_percent: { label: "Cumplimiento por carga", formula: "completadas / planeadas", source_fields: "status, planned_minutes" }, order_completion_percent: { label: "Cumplimiento por órdenes", formula: "finalizadas / total", source_fields: "status" },
  target: { label: "Meta PMP", formula: "carga > 90", source_fields: "regla PMP" }, capacity: { label: "Capacidad", formula: "sum(schedule)", source_fields: "available_minutes" },
};

function dashboard(configured = false): PmpDashboardResponse {
  const mec = metric();
  return { metrics: { global: mec, by_area: { MEC: mec }, area_ranking: ["MEC"], highest_risk_area: "MEC", alerts: [], filter_application: { order_date_filter: "not_requested", as_of_date: null, orders_without_planned_start_date_excluded: 0 } }, capacity: { configured, notice: "Turno no asignado a demanda.", available_shifts: configured ? ["1"] : [], rows: configured ? [{ area: "MEC", configured: true, available_hours: 8, required_hours: 1, gap_hours: 0, staffing_gap_equivalent: 0, status: "sufficient", missing_inputs: [] }] : [{ area: "MEC", configured: false, available_hours: null, required_hours: null, gap_hours: null, staffing_gap_equivalent: null, status: "not_configured", missing_inputs: ["personal PMP activo"] }] }, metric_dictionary: dictionary };
}

const orders: PmpOrdersResponse = { items: [{ id: 1, external_id: "OT-1", area: "MEC", status: "pending", planned_minutes: 60, planned_hours: 1, planned_start_date: "2026-08-10", source: "excel", source_row_number: 2 }], total: 1, offset: 0, limit: 30 };
const filters: PmpFilters = { area: "", status: "", date_from: "", date_to: "", shift: "", unit: "hours" };

describe("PmpDashboard", () => {
  it("renders KPI values and marks exactly 90% as not compliant", () => {
    render(<PmpDashboard dashboard={dashboard()} orders={orders} errors={[]} areas={["MEC"]} filters={filters} onFiltersChange={vi.fn()} onOrderPage={vi.fn()} />);
    expect(screen.getByText("Horas planeadas")).toBeTruthy();
    expect(screen.getAllByText("90%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("En vigilancia").length).toBeGreaterThan(0);
    expect(screen.getByText(/concentra la mayor carga pendiente/)).toBeTruthy();
  });

  it("emits filter changes and exposes capacity warning when it is not configured", () => {
    const onFiltersChange = vi.fn();
    render(<PmpDashboard dashboard={dashboard()} orders={orders} errors={[]} areas={["MEC"]} filters={filters} onFiltersChange={onFiltersChange} onOrderPage={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Área"), { target: { value: "MEC" } });
    fireEvent.change(screen.getByLabelText("Fecha inicial"), { target: { value: "2026-08-10" } });
    fireEvent.change(screen.getByLabelText("Fecha final"), { target: { value: "2026-08-12" } });
    fireEvent.click(screen.getByRole("button", { name: "Minutos" }));
    expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ area: "MEC" }));
    expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ date_from: "2026-08-10" }));
    expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ date_to: "2026-08-12" }));
    expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ unit: "minutes" }));
    expect(screen.getByText("Capacidad no configurada")).toBeTruthy();
    expect(screen.getByText("No hay capacidad verificable")).toBeTruthy();
  });

  it("validates a reversed date range before requesting PMP data", () => {
    expect(validatePmpDateRange({ date_from: "2026-08-12", date_to: "2026-08-10" })).toMatch(/fecha inicial/i);
    expect(validatePmpDateRange({ date_from: "2026-08-10", date_to: "2026-08-12" })).toBeNull();
  });

  it("renders configured capacity instead of a staffing claim when data exists", () => {
    render(<PmpDashboard dashboard={dashboard(true)} orders={orders} errors={[]} areas={["MEC"]} filters={filters} onFiltersChange={vi.fn()} onOrderPage={vi.fn()} />);
    expect(screen.getByText("Capacidad suficiente")).toBeTruthy();
    expect(screen.getByText("Disponible")).toBeTruthy();
  });

  it("shows an empty detail state for a filtered area without orders", () => {
    render(<PmpDashboard dashboard={dashboard()} orders={{ ...orders, items: [], total: 0 }} errors={[]} areas={["MEC"]} filters={filters} onFiltersChange={vi.fn()} onOrderPage={vi.fn()} />);
    expect(screen.getByText("Sin órdenes para este alcance")).toBeTruthy();
  });
});
