import {
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  ClipboardList,
  Gauge,
  UsersRound,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type WorkloadUnit = "orders" | "minutes" | "hours";
export type PmpFilters = { area: string; status: string; as_of_date: string; shift: string; unit: WorkloadUnit };

export type PmpMetric = {
  total_orders: number; finalized_orders: number; pending_orders: number;
  planned_minutes: number; completed_planned_minutes: number; pending_planned_minutes: number;
  planned_hours: number; completed_planned_hours: number; pending_planned_hours: number;
  workload_completion_percent: number; order_completion_percent: number;
  target_gap_percentage_points: number; additional_completed_hours_lower_bound: number;
  strict_target_note: string; compliant: boolean; traffic_light: "green" | "yellow" | "red";
  risk_rank?: number | null; formatted: Record<string, string>;
};

export type PmpDashboardResponse = {
  metrics: {
    global: PmpMetric; by_area: Record<string, PmpMetric>; area_ranking: string[];
    highest_risk_area: string | null; alerts: { code: string; message: string }[];
    filter_application: { order_date_filter: string; as_of_date: string | null; orders_without_planned_start_date_excluded: number };
  };
  capacity: {
    configured: boolean; notice: string; available_shifts: string[];
    rows: { area: string; configured: boolean; available_hours: number | null; required_hours: number | null; gap_hours: number | null; staffing_gap_equivalent: number | null; status: string; missing_inputs: string[] }[];
  };
  metric_dictionary: Record<string, { label: string; formula: string; source_fields: string }>;
};

export type PmpOrder = { id: number; external_id: string; area: string; status: "pending" | "finalized"; planned_minutes: number; planned_hours: number; planned_start_date: string | null; source: string; source_row_number: number | null };
export type PmpOrdersResponse = { items: PmpOrder[]; total: number; offset: number; limit: number };
export type PmpImportError = { row_number: number; field_name: string; message: string; code?: string };

function n(value: number | null | undefined, digits = 1) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("es-CO", { maximumFractionDigits: digits }).format(value);
}

function TooltipLabel({ metric, dictionary }: { metric: string; dictionary: PmpDashboardResponse["metric_dictionary"] }) {
  const definition = dictionary[metric];
  if (!definition) return null;
  return <span className="pmp-tooltip" tabIndex={0} aria-label={`${definition.label}: ${definition.formula}. Fuente: ${definition.source_fields}`}><CircleHelp size={14} /><span role="tooltip"><strong>{definition.label}</strong>{definition.formula}<em>Fuente: {definition.source_fields}</em></span></span>;
}

function StatusChip({ metric }: { metric: PmpMetric }) {
  const text = metric.compliant ? "Cumple >90%" : metric.traffic_light === "yellow" ? "En vigilancia" : "Crítico";
  return <span className={`pmp-status ${metric.traffic_light}`}><span aria-hidden="true" />{text}</span>;
}

export function PmpDashboard({
  dashboard, orders, errors, areas, filters, onFiltersChange, onOrderPage,
}: {
  dashboard: PmpDashboardResponse; orders: PmpOrdersResponse; errors: PmpImportError[]; areas: string[];
  filters: PmpFilters; onFiltersChange: (next: PmpFilters) => void; onOrderPage: (offset: number) => void;
}) {
  const metrics = dashboard.metrics.global;
  const areaRows = Object.entries(dashboard.metrics.by_area).map(([area, value]) => ({ area, ...value }));
  const capacityRows = dashboard.capacity.rows;
  const set = (key: keyof PmpFilters, value: string) => onFiltersChange({ ...filters, [key]: value });
  const capacityUnavailable = !dashboard.capacity.configured;
  const unitLabel = filters.unit === "orders" ? "órdenes" : filters.unit === "minutes" ? "minutos" : "horas";
  const displayWork = (metric: PmpMetric, name: "planned" | "completed" | "pending") => {
    if (filters.unit === "orders") return name === "completed" ? metric.finalized_orders : name === "pending" ? metric.pending_orders : metric.total_orders;
    if (filters.unit === "minutes") return name === "completed" ? metric.completed_planned_minutes : name === "pending" ? metric.pending_planned_minutes : metric.planned_minutes;
    return name === "completed" ? metric.completed_planned_hours : name === "pending" ? metric.pending_planned_hours : metric.planned_hours;
  };
  const barData = areaRows.map((row) => ({
    area: row.area, planned: row.planned_hours, completed: row.completed_planned_hours, pending: row.pending_planned_hours,
    completion: row.workload_completion_percent, targetGap: row.target_gap_percentage_points,
  }));

  return <div className="pmp-dashboard" data-testid="pmp-dashboard">
    <section className="pmp-dashboard-hero">
      <div>
        <span className="eyebrow">Corte de PMP · fuente: JOSE.xlsx</span>
        <h2>Decisiones por carga real, no por conteo.</h2>
        <p>La meta se cumple únicamente al superar 90% de la carga planeada. La fecha de corte usa <strong>FechaPlaneadaInicio</strong> de la fuente, no una fecha inventada.</p>
      </div>
      <div className={`pmp-hero-status ${metrics.traffic_light}`}>
        <Gauge size={24} /><span>Estado de meta</span><strong>{metrics.workload_completion_percent.toFixed(2)}%</strong><StatusChip metric={metrics} />
      </div>
    </section>

    <section className="pmp-filter-panel" aria-label="Filtros PMP">
      <label>Área<select aria-label="Área" value={filters.area} onChange={(e) => set("area", e.target.value)}><option value="">Todas las áreas</option>{areas.map((area) => <option key={area} value={area}>{area}</option>)}</select></label>
      <label>Estado<select aria-label="Estado" value={filters.status} onChange={(e) => set("status", e.target.value)}><option value="">Todos</option><option value="pending">Pendientes</option><option value="finalized">Finalizadas</option></select></label>
      <label>Fecha de corte<input aria-label="Fecha de corte" type="date" value={filters.as_of_date} onChange={(e) => set("as_of_date", e.target.value)} /><small>Vacío: toda la fuente</small></label>
      <label>Turno<select aria-label="Turno" value={filters.shift} onChange={(e) => set("shift", e.target.value)} disabled={!dashboard.capacity.available_shifts.length}><option value="">Todos / sin asignar demanda</option>{dashboard.capacity.available_shifts.map((shift) => <option key={shift} value={shift}>Turno {shift}</option>)}</select></label>
      <fieldset className="pmp-unit-switch"><legend>Unidad de carga</legend>{(["orders", "minutes", "hours"] as const).map((unit) => <button key={unit} type="button" aria-pressed={filters.unit === unit} onClick={() => set("unit", unit)}>{unit === "orders" ? "Órdenes" : unit === "minutes" ? "Minutos" : "Horas"}</button>)}</fieldset>
    </section>
    {dashboard.metrics.filter_application.orders_without_planned_start_date_excluded > 0 && <p className="pmp-inline-warning"><AlertTriangle size={15} />Se excluyeron {dashboard.metrics.filter_application.orders_without_planned_start_date_excluded} órdenes sin FechaPlaneadaInicio al aplicar el corte.</p>}

    <section className="pmp-kpi-grid" aria-label="Indicadores principales PMP">
      {[
        ["Órdenes totales", n(metrics.total_orders, 0), "total_orders"], ["Finalizadas", n(metrics.finalized_orders, 0), "total_orders"], ["Pendientes", n(metrics.pending_orders, 0), "total_orders"],
        ["Horas planeadas", `${n(metrics.planned_hours)} h`, "planned_hours"], ["Horas completadas", `${n(metrics.completed_planned_hours)} h`, "completed_planned_hours"], ["Horas pendientes", `${n(metrics.pending_planned_hours)} h`, "pending_planned_hours"],
        ["Cumplimiento carga", `${n(metrics.workload_completion_percent, 2)}%`, "workload_completion_percent"], ["Cumplimiento órdenes", `${n(metrics.order_completion_percent, 2)}%`, "order_completion_percent"],
      ].map(([label, value, field]) => <article className="pmp-kpi" key={label}><span>{label}<TooltipLabel metric={field} dictionary={dashboard.metric_dictionary} /></span><strong>{value}</strong><small>{field === "workload_completion_percent" ? <StatusChip metric={metrics} /> : field === "total_orders" ? `${n(metrics.pending_orders, 0)} pendientes` : ""}</small></article>)}
    </section>

    <section className="pmp-chart-grid">
      <article className="pmp-chart-card"><header><div><span className="eyebrow">Comparación por área</span><h3>Horas planeadas, completadas y pendientes</h3></div><span className="pmp-chart-unit">Horas</span></header><ResponsiveContainer width="100%" height={310}><BarChart data={barData} margin={{ top: 12, right: 10, left: -18, bottom: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="area" /><YAxis /><Tooltip formatter={(value) => [`${n(Number(value))} h`, ""]} /><Legend /><Bar dataKey="planned" name="Planeadas" fill="#436e72" radius={[4, 4, 0, 0]} /><Bar dataKey="completed" name="Completadas" fill="#558b69" radius={[4, 4, 0, 0]} /><Bar dataKey="pending" name="Pendientes" fill="#c96e3c" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></article>
      <article className="pmp-chart-card"><header><div><span className="eyebrow">Meta explícita</span><h3>Avance de carga vs. umbral &gt;90%</h3></div><TooltipLabel metric="target" dictionary={dashboard.metric_dictionary} /></header><ResponsiveContainer width="100%" height={310}><BarChart data={barData} layout="vertical" margin={{ top: 12, right: 22, left: 8, bottom: 4 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" domain={[0, 100]} unit="%" /><YAxis type="category" dataKey="area" width={42} /><Tooltip formatter={(value) => [`${n(Number(value), 2)}%`, ""]} /><ReferenceLine x={90} stroke="#b04d34" strokeDasharray="4 4" label={{ value: "90%", position: "top", fill: "#8b432d" }} /><Bar dataKey="completion" name="Cumplimiento por carga" radius={[0, 4, 4, 0]}>{barData.map((entry) => <Cell key={entry.area} fill={entry.completion > 90 ? "#558b69" : entry.completion >= 80 ? "#c49832" : "#c96e3c"} />)}</Bar></BarChart></ResponsiveContainer></article>
    </section>

    <section className="pmp-chart-grid">
      <article className="pmp-table-card"><header><div><span className="eyebrow">Bottleneck ranking</span><h3>Riesgo por carga pendiente</h3></div><span className="pmp-chart-unit">{unitLabel}</span></header><div className="pmp-bottleneck-list">{dashboard.metrics.area_ranking.map((area) => { const row = dashboard.metrics.by_area[area]; const value = displayWork(row, "pending"); const top = Math.max(...areaRows.map((item) => displayWork(item, "pending")), 1); return <div key={area}><span className="pmp-rank">{row.risk_rank}</span><strong>{area}</strong><div className="pmp-bar"><i style={{ width: `${(value / top) * 100}%` }} /></div><b>{n(value)} {filters.unit === "hours" ? "h" : filters.unit === "minutes" ? "min" : ""}</b></div>; })}</div>{dashboard.metrics.highest_risk_area && <p className="pmp-risk-callout"><AlertTriangle size={16} /><strong>{dashboard.metrics.highest_risk_area}</strong> concentra la mayor carga pendiente.</p>}</article>
      <article className={`pmp-capacity-card ${capacityUnavailable ? "is-unavailable" : ""}`}><header><div><span className="eyebrow">Capacidad vs. demanda</span><h3>{capacityUnavailable ? "Capacidad no configurada" : "Cobertura por área"}</h3></div><UsersRound size={20} /></header>{capacityUnavailable ? <div className="pmp-capacity-empty"><AlertTriangle size={27} /><strong>No hay capacidad verificable</strong><p>Para calcularla se requieren: personal PMP activo, área y turno de cada persona, semana de programación y minutos disponibles por persona.</p></div> : <><p className="pmp-capacity-note">{dashboard.capacity.notice}</p><div className="pmp-capacity-rows">{capacityRows.map((row) => <div key={row.area}><strong>{row.area}</strong><span>Disponible <b>{n(row.available_hours)} h</b></span><span>Requerida <b>{n(row.required_hours)} h</b></span><span className={row.status === "insufficient" ? "danger" : "good"}>{row.status === "insufficient" ? `Brecha ${n(row.gap_hours)} h` : "Capacidad suficiente"}</span>{row.staffing_gap_equivalent !== null && row.status === "insufficient" && <small>Brecha equivalente: {n(row.staffing_gap_equivalent, 2)} personas-semana con la disponibilidad programada.</small>}</div>)}</div></>}</article>
    </section>

    <section className="pmp-table-card"><header><div><span className="eyebrow">Resumen de áreas · MEC incluido</span><h3>Decisión por área</h3></div><ClipboardList size={20} /></header><div className="pmp-table-wrap"><table><thead><tr><th>Área</th><th>Total / finalizadas</th><th>Planeadas</th><th>Completadas</th><th>Pendientes</th><th>Carga / órdenes</th><th>Meta &gt;90%</th><th>Brecha para meta</th></tr></thead><tbody>{areaRows.map((row) => <tr key={row.area}><td><strong>{row.area}</strong>{row.area === "MEC" && <small className="pmp-mec-mark">en foco</small>}</td><td>{n(row.total_orders, 0)} / {n(row.finalized_orders, 0)}<small>{n(row.pending_orders, 0)} pendientes</small></td><td>{n(row.planned_hours)} h</td><td>{n(row.completed_planned_hours)} h</td><td>{n(row.pending_planned_hours)} h</td><td>{n(row.workload_completion_percent, 2)}% / {n(row.order_completion_percent, 2)}%</td><td><StatusChip metric={row} /></td><td>{row.compliant ? "—" : <><b>{n(row.target_gap_percentage_points, 2)} pp</b><small>&gt; {n(row.additional_completed_hours_lower_bound)} h mínimo estricto</small></>}</td></tr>)}</tbody></table></div></section>

    <section className="pmp-table-card"><header><div><span className="eyebrow">Profundización de órdenes</span><h3>Órdenes del alcance ({n(orders.total, 0)})</h3></div></header>{orders.items.length ? <><div className="pmp-table-wrap"><table><thead><tr><th>Orden</th><th>Área</th><th>Estado</th><th>Tiempo planeado</th><th>Fecha planeada</th><th>Origen / fila</th></tr></thead><tbody>{orders.items.map((order) => <tr key={order.id}><td><strong>{order.external_id}</strong></td><td>{order.area}</td><td><span className={`pmp-order-status ${order.status}`}>{order.status === "finalized" ? "Finalizada" : "Pendiente"}</span></td><td>{n(order.planned_minutes)} min <small>{n(order.planned_hours)} h</small></td><td>{order.planned_start_date || "Sin fecha fuente"}</td><td>{order.source} {order.source_row_number ? `· fila ${order.source_row_number}` : ""}</td></tr>)}</tbody></table></div><footer className="pmp-pagination"><span>Mostrando {orders.offset + 1}–{Math.min(orders.offset + orders.limit, orders.total)} de {orders.total}</span><div><button type="button" className="secondary" disabled={orders.offset === 0} onClick={() => onOrderPage(Math.max(0, orders.offset - orders.limit))}>Anterior</button><button type="button" className="secondary" disabled={orders.offset + orders.limit >= orders.total} onClick={() => onOrderPage(orders.offset + orders.limit)}>Siguiente</button></div></footer></> : <div className="pmp-empty"><ClipboardList size={26} /><strong>Sin órdenes para este alcance</strong><p>Ajusta los filtros o confirma que la carga inicial esté disponible.</p></div>}</section>

    <section className="pmp-quality-card"><header><div><span className="eyebrow">Calidad y reconciliación</span><h3>Diagnósticos de fuente</h3></div>{errors.length ? <span className="pmp-quality-count"><AlertTriangle size={16} />{errors.length} inconsistencias</span> : <span className="pmp-quality-count good"><CheckCircle2 size={16} />Sin diagnósticos</span>}</header>{errors.length ? <div className="pmp-table-wrap"><table><thead><tr><th>Fila Excel</th><th>Campo</th><th>Motivo</th></tr></thead><tbody>{errors.slice(0, 20).map((error) => <tr key={`${error.row_number}-${error.field_name}`}><td>{error.row_number}</td><td>{error.field_name}</td><td>{error.message}</td></tr>)}</tbody></table></div> : <p>Las filas válidas del alcance no presentan errores de importación.</p>}</section>
  </div>;
}
