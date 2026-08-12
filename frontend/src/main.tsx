import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CalendarDays,
  ChevronDown,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Database,
  FileDown,
  FileText,
  Factory,
  Home,
  LogOut,
  MapPin,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Target,
  TrendingUp,
  UploadCloud,
  Users,
  Wrench,
  X
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { API_URL, api, Equipment, ProductionLine, Upload, User } from "./lib/api";
import { ReportDeleteAction } from "./components/ReportDeleteAction";
import { ReportRangeControls } from "./components/ReportRangeControls";
import { PmpDashboard, PmpDashboardResponse, PmpFilters, PmpImportError, PmpOrdersResponse } from "./components/PmpDashboard";
import "./styles.css";

type View = "home" | "dashboard" | "equipment" | "lines" | "reports" | "pmp" | "management_reports" | "users";
type NavItem = readonly [View, React.ElementType, string, string];
type KpiTone = "good" | "warn" | "danger" | "neutral";
type KpiItem = [string, React.ReactNode, string?, KpiTone?];
type FilterState = {
  date_from: string;
  date_to: string;
  year: string;
  month: string;
  production_line_id: string;
  equipment_id: string;
  shift_id: string;
};
type FailureMode = { id: number; name: string; is_active: boolean };
type ShiftOption = { id: number; name: string; is_active: boolean };
type DailyReport = {
  id: number;
  event_date: string;
  equipment_id: number;
  equipment_code?: string | null;
  line_name: string;
  area_code?: string | null;
  area_name?: string | null;
  process_code?: string | null;
  process_name?: string | null;
  shift_name: string;
  equipment_name: string;
  failure_mode_name: string;
  damage_description: string;
  reason_description: string;
  downtime_minutes: number;
  frequency: number;
  reported_by: string;
  created_at: string;
};
type IncidentEquipmentGroup = {
  id: number;
  code?: string | null;
  name: string;
  areaCode?: string | null;
  areaName?: string | null;
  processCode?: string | null;
  processName?: string | null;
  reports: DailyReport[];
};
type CatalogFilterOptions = {
  areas: { code: string; name: string }[];
  processes: { code: string; name: string; area_code: string }[];
};
type SearchOption = { value: string; label: string; searchText?: string; meta?: string };

const emptyFilters: FilterState = {
  date_from: "",
  date_to: "",
  year: "",
  month: "",
  production_line_id: "",
  equipment_id: "",
  shift_id: "",
};

const nav: readonly NavItem[] = [
  ["home", Home, "Inicio", "Resumen operativo"],
  ["dashboard", BarChart3, "Dashboard", "Gerencia"],
  ["equipment", Wrench, "Equipos", "Incidentes"],
  ["lines", Factory, "Áreas", "Taxonomía"],
  ["reports", ClipboardCheck, "Reportes", "Fallas diarias"],
  ["pmp", ClipboardCheck, "PMP", "Plan preventivo"],
  ["management_reports", FileText, "Reportes gerenciales", "Exportación PDF"],
  ["users", Users, "Usuarios", "Accesos"]
];

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>("home");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.me().then(setUser).catch(() => null).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="boot"><Factory /> Inicializando consola...</div>;
  if (!user) return <Login onLogin={setUser} />;

  const active = nav.find(([id]) => id === view);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img className="brand-logo" src="/cek-logo.png" alt="CEK Global Inspection Services" />
          <div>
            <strong>Control de mantenimiento</strong>
            <span>Operación industrial</span>
          </div>
        </div>

        <nav className="side-nav" aria-label="Navegación principal">
          {nav.map(([id, Icon, label, meta]) => {
            if ((id === "reports" || id === "users" || id === "management_reports") && user.role !== "admin") return null;
            return (
              <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}>
                <Icon size={18} />
                <span>{label}<small>{meta}</small></span>
              </button>
            );
          })}
        </nav>

        <div className="account">
          <div className="account-avatar">{initials(user.name)}</div>
          <div>
            <span>{user.name}</span>
            <small>{user.role === "admin" ? "Administrador" : "Usuario planta"}</small>
          </div>
          <button onClick={() => { api.logout(); setUser(null); setView("home"); }}><LogOut size={16} />Salir</button>
        </div>
      </aside>

      <main>
        <div className="topbar">
          <div>
            <span className="eyebrow">{active?.[3] || "MVP"}</span>
            <strong>{active?.[2] || "Mantenimiento"}</strong>
          </div>
          <div className="topbar-actions">
            <span className="live-dot">Sistema activo</span>
            <span className="role-badge">{user.role === "admin" ? "Admin" : "Planta"}</span>
          </div>
        </div>

        {view === "home" && <HomePage setView={setView} />}
        {view === "dashboard" && <DashboardPage />}
        {view === "equipment" && <EquipmentPage user={user} />}
        {view === "lines" && <LinesPage user={user} />}
        {view === "reports" && user.role === "admin" && <ReportsPage user={user} />}
        {view === "pmp" && <PmpPage user={user} />}
        {view === "management_reports" && user.role === "admin" && <ManagementReports />}
        {view === "users" && <UsersPage />}
      </main>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = useState("admin@mantenimiento.local");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const result = await api.login(email, password);
      api.setToken(result.access_token);
      onLogin(result.user);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="login">
      <section className="login-hero">
        <img className="login-logo" src="/cek-logo.png" alt="CEK Global Inspection Services" />
        <span className="eyebrow">Global Inspection Services</span>
        <h1>Control de paradas de mantenimiento</h1>
        <p>Centraliza cargas Excel, valida datos históricos y entrega indicadores gerenciales de tiempo perdido.</p>
        <div className="login-proof">
          <span><Database size={16} />Raw + validado</span>
          <span><ShieldCheck size={16} />Roles y trazabilidad</span>
          <span><BarChart3 size={16} />Pareto gerencial</span>
        </div>
      </section>
      <form onSubmit={submit} className="login-card">
        <span className="eyebrow">Acceso seguro</span>
        <h2>Iniciar sesión</h2>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Contraseña<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary">Entrar al sistema</button>
        <small>Admin: admin@mantenimiento.local / Admin123!<br />Planta: planta@mantenimiento.local / Planta123!</small>
      </form>
    </div>
  );
}

function PageTitle({ title, subtitle, action }: { title: string; subtitle: string; action?: React.ReactNode }) {
  return (
    <header className="page-title">
      <div>
        <span className="eyebrow">Mantenimiento industrial</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </header>
  );
}

function searchableText(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("es-CO");
}

function SearchableSelect({
  label,
  placeholder,
  options,
  value,
  onChange,
  disabled = false,
  required = false,
  emptyText = "No hay coincidencias",
  className = "",
}: {
  label: string;
  placeholder: string;
  options: SearchOption[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  required?: boolean;
  emptyText?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const selected = options.find((option) => option.value === value);
  const term = searchableText(search.trim());
  const matches = options.filter((option) => searchableText(`${option.label} ${option.searchText || ""} ${option.meta || ""}`).includes(term)).slice(0, 80);

  return (
    <div className={`searchable-field ${className}`}>
      <span className="searchable-label">{label}</span>
      <div className={`searchable-select ${open ? "open" : ""} ${disabled ? "disabled" : ""}`}>
        <Search size={16} className="searchable-icon" />
        <input
          required={required}
          disabled={disabled}
          autoComplete="off"
          aria-label={label}
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          placeholder={placeholder}
          value={open ? search : selected?.label || ""}
          onFocus={(event) => {
            const input = event.currentTarget;
            setSearch(selected?.label || "");
            setOpen(true);
            requestAnimationFrame(() => input.select());
          }}
          onChange={(event) => {
            setSearch(event.target.value);
            if (value) onChange("");
            setOpen(true);
          }}
          onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        />
        <ChevronDown size={16} className="searchable-chevron" />
        {open && !disabled && (
          <div className="searchable-menu" role="listbox">
            {matches.length ? matches.map((option) => (
              <button
                type="button"
                role="option"
                aria-selected={option.value === value}
                key={option.value}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onChange(option.value);
                  setSearch(option.label);
                  setOpen(false);
                }}
              >
                <span><strong>{option.label}</strong>{option.meta && <small>{option.meta}</small>}</span>
                {option.value === value && <CheckCircle2 size={16} />}
              </button>
            )) : <div className="searchable-empty">{emptyText}</div>}
          </div>
        )}
      </div>
    </div>
  );
}

function HomePage({ setView }: { setView: (v: View) => void }) {
  const [dash, setDash] = useState<any>(null);
  const [catalog, setCatalog] = useState<any>(null);
  const [dailyReports, setDailyReports] = useState<DailyReport[]>([]);

  useEffect(() => {
    api.request<any>("/dashboard/summary").then(setDash);
    api.request<any>("/catalog-stats").then(setCatalog);
    api.request<DailyReport[]>("/daily-reports").then(setDailyReports);
  }, []);

  const last = dailyReports[0];
  const kpis = dash?.kpis;

  return (
    <>
      <PageTitle
        title="Centro de control"
        subtitle="Reportes diarios, catálogo de activos y desempeño de mantenimiento."
        action={<button className="primary" onClick={() => setView("pmp")}><ClipboardCheck size={18} />Ver PMP</button>}
      />
      <section className="command-panel">
        <div>
          <span className="eyebrow">Registro del día</span>
          <h2>{last ? `${last.equipment_name} · Turno ${last.shift_name}` : "Aún no hay reportes hoy"}</h2>
          <p>{last ? `${last.failure_mode_name} · ${formatNumber(last.downtime_minutes)} minutos` : "Registra la primera falla para alimentar los indicadores del dashboard."}</p>
        </div>
        <div className="command-strip">
          <span><CheckCircle2 size={18} />{formatNumber(dailyReports.length)} reportes hoy</span>
          <span><Factory size={18} />{formatNumber(catalog?.active_lines ?? 0)} áreas activas</span>
          <span><Wrench size={18} />{formatNumber(catalog?.reportable_equipment ?? 0)} activos seleccionables</span>
        </div>
      </section>
      <KpiGrid items={[
        ["Tiempo perdido", `${formatNumber(kpis?.total_minutes ?? 0)} min`, `${kpis?.total_hours ?? 0} horas`, "danger"],
        ["Equipo crítico", kpis?.critical_equipment ?? "Sin datos", "Mayor impacto por tiempo", "warn"],
        ["Eventos reportados", formatNumber(kpis?.total_events ?? 0), "Registros manuales confirmados", "good"],
        ["Frecuencia total", formatNumber(kpis?.total_frequency ?? 0), "Ocurrencias reportadas", "neutral"],
      ]} />
    </>
  );
}

function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Upload | null>(null);
  const [preview, setPreview] = useState<any[]>([]);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const upload = await api.request<Upload>("/uploads", { method: "POST", body: form });
      setResult(upload);
      setPreview(await api.request<any[]>(`/uploads/${upload.id}/preview`));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function confirm() {
    if (!result) return;
    const updated = await api.request<Upload>(`/uploads/${result.id}/confirm`, { method: "POST" });
    setResult(updated);
  }

  return (
    <>
      <PageTitle title="Cargar archivo" subtitle="Valida el Excel antes de confirmar datos en el histórico limpio." />
      <form className="upload-box" onSubmit={submit}>
        <div className="drop-zone">
          <UploadCloud size={30} />
          <div>
            <strong>{file?.name || "Selecciona un archivo .xlsx"}</strong>
            <span>Solo Excel, máximo 20 MB. Las columnas extra se ignoran con advertencia.</span>
          </div>
          <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>
        <button className="primary" disabled={!file}><UploadCloud size={18} />Validar Excel</button>
      </form>
      {error && <div className="error">{error}</div>}
      {result && <StatusBand upload={result} onConfirm={confirm} />}
      <PreviewTable rows={preview} />
    </>
  );
}

function StatusBand({ upload, onConfirm }: { upload: Upload; onConfirm: () => void }) {
  return (
    <div className={`status-band ${upload.status}`}>
      <strong>{statusLabel(upload.status)}</strong>
      <span>{formatNumber(upload.total_rows)} filas</span>
      <span>{formatNumber(upload.valid_rows)} válidas</span>
      <span>{formatNumber(upload.error_rows)} errores</span>
      <span>{formatNumber(upload.warning_rows)} advertencias</span>
      {upload.status === "ready_to_confirm" && <button onClick={onConfirm}>Confirmar carga</button>}
    </div>
  );
}

function PreviewTable({ rows }: { rows: any[] }) {
  if (!rows.length) return <EmptyState title="Sin vista previa" text="Cuando subas un archivo válido, aquí aparecerán las primeras filas leídas." />;
  return (
    <DataTable
      headers={["Fila", "Fecha", "Línea", "Turno", "Equipo", "Daño", "Razón", "Tiempo", "Frecuencia", "Estado"]}
      rows={rows.map((r) => [r.row_number, r.fecha, r.linea, r.turno, r.equipo, r.dano, r.razon, r.tiempo, r.frecuencia, <span className={`pill ${r.status}`}>{statusLabel(r.status)}</span>])}
    />
  );
}

function LoadsPage() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  useEffect(() => { api.request<Upload[]>("/uploads").then(setUploads); }, []);
  return <><PageTitle title="Cargas" subtitle="Histórico de archivos, versiones y estados de validación." /><UploadTable uploads={uploads} /></>;
}

function UploadTable({ uploads }: { uploads: Upload[] }) {
  if (!uploads.length) return <EmptyState title="No hay cargas" text="Sube el primer archivo Excel para crear histórico." />;
  return (
    <DataTable
      headers={["Archivo", "Estado", "Filas", "Válidas", "Errores", "Advertencias", "Fecha"]}
      rows={uploads.map((u) => [
        u.original_filename,
        <span className={`pill ${u.status}`}>{statusLabel(u.status)}</span>,
        formatNumber(u.total_rows),
        formatNumber(u.valid_rows),
        formatNumber(u.error_rows),
        formatNumber(u.warning_rows),
        new Date(u.uploaded_at).toLocaleString()
      ])}
    />
  );
}

function CorrectionsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  useEffect(() => { refresh(); api.request<Equipment[]>("/equipment").then(setEquipment); }, []);
  function refresh() { api.request<any[]>("/corrections/pending").then(setRows); }
  async function correct(rowId: number, equipmentId: string) {
    await api.request(`/raw-events/${rowId}/correction`, { method: "PATCH", body: JSON.stringify({ equipment_id: Number(equipmentId) }) });
    refresh();
  }

  return (
    <>
      <PageTitle title="Correcciones pendientes" subtitle="Corrige equipos usando solo valores existentes del catálogo maestro." />
      {!rows.length ? <EmptyState title="Sin pendientes" text="No hay registros bloqueantes esperando corrección." /> : (
        <DataTable
          headers={["Fila", "Línea", "Equipo original", "Daño", "Corrección"]}
          rows={rows.map((r) => [
            r.row_number,
            r.linea,
            <span className="pill danger">{r.equipo}</span>,
            r.dano,
            <select onChange={(e) => e.target.value && correct(r.id, e.target.value)}>
              <option>Seleccionar equipo</option>
              {equipment.map((eq) => <option key={eq.id} value={eq.id}>{eq.name}</option>)}
            </select>
          ])}
        />
      )}
    </>
  );
}

function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [options, setOptions] = useState<any>(null);
  const [filters, setFilters] = useState<FilterState>(emptyFilters);
  const [loading, setLoading] = useState(false);
  const [trendMetric, setTrendMetric] = useState<"downtime" | "events">("downtime");
  useEffect(() => {
    api.request<any>("/dashboard/filters").then(setOptions);
    loadDashboard(filters);
  }, []);
  async function loadDashboard(nextFilters: FilterState) {
    setLoading(true);
    try {
      setData(await api.request<any>(`/dashboard/summary${queryString(nextFilters)}`));
    } finally {
      setLoading(false);
    }
  }
  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    loadDashboard(filters);
  }
  if (!data) return <PageTitle title="Dashboard" subtitle="Cargando indicadores validados..." />;

  const period = formatPeriod(data.period?.date_from, data.period?.date_to);
  const activeFilterCount = Object.values(filters).filter(Boolean).length;
  const trendData = data.daily_trend?.length > 62 ? data.downtime_by_month : data.daily_trend;
  const peakDay = data.insights?.peak_day;
  const highestMttr = [...(data.critical_equipment || [])].sort((a: any, b: any) => b.mttr - a.mttr)[0];

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div>
          <span className="dashboard-kicker"><Activity size={14} /> Inteligencia de mantenimiento</span>
          <h1>Centro de confiabilidad</h1>
          <p>Lectura ejecutiva del desempeño, la recurrencia y los activos que concentran el impacto operacional.</p>
        </div>
        <div className="dashboard-period">
          <CalendarDays size={20} />
          <div><small>PERÍODO ANALIZADO</small><strong>{period}</strong></div>
          <button className={`icon-button ${loading ? "loading" : ""}`} onClick={() => loadDashboard(filters)} disabled={loading} title="Actualizar dashboard" aria-label="Actualizar dashboard">
            <RefreshCw size={18} />
          </button>
        </div>
      </section>

      <FilterBar filters={filters} setFilters={setFilters} options={options} onSubmit={applyFilters} onReset={() => { setFilters(emptyFilters); loadDashboard(emptyFilters); }} />
      <div className="filter-context">
        <span>{activeFilterCount ? `${activeFilterCount} filtros activos` : "Vista consolidada"}</span>
        <span>Último dato: {data.period?.date_to ? formatDate(data.period.date_to) : "Sin registros"}</span>
      </div>

      <SectionHeading number="01" eyebrow="Pulso operacional" title="Indicadores del período" subtitle="Resultados calculados sobre registros confirmados y el alcance de los filtros activos." />
      <KpiGrid items={[
        ["Tiempo perdido", `${formatNumber(data.kpis.total_minutes)} min`, `${formatNumber(data.kpis.total_hours)} horas de parada`, "danger"],
        ["Eventos analizados", formatNumber(data.kpis.total_events), `${formatNumber(data.kpis.total_frequency)} ocurrencias`, "neutral"],
        ["MTTR global", `${formatNumber(data.kpis.mttr)} min`, "Tiempo medio por ocurrencia", "warn"],
        ["Equipo crítico", data.kpis.critical_equipment, "Mayor tiempo perdido", "danger"],
        ["Línea crítica", data.kpis.critical_line, "Mayor impacto acumulado", "warn"],
        ["Concentración Top 4", `${formatNumber(data.kpis.top_four_percentage)}%`, "Del downtime en cuatro equipos", "good"],
      ]} />

      <SectionHeading number="02" eyebrow="Comportamiento" title="Evolución del desempeño" subtitle="Alterna entre tiempo perdido y volumen de eventos para leer magnitud y recurrencia." />
      <article className="chart chart-featured">
        <div className="chart-heading">
          <div><span className="chart-label">TENDENCIA</span><h3>{trendMetric === "downtime" ? "Tiempo perdido" : "Eventos registrados"}</h3></div>
          <div className="metric-switch" role="group" aria-label="Métrica de tendencia">
            <button className={trendMetric === "downtime" ? "active" : ""} onClick={() => setTrendMetric("downtime")}>Tiempo</button>
            <button className={trendMetric === "events" ? "active" : ""} onClick={() => setTrendMetric("events")}>Frecuencia</button>
          </div>
        </div>
        <ResponsiveContainer height={330}>
          <ComposedChart data={trendData} margin={{ left: 4, right: 18, top: 16, bottom: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#d9ded6" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} minTickGap={28} tickFormatter={shortDateLabel} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip labelFormatter={(value) => formatChartDate(String(value))} formatter={(value: any) => [formatNumber(value ?? 0), trendMetric === "downtime" ? "Minutos" : "Eventos"]} />
            <Bar dataKey={trendMetric} fill="#d7c5a2" radius={[5, 5, 0, 0]} opacity={0.65} />
            <Line type="monotone" dataKey={trendMetric} stroke="#b45a2b" strokeWidth={3} dot={false} activeDot={{ r: 5 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </article>

      <SectionHeading number="03" eyebrow="Distribución" title="Dónde se concentra el impacto" subtitle="Comparación por línea y turno dentro del mismo universo filtrado." />
      <ChartGrid>
        <Chart title="Tiempo perdido por línea" data={data.downtime_by_line} horizontal color="#254f55" valueLabel="Tiempo perdido" unit=" min" />
        <Chart title="Distribución por turno" data={data.by_shift} color="#596b4f" valueLabel="Tiempo perdido" unit=" min" />
      </ChartGrid>

      <SectionHeading number="04" eyebrow="Criticidad" title="Equipos que más afectaron la operación" subtitle={`Los cuatro equipos principales concentran ${formatNumber(data.insights.top_four_percentage)}% del downtime del período.`} />
      <ChartGrid>
        <Pareto data={data.pareto} />
        <ScatterPanel data={data.downtime_vs_frequency} />
      </ChartGrid>
      <CriticalityTable rows={data.critical_equipment} />

      <SectionHeading number="05" eyebrow="Causas registradas" title="Motivos con mayor impacto" subtitle="Vista agregada de las razones consignadas; no incluye tarjetas ni listado de daños encontrados." />
      <Chart title="Tiempo perdido por causa registrada" data={data.top_reasons} horizontal color="#c98324" valueLabel="Tiempo perdido" unit=" min" />

      <SectionHeading number="06" eyebrow="Inteligencia operacional" title="Señales que merecen atención" subtitle="Lectura automática y transparente a partir del período filtrado." />
      <section className="insight-grid">
        <InsightCard icon={<Target size={19} />} label="Mayor tiempo perdido" value={data.insights.highest_downtime.name} detail={`${formatNumber(data.insights.highest_downtime.minutes)} min · ${formatNumber(data.insights.highest_downtime.percentage)}% del total`} />
        <InsightCard icon={<TrendingUp size={19} />} label="Mayor recurrencia" value={data.insights.highest_frequency.name} detail={`${formatNumber(data.insights.highest_frequency.frequency)} ocurrencias`} />
        <InsightCard icon={<CalendarDays size={19} />} label="Día de mayor afectación" value={peakDay?.date ? formatDate(peakDay.date) : "Sin datos"} detail={`${formatNumber(peakDay?.minutes || 0)} min · ${formatNumber(peakDay?.events || 0)} eventos`} />
        <InsightCard icon={<Clock3 size={19} />} label="Mayor MTTR del Top 12" value={highestMttr?.name || "Sin datos"} detail={`${formatNumber(highestMttr?.mttr || 0)} min por ocurrencia`} />
      </section>

      <section className="analysis-panel">
        <div className="analysis-copy">
          <span className="chart-label">DIAGNÓSTICO AUTOMÁTICO</span>
          <h2>Lectura técnica del período</h2>
          <p>Se analizaron <strong>{formatNumber(data.kpis.total_events)} eventos</strong>, equivalentes a <strong>{formatNumber(data.kpis.total_minutes)} minutos</strong> de parada. <strong>{data.kpis.critical_equipment}</strong> fue el activo con mayor impacto y <strong>{data.kpis.critical_line}</strong> la línea con mayor downtime.</p>
          <p>La concentración del Top 4 es de <strong>{formatNumber(data.kpis.top_four_percentage)}%</strong>. Este indicador ayuda a decidir si conviene intervenir pocos activos críticos o ampliar el plan preventivo a una población mayor.</p>
        </div>
        <div className="recommendation-list">
          <span className="chart-label">PLAN SUGERIDO</span>
          <h3>Prioridades de intervención</h3>
          <ol>
            <li>Ejecutar análisis de causa raíz sobre <strong>{data.kpis.critical_equipment}</strong> y sus eventos más recurrentes.</li>
            <li>Revisar el plan preventivo de <strong>{data.kpis.critical_line}</strong>, empezando por los equipos del Top 4.</li>
            <li>Dar seguimiento semanal a <strong>{highestMttr?.name || "los equipos con mayor MTTR"}</strong> para reducir duración, además de frecuencia.</li>
          </ol>
        </div>
      </section>
    </div>
  );
}

function SectionHeading({ number, eyebrow, title, subtitle }: { number: string; eyebrow: string; title: string; subtitle: string }) {
  return <header className="dashboard-section-heading"><span>{number}</span><div><small>{eyebrow}</small><h2>{title}</h2><p>{subtitle}</p></div></header>;
}

function InsightCard({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: string; detail: string }) {
  return <article className="insight-card"><div className="insight-icon">{icon}</div><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>;
}

function CriticalityTable({ rows }: { rows: any[] }) {
  return (
    <div className="table-wrap criticality-table">
      <table>
        <thead><tr><th>#</th><th>Equipo</th><th>Tiempo perdido</th><th>Frecuencia</th><th>MTTR</th><th>% total</th><th>% acumulado</th></tr></thead>
        <tbody>{rows.map((row, index) => <tr key={row.name}>
          <td><span className="rank-badge">{index + 1}</span></td><td><strong>{row.name}</strong></td><td>{formatNumber(row.downtime)} min</td><td>{formatNumber(row.frequency)}</td><td>{formatNumber(row.mttr)} min</td><td>{formatNumber(row.percentage)}%</td><td><div className="progress-cell"><span style={{ width: `${Math.min(row.cumulative, 100)}%` }} />{formatNumber(row.cumulative)}%</div></td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}

function QualityPage() {
  const [q, setQ] = useState<any>(null);
  useEffect(() => { api.request<any>("/data-quality/summary").then(setQ); }, []);
  return (
    <>
      <PageTitle title="Calidad de datos" subtitle="Pendientes, advertencias y trazabilidad de correcciones." />
      {q && <>
        <KpiGrid items={[
          ["Archivos cargados", q.uploads, "Incluye rechazados para auditoría", "neutral"],
          ["Archivos pendientes", q.pending_uploads, "Requieren acción", q.pending_uploads ? "warn" : "good"],
          ["Errores abiertos", q.open_errors, "Bloqueantes activos", q.open_errors ? "danger" : "good"],
          ["Advertencias", formatNumber(q.warnings), "Datos útiles con observación", "warn"],
          ["Registros corregidos", q.corrected_records, "Trazabilidad aplicada", "neutral"],
          ["Calidad", `${q.data_quality_percent}%`, "Sobre cargas activas", "good"],
        ]} />
        <ChartGrid><Chart title="Alertas por tipo" data={q.errors_by_type.map((x: any) => ({ name: x.type, value: x.count }))} color="#b45a2b" /></ChartGrid>
      </>}
    </>
  );
}

function FilterBar({ filters, setFilters, options, onSubmit, onReset }: { filters: FilterState; setFilters: (filters: FilterState) => void; options: any; onSubmit: (e: React.FormEvent) => void; onReset?: () => void }) {
  const set = (key: keyof FilterState, value: string) => setFilters({ ...filters, [key]: value });
  return (
    <form className="filter-bar" onSubmit={onSubmit}>
      <label>Desde<input type="date" value={filters.date_from} onChange={(e) => set("date_from", e.target.value)} /></label>
      <label>Hasta<input type="date" value={filters.date_to} onChange={(e) => set("date_to", e.target.value)} /></label>
      <label>Año<select value={filters.year} onChange={(e) => set("year", e.target.value)}><option value="">Todos</option>{options?.years?.map((year: number) => <option key={year} value={year}>{year}</option>)}</select></label>
      <label>Mes<select value={filters.month} onChange={(e) => set("month", e.target.value)}><option value="">Todos</option>{options?.months?.map((month: number) => <option key={month} value={month}>{month}</option>)}</select></label>
      <label>Línea<select value={filters.production_line_id} onChange={(e) => set("production_line_id", e.target.value)}><option value="">Todas</option>{options?.lines?.map((line: any) => <option key={line.id} value={line.id}>{line.name}</option>)}</select></label>
      <label>Equipo<select value={filters.equipment_id} onChange={(e) => set("equipment_id", e.target.value)}><option value="">Todos</option>{options?.equipment?.filter((item: any) => !filters.production_line_id || String(item.production_line_id) === filters.production_line_id).map((item: any) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Turno<select value={filters.shift_id} onChange={(e) => set("shift_id", e.target.value)}><option value="">Todos</option>{options?.shifts?.map((shift: any) => <option key={shift.id} value={shift.id}>{shift.name}</option>)}</select></label>
      <button className="primary">Aplicar filtros</button>
      <button type="button" className="secondary" onClick={() => { setFilters(emptyFilters); onReset?.(); }}>Limpiar</button>
    </form>
  );
}

function EquipmentPage({ user }: { user: User }) {
  const todayIso = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const [dateFrom, setDateFrom] = useState(todayIso);
  const [dateTo, setDateTo] = useState(todayIso);
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [selectedEquipment, setSelectedEquipment] = useState<IncidentEquipmentGroup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lines, setLines] = useState<ProductionLine[]>([]);
  const [showAddAsset, setShowAddAsset] = useState(false);
  const [assetName, setAssetName] = useState("");
  const [assetCode, setAssetCode] = useState("");
  const [assetLineId, setAssetLineId] = useState("");
  const [adminMessage, setAdminMessage] = useState("");
  const [reportMessage, setReportMessage] = useState("");

  useEffect(() => {
    if (user.role === "admin") {
      api.request<ProductionLine[]>("/production-lines?include_inactive=false").then(setLines).catch((err) => setError((err as Error).message));
    }
  }, [user.role]);

  useEffect(() => { refreshIncidents(); }, []);

  useEffect(() => {
    if (!selectedEquipment) return;
    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setSelectedEquipment(null); };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [selectedEquipment]);

  const groupMap = new Map<number, IncidentEquipmentGroup>();
  reports.forEach((report) => {
    const current = groupMap.get(report.equipment_id);
    if (current) current.reports.push(report);
    else groupMap.set(report.equipment_id, {
      id: report.equipment_id,
      code: report.equipment_code,
      name: report.equipment_name,
      areaCode: report.area_code,
      areaName: report.area_name || report.line_name,
      processCode: report.process_code,
      processName: report.process_name,
      reports: [report],
    });
  });
  const equipmentGroups = Array.from(groupMap.values()).sort((a, b) => totalDowntime(b.reports) - totalDowntime(a.reports));
  const totalDayDowntime = totalDowntime(reports);
  const selectedDateLabel = dateFrom === dateTo ? formatDate(dateFrom) : `${formatDate(dateFrom)} — ${formatDate(dateTo)}`;

  async function refreshIncidents() {
    if (dateFrom > dateTo) {
      setError("La fecha inicial no puede ser posterior a la fecha final.");
      return;
    }
    setSelectedEquipment(null);
    setLoading(true);
    setError("");
    try {
      setReports(await api.request<DailyReport[]>(`/daily-reports?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function deleteReport(reportId: number) {
    setError("");
    setReportMessage("");
    await api.request<{ id: number; deleted: boolean }>(`/daily-reports/${reportId}`, { method: "DELETE" });
    setReportMessage("Reporte eliminado correctamente.");
    await refreshIncidents();
  }

  async function createAsset() {
    setError("");
    setAdminMessage("");
    try {
      await api.request("/equipment", { method: "POST", body: JSON.stringify({ name: assetName, code: assetCode, production_line_id: Number(assetLineId), is_active: true }) });
      setAssetName("");
      setAssetCode("");
      setAssetLineId("");
      setAdminMessage("Activo agregado correctamente.");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="equipment-incidents-page">
      <PageTitle
        title="Equipos con fallas"
        subtitle="Consulta los equipos que presentaron reportes en un rango de fechas y abre cada tarjeta para revisar el detalle de sus fallas."
        action={user.role === "admin" ? <button className="secondary" onClick={() => setShowAddAsset((value) => !value)}><Plus size={17} />Agregar activo</button> : undefined}
      />

      <section className="incident-date-panel">
        <div>
          <span className="eyebrow">Período consultado</span>
          <h2>{selectedDateLabel}</h2>
          <p>El rango incluye ambas fechas y conserva el orden de los reportes.</p>
        </div>
        <ReportRangeControls dateFrom={dateFrom} dateTo={dateTo} maxDate={todayIso} loading={loading} onDateFromChange={setDateFrom} onDateToChange={setDateTo} onApply={refreshIncidents} />
      </section>

      <section className="incident-day-metrics">
        <article><span>Equipos afectados</span><strong>{equipmentGroups.length}</strong><small>Con reportes en el rango</small></article>
        <article><span>Reportes registrados</span><strong>{reports.length}</strong><small>Eventos puntuales del período</small></article>
        <article><span>Tiempo total</span><strong>{formatNumber(totalDayDowntime)} <em>min</em></strong><small>{formatNumber(totalDayDowntime / 60)} horas acumuladas</small></article>
      </section>

      {showAddAsset && user.role === "admin" && (
        <section className="admin-catalog-card equipment-create-card">
          <div><span className="eyebrow">Solo administradores</span><h3>Agregar activo</h3><p>Esta acción administrativa no modifica la consulta de incidentes.</p></div>
          <div className="inline-form"><input value={assetCode} onChange={(event) => setAssetCode(event.target.value.toUpperCase())} placeholder="Código, ej. BA-EM-E1-BT18" /><input value={assetName} onChange={(event) => setAssetName(event.target.value)} placeholder="Descripción del activo" /><select value={assetLineId} onChange={(event) => setAssetLineId(event.target.value)}><option value="">Área</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} · {line.name}</option>)}</select><button disabled={!assetName.trim() || !assetCode.trim() || !assetLineId} onClick={createAsset}>Agregar</button></div>
          {adminMessage && <div className="success-message"><CheckCircle2 size={18} />{adminMessage}</div>}
        </section>
      )}

      {error && <div className="error">{error}</div>}
      {reportMessage && <div className="success-message"><CheckCircle2 size={18} />{reportMessage}</div>}
      {loading ? <div className="loading-panel"><RefreshCw className="spin" size={20} />Consultando equipos con reportes...</div> : !equipmentGroups.length ? (
        <EmptyState title="No hubo equipos reportados" text={`No se registraron fallas para ${selectedDateLabel}. Escoge otro rango para consultar.`} />
      ) : (
        <section className="incident-equipment-grid" aria-label="Equipos con reportes">
          {equipmentGroups.map((group, index) => {
            const modes = Array.from(new Set(group.reports.map((report) => report.failure_mode_name)));
            return (
              <button className="incident-equipment-card" key={group.id} onClick={() => setSelectedEquipment(group)} style={{ animationDelay: `${Math.min(index * 55, 330)}ms` }}>
                <span className="incident-card-index">{String(index + 1).padStart(2, "0")}</span>
                <div className="incident-card-heading"><code>{group.code || "SIN CÓDIGO"}</code><h3>{group.name}</h3><p><MapPin size={14} />{equipmentLocation(group)}</p></div>
                <div className="incident-card-modes">{modes.slice(0, 3).map((mode) => <span key={mode}>{mode}</span>)}{modes.length > 3 && <span>+{modes.length - 3}</span>}</div>
                <div className="incident-card-stats"><span><strong>{group.reports.length}</strong> reporte{group.reports.length === 1 ? "" : "s"}</span><span><strong>{formatNumber(totalDowntime(group.reports))}</strong> min</span><span><strong>{formatNumber(totalFrequency(group.reports))}</strong> frecuencia</span></div>
                <div className="incident-card-open"><AlertTriangle size={16} />Ver detalle de fallas</div>
              </button>
            );
          })}
        </section>
      )}

      {selectedEquipment && (
        <div className="incident-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedEquipment(null); }}>
          <section className="incident-modal" role="dialog" aria-modal="true" aria-labelledby="incident-modal-title">
            <header className="incident-modal-header">
              <div><span className="eyebrow">Detalle del equipo · {selectedDateLabel}</span><code>{selectedEquipment.code || "SIN CÓDIGO"}</code><h2 id="incident-modal-title">{selectedEquipment.name}</h2><p><MapPin size={15} />{equipmentLocation(selectedEquipment)}</p></div>
              <button className="modal-close" aria-label="Cerrar detalle" onClick={() => setSelectedEquipment(null)}><X size={22} /></button>
            </header>
            <div className="incident-modal-summary"><span><strong>{selectedEquipment.reports.length}</strong> reportes</span><span><strong>{formatNumber(totalDowntime(selectedEquipment.reports))}</strong> minutos</span><span><strong>{formatNumber(totalFrequency(selectedEquipment.reports))}</strong> frecuencia</span></div>
            <div className="incident-report-list">
              {selectedEquipment.reports.map((report, index) => (
                <article className="incident-report-detail" key={report.id}>
                  <header><span>Reporte {String(index + 1).padStart(2, "0")}</span><strong>{report.failure_mode_name}</strong></header>
                  <div className="incident-damage-grid"><div><small>Qué se dañó</small><p>{report.damage_description}</p></div><div><small>Razón del daño</small><p>{report.reason_description}</p></div></div>
                  <footer><span>Turno <strong>{report.shift_name}</strong></span><span>Tiempo <strong>{formatNumber(report.downtime_minutes)} min</strong></span><span>Frecuencia <strong>{formatNumber(report.frequency)}</strong></span><span>Reportó <strong>{report.reported_by}</strong></span><ReportDeleteAction reportId={report.id} reportLabel={`reporte ${report.id} de ${report.equipment_name}`} canDelete={user.role === "admin"} onDelete={deleteReport} /></footer>
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function totalDowntime(reports: DailyReport[]) {
  return reports.reduce((total, report) => total + Number(report.downtime_minutes || 0), 0);
}

function totalFrequency(reports: DailyReport[]) {
  return reports.reduce((total, report) => total + Number(report.frequency || 0), 0);
}

function equipmentLocation(group: IncidentEquipmentGroup) {
  const area = group.areaCode ? `${group.areaCode} · ${group.areaName || "Área"}` : group.areaName;
  const lineSuffix = group.processCode?.split("-").slice(-1)[0];
  const line = lineSuffix ? `${lineSuffix} · ${group.processName || "Línea"}` : group.processName;
  return [area, line].filter(Boolean).join(" / ") || "Ubicación no clasificada";
}

function EquipmentCatalogPage({ user }: { user: User }) {
  const [items, setItems] = useState<Equipment[]>([]);
  const [lines, setLines] = useState<ProductionLine[]>([]);
  const [options, setOptions] = useState<any>({ areas: [], processes: [], criticalities: [], specialties: [], levels: [] });
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [lineId, setLineId] = useState("");
  const [filters, setFilters] = useState({ search: "", area_code: "", process_code: "", hierarchy_level: "", criticality: "", specialty: "", state: "all" });
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const pageSize = 100;

  useEffect(() => {
    Promise.all([
      api.request<ProductionLine[]>("/production-lines?include_inactive=false"),
      api.request<any>("/equipment/filter-options"),
    ]).then(([lineRows, filterOptions]) => { setLines(lineRows); setOptions(filterOptions); }).catch((err) => setError((err as Error).message));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => refresh(), 220);
    return () => window.clearTimeout(timer);
  }, [filters, page]);

  function refresh() {
    setLoading(true);
    setError("");
    api.request<Equipment[]>(`/equipment${queryString({
      include_inactive: true,
      active: filters.state === "all" ? "" : filters.state === "active",
      search: filters.search,
      area_code: filters.area_code,
      process_code: filters.process_code,
      hierarchy_level: filters.hierarchy_level,
      criticality: filters.criticality,
      specialty: filters.specialty,
      limit: pageSize,
      offset: page * pageSize,
    })}`).then(setItems).catch((err) => setError((err as Error).message)).finally(() => setLoading(false));
  }

  function setFilter(key: keyof typeof filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value, ...(key === "area_code" ? { process_code: "" } : {}) }));
    setPage(0);
  }

  async function create() {
    await api.request("/equipment", { method: "POST", body: JSON.stringify({ name, code, production_line_id: Number(lineId), is_active: true }) });
    setName("");
    setCode("");
    refresh();
  }
  async function rename(item: Equipment) {
    const next = window.prompt("Nuevo nombre del equipo", item.name);
    if (!next || !next.trim()) return;
    await api.request(`/equipment/${item.id}`, { method: "PATCH", body: JSON.stringify({ name: next.trim(), code: item.code, production_line_id: item.production_line_id, is_active: item.is_active }) });
    refresh();
  }
  async function toggle(item: Equipment) {
    await api.request(`/equipment/${item.id}/${item.is_active ? "deactivate" : "activate"}`, { method: "PATCH" });
    refresh();
  }
  const visibleProcesses = options.processes.filter((item: any) => !filters.area_code || item.area_code === filters.area_code);

  return (
    <div className="equipment-page">
      <PageTitle title="Catálogo taxonómico de equipos" subtitle="Explora la jerarquía completa de Planta Barranquilla por código, descripción y datos técnicos." />

      <section className="taxonomy-hero">
        <div><span className="eyebrow">Taxonomía de activos</span><h2><code>BA</code> identifica la planta; cada bloque siguiente profundiza la ubicación del activo.</h2></div>
        <div className="taxonomy-path"><span>BA<small>Planta</small></span><i>→</i><span>WF<small>Área</small></span><i>→</i><span>ZE<small>Proceso</small></span><i>→</i><span>MZ02<small>Equipo</small></span><i>→</i><span>TQ02<small>Componente</small></span></div>
      </section>

      <section className="catalog-metrics">
        <div><strong>{formatNumber(options.total || 0)}</strong><span>Códigos únicos</span></div>
        <div><strong>{formatNumber(options.active || 0)}</strong><span>Registros habilitados</span></div>
        <div><strong>{formatNumber(options.reportable || 0)}</strong><span>Activos seleccionables</span></div>
        <div><strong>{formatNumber(options.areas?.length || 0)}</strong><span>Áreas de planta</span></div>
      </section>

      <section className="equipment-filter-panel">
        <label className="asset-search">Buscar coincidencias<input value={filters.search} onChange={(e) => setFilter("search", e.target.value)} placeholder="Código, descripción, marca, modelo, serial, ubicación o QR" /></label>
        <div className="equipment-filter-grid">
          <label>Área<select value={filters.area_code} onChange={(e) => setFilter("area_code", e.target.value)}><option value="">Todas las áreas</option>{options.areas.map((item: any) => <option key={item.code} value={item.code}>{item.code} · {item.name}</option>)}</select></label>
          <label>Proceso / Línea<select value={filters.process_code} onChange={(e) => setFilter("process_code", e.target.value)}><option value="">Todos los procesos</option>{visibleProcesses.map((item: any) => <option key={item.code} value={item.code}>{item.code} · {item.name}</option>)}</select></label>
          <label>Nivel<select value={filters.hierarchy_level} onChange={(e) => setFilter("hierarchy_level", e.target.value)}><option value="">Todos los niveles</option>{options.levels.map((item: any) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label>Criticidad<select value={filters.criticality} onChange={(e) => setFilter("criticality", e.target.value)}><option value="">Todas</option>{options.criticalities.map((item: string) => <option key={item}>{item}</option>)}</select></label>
          <label>Especialidad<select value={filters.specialty} onChange={(e) => setFilter("specialty", e.target.value)}><option value="">Todas</option>{options.specialties.map((item: string) => <option key={item}>{item}</option>)}</select></label>
          <label>Estado<select value={filters.state} onChange={(e) => setFilter("state", e.target.value)}><option value="all">Todos</option><option value="active">Habilitados</option><option value="inactive">Inhabilitados</option></select></label>
        </div>
      </section>

      {user.role === "admin" && (
        <section className="admin-catalog-card equipment-create-card">
          <div><span className="eyebrow">Solo administradores</span><h3>Agregar activo</h3><p>El código debe respetar el prefijo del área seleccionada.</p></div>
          <div className="inline-form"><input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="Código, ej. BA-EM-E1-BT18" /><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Descripción del activo" /><select value={lineId} onChange={(e) => setLineId(e.target.value)}><option value="">Área</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} · {line.name}</option>)}</select><button disabled={!name.trim() || !code.trim() || !lineId} onClick={create}>Agregar</button></div>
        </section>
      )}

      {error && <div className="error">{error}</div>}
      {loading ? <div className="loading-panel"><RefreshCw className="spin" size={20} />Buscando en el catálogo...</div> : !items.length ? <EmptyState title="Sin coincidencias" text="Prueba otra búsqueda o limpia uno de los filtros." /> : (
        <DataTable headers={["Código y activo", "Nivel", "Área / Proceso", "Datos técnicos", "Estado", "Acciones"]} rows={items.map((item) => [
          <div className="asset-identity"><code>{item.code || "SIN-CÓDIGO"}</code><strong>{item.name}</strong><small>{item.parent_code ? `Depende de ${item.parent_code}` : "Raíz de la taxonomía"}</small></div>,
          <span className="level-badge">{taxonomyLevelLabel(item.hierarchy_level)}</span>,
          <div className="asset-location"><strong>{item.area_name || item.plant_name || "—"}</strong><small>{item.process_name || "Sin proceso adicional"}</small></div>,
          <div className="asset-tech"><span>{[item.brand, item.model].filter(Boolean).join(" · ") || "Sin marca/modelo"}</span><small>{[item.specialty && `Esp. ${item.specialty}`, item.criticality && `Crit. ${item.criticality}`, item.location].filter(Boolean).join(" · ") || "Sin datos adicionales"}</small></div>,
          <span className={`pill ${item.is_active ? "good" : "danger"}`}>{item.is_active ? "Habilitado" : "Inhabilitado"}</span>,
          user.role === "admin" && item.production_line_id ? <ActionGroup><button onClick={() => rename(item)}>Renombrar</button><button onClick={() => toggle(item)}>{item.is_active ? "Desactivar" : "Activar"}</button></ActionGroup> : "—"
        ])} />
      )}

      <div className="catalog-pagination"><span>Mostrando {page * pageSize + (items.length ? 1 : 0)}–{page * pageSize + items.length}</span><div><button className="secondary" disabled={page === 0 || loading} onClick={() => setPage((value) => Math.max(0, value - 1))}>Anterior</button><button className="secondary" disabled={items.length < pageSize || loading} onClick={() => setPage((value) => value + 1)}>Siguiente</button></div></div>
    </div>
  );
}

function LinesPage({ user }: { user: User }) {
  const [items, setItems] = useState<ProductionLine[]>([]);
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  useEffect(() => { refresh(); }, []);
  function refresh(nextSearch = search) { api.request<ProductionLine[]>(`/production-lines${queryString({ include_inactive: true, search: nextSearch })}`).then(setItems); }
  async function create() {
    await api.request("/production-lines", { method: "POST", body: JSON.stringify({ name, is_active: true }) });
    setName("");
    refresh();
  }
  async function rename(item: ProductionLine) {
    const next = window.prompt("Nuevo nombre de la línea", item.name);
    if (!next || !next.trim()) return;
    await api.request(`/production-lines/${item.id}`, { method: "PATCH", body: JSON.stringify({ name: next.trim(), is_active: item.is_active }) });
    refresh();
  }
  async function toggle(item: ProductionLine) {
    await api.request(`/production-lines/${item.id}/${item.is_active ? "deactivate" : "activate"}`, { method: "PATCH" });
    refresh();
  }
  return (
    <Catalog
      title="Líneas"
      subtitle="Catálogo maestro de líneas de producción."
      user={user}
      name={name}
      setName={setName}
      create={create}
      search={search}
      onSearch={(value: string) => { setSearch(value); refresh(value); }}
      headers={["Línea", "Estado", "Acciones"]}
      rows={items.map((i) => [
        i.name,
        <span className={`pill ${i.is_active ? "good" : "danger"}`}>{i.is_active ? "Activa" : "Inactiva"}</span>,
        user.role === "admin" ? <ActionGroup><button onClick={() => rename(i)}>Renombrar</button><button onClick={() => toggle(i)}>{i.is_active ? "Desactivar" : "Activar"}</button></ActionGroup> : "-"
      ])}
    />
  );
}

function Catalog({ title, subtitle, user, name, setName, create, rows, headers, extra, canCreate = true, search = "", onSearch }: any) {
  return (
    <>
      <PageTitle title={title} subtitle={subtitle} />
      <div className="inline-form compact">
        <input placeholder="Buscar" value={search} onChange={(e) => onSearch?.(e.target.value)} />
      </div>
      {user.role === "admin" && (
        <div className="inline-form">
          <input placeholder="Nombre" value={name} onChange={(e) => setName(e.target.value)} />
          {extra}
          <button disabled={!name || !canCreate} onClick={create}>Crear</button>
        </div>
      )}
      <DataTable headers={headers} rows={rows} />
    </>
  );
}

function ReportsPage({ user }: { user: User }) {
  const [lines, setLines] = useState<ProductionLine[]>([]);
  const [catalogOptions, setCatalogOptions] = useState<CatalogFilterOptions>({ areas: [], processes: [] });
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [shifts, setShifts] = useState<ShiftOption[]>([]);
  const [failureModes, setFailureModes] = useState<FailureMode[]>([]);
  const [dailyReports, setDailyReports] = useState<DailyReport[]>([]);
  const [newFailureMode, setNewFailureMode] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);
  const todayIso = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const [reportDateFrom, setReportDateFrom] = useState(todayIso);
  const [reportDateTo, setReportDateTo] = useState(todayIso);
  const [form, setForm] = useState({
    event_date: todayIso,
    production_line_id: "",
    process_code: "",
    shift_id: "",
    equipment_id: "",
    failure_mode_id: "",
    damage_description: "",
    reason_description: "",
    downtime_minutes: "",
    frequency: "1",
  });

  const formDateLabel = formatDate(form.event_date);
  const selectedDateLabel = formatPeriod(reportDateFrom, reportDateTo);
  const availableEquipment = equipment.filter((item) => item.is_active);
  const selectedArea = lines.find((line) => String(line.id) === form.production_line_id);
  const availableProcesses = catalogOptions.processes.filter((process) => process.area_code === selectedArea?.code);
  const areaOptions: SearchOption[] = lines.map((line) => ({
    value: String(line.id),
    label: `${line.code || "S/C"} · ${line.name}`,
    searchText: `${line.code || ""} ${line.name}`,
  }));
  const processOptions: SearchOption[] = availableProcesses.map((process) => ({
    value: process.code,
    label: `${process.code.split("-").slice(-1)[0]} · ${process.name}`,
    searchText: `${process.code} ${process.name}`,
    meta: process.code,
  }));
  const equipmentOptions: SearchOption[] = availableEquipment.map((item) => ({
    value: String(item.id),
    label: `${item.code || "S/C"} · ${item.name}`,
    searchText: `${item.code || ""} ${item.name} ${item.brand || ""} ${item.model || ""} ${item.serial_number || ""}`,
    meta: item.process_name || undefined,
  }));
  const failureModeOptions: SearchOption[] = failureModes.map((mode) => ({ value: String(mode.id), label: mode.name }));

  useEffect(() => {
    Promise.all([
      api.request<ProductionLine[]>("/production-lines?include_inactive=false"),
      api.request<ShiftOption[]>("/shifts"),
      api.request<FailureMode[]>("/failure-modes?include_inactive=false"),
      api.request<CatalogFilterOptions>("/equipment/filter-options"),
    ]).then(([lineRows, shiftRows, modeRows, filterOptions]) => {
      setLines(lineRows);
      setShifts(shiftRows);
      setFailureModes(modeRows);
      setCatalogOptions(filterOptions);
    }).catch((err) => setError((err as Error).message));
  }, []);

  useEffect(() => { refreshReports(); }, []);

  useEffect(() => {
    if (!form.production_line_id || !form.process_code || !selectedArea?.code) {
      setEquipment([]);
      return;
    }
    api.request<Equipment[]>(`/equipment${queryString({ include_inactive: false, production_line_id: form.production_line_id, area_code: selectedArea.code, process_code: form.process_code, reportable: true, limit: 1200 })}`)
      .then(setEquipment)
      .catch((err) => setError((err as Error).message));
  }, [form.production_line_id, form.process_code, selectedArea?.code]);

  function setField(field: keyof typeof form, value: string) {
    setForm((current) => ({
      ...current,
      [field]: value,
      ...(field === "production_line_id" ? { process_code: "", equipment_id: "" } : {}),
      ...(field === "process_code" ? { equipment_id: "" } : {}),
    }));
  }

  async function refreshReports(dateFrom = reportDateFrom, dateTo = reportDateTo) {
    setLoadingReports(true);
    setError("");
    try {
      setDailyReports(await api.request<DailyReport[]>(`/daily-reports?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingReports(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await api.request<DailyReport>("/daily-reports", {
        method: "POST",
        body: JSON.stringify({
          event_date: form.event_date,
          production_line_id: Number(form.production_line_id),
          shift_id: Number(form.shift_id),
          equipment_id: Number(form.equipment_id),
          failure_mode_id: Number(form.failure_mode_id),
          damage_description: form.damage_description,
          reason_description: form.reason_description,
          downtime_minutes: Number(form.downtime_minutes),
          frequency: Number(form.frequency),
        }),
      });
      setForm((current) => ({ ...current, equipment_id: "", damage_description: "", reason_description: "", downtime_minutes: "", frequency: "1" }));
      setMessage("Reporte guardado y enviado al dashboard.");
      if (reportDateFrom === form.event_date && reportDateTo === form.event_date) await refreshReports(form.event_date, form.event_date);
      else {
        setReportDateFrom(form.event_date);
        setReportDateTo(form.event_date);
        await refreshReports(form.event_date, form.event_date);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function addFailureMode() {
    if (!newFailureMode.trim()) return;
    setError("");
    try {
      await api.request("/failure-modes", { method: "POST", body: JSON.stringify({ name: newFailureMode, is_active: true }) });
      setNewFailureMode("");
      setFailureModes(await api.request<FailureMode[]>("/failure-modes?include_inactive=false"));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function deleteReport(reportId: number) {
    setError("");
    setMessage("");
    await api.request<{ id: number; deleted: boolean }>(`/daily-reports/${reportId}`, { method: "DELETE" });
    await refreshReports();
    setMessage("Reporte eliminado correctamente.");
  }

  const ready = Object.values(form).every(Boolean) && Number(form.downtime_minutes) > 0 && Number(form.frequency) > 0;
  return (
    <>
      <PageTitle title="Reporte diario de falla" subtitle="Selecciona la fecha en que ocurrió la falla, aunque la estés registrando otro día." />

      <section className="report-hero">
        <div>
          <span className="eyebrow">Fecha de ocurrencia</span>
          <strong><CalendarDays size={22} />{formDateLabel}</strong>
          <p>El calendario inicia en hoy. Puedes escoger una fecha anterior si el reporte se registra después.</p>
        </div>
        <label className="report-event-date"><span>Fecha del reporte</span><input required type="date" max={todayIso} value={form.event_date} onChange={(e) => setField("event_date", e.target.value)} /></label>
      </section>

      <form className="daily-report-form" onSubmit={submit}>
        <div className="form-section-heading"><span>01</span><div><strong>Ubicación de la falla</strong><small>Área, turno y activo involucrado</small></div></div>
        <div className="report-field-grid three report-location-grid">
          <SearchableSelect required label="Área" placeholder="Escribe código o área" options={areaOptions} value={form.production_line_id} onChange={(value) => setField("production_line_id", value)} />
          <SearchableSelect required label="Línea" placeholder={form.production_line_id ? "Escribe E1 o nombre de línea" : "Primero selecciona el área"} options={processOptions} value={form.process_code} onChange={(value) => setField("process_code", value)} disabled={!form.production_line_id} emptyText="No hay líneas que coincidan en esta área" />
          <label>Turno<select required value={form.shift_id} onChange={(e) => setField("shift_id", e.target.value)}><option value="">Seleccionar turno</option>{shifts.map((shift) => <option key={shift.id} value={shift.id}>Turno {shift.name}</option>)}</select></label>
          <SearchableSelect required className="equipment-field" label="Activo / Equipo" placeholder={form.process_code ? "Escribe código, nombre, marca o modelo" : "Primero selecciona la línea"} options={equipmentOptions} value={form.equipment_id} onChange={(value) => setField("equipment_id", value)} disabled={!form.process_code} emptyText="No hay equipos que coincidan en esta línea" />
        </div>

        <div className="form-section-heading"><span>02</span><div><strong>Diagnóstico</strong><small>Clasificación y descripción de la falla</small></div></div>
        <div className="report-field-grid">
          <SearchableSelect required className="full" label="Modo de falla" placeholder="Escribe para buscar coincidencias" options={failureModeOptions} value={form.failure_mode_id} onChange={(value) => setField("failure_mode_id", value)} />
          <label>¿Qué fue lo que se dañó?<textarea required rows={4} value={form.damage_description} onChange={(e) => setField("damage_description", e.target.value)} placeholder="Ej. Rodamiento del motor principal" /></label>
          <label>Razón por la que se dañó<textarea required rows={4} value={form.reason_description} onChange={(e) => setField("reason_description", e.target.value)} placeholder="Ej. Falta de lubricación preventiva" /></label>
        </div>

        <div className="form-section-heading"><span>03</span><div><strong>Impacto operativo</strong><small>Tiempo de parada y recurrencia</small></div></div>
        <div className="report-field-grid compact-fields">
          <label>Tiempo para corregir (minutos)<input required type="number" min="0.1" max="1440" step="0.1" value={form.downtime_minutes} onChange={(e) => setField("downtime_minutes", e.target.value)} placeholder="0" /></label>
          <label>Frecuencia<input required type="number" min="1" max="1000" step="1" value={form.frequency} onChange={(e) => setField("frequency", e.target.value)} /></label>
        </div>

        {error && <div className="error">{error}</div>}
        {message && <div className="success-message"><CheckCircle2 size={18} />{message}</div>}
        <div className="report-submit"><button className="primary" disabled={!ready || saving}>{saving ? <RefreshCw size={18} className="spin" /> : <ClipboardCheck size={18} />}{saving ? "Guardando..." : "Guardar reporte"}</button></div>
      </form>

      {user.role === "admin" && (
        <section className="admin-catalog-card">
          <div><span className="eyebrow">Solo administradores</span><h3>Agregar modo de falla</h3><p>Los activos nuevos se administran desde el apartado Equipos.</p></div>
          <div className="inline-form"><input value={newFailureMode} onChange={(e) => setNewFailureMode(e.target.value)} placeholder="Nuevo modo de falla" /><button disabled={!newFailureMode.trim()} onClick={addFailureMode}>Agregar</button></div>
        </section>
      )}

      <PageTitle
        title={`Reportes registrados · ${selectedDateLabel}`}
        subtitle="Consulta todos los reportes registrados dentro de un rango de fechas, incluyendo ambas fechas."
        action={<ReportRangeControls className="report-date-control report-range-controls" dateFrom={reportDateFrom} dateTo={reportDateTo} maxDate={todayIso} loading={loadingReports} onDateFromChange={setReportDateFrom} onDateToChange={setReportDateTo} onApply={() => refreshReports()} />}
      />
      {loadingReports ? <div className="loading-panel"><RefreshCw className="spin" size={20} />Consultando reportes del rango...</div> : !dailyReports.length ? <EmptyState title="No hay reportes en este rango" text={`No se encontraron registros para ${selectedDateLabel}.`} /> : (
        <DataTable headers={["Área", "Línea", "Turno", "Activo", "Modo de falla", "Qué se dañó", "Razón", "Tiempo", "Frecuencia", "Reportó", "Acción"]} rows={dailyReports.map((row) => [row.area_code ? `${row.area_code} · ${row.area_name || row.line_name}` : row.line_name, row.process_code ? `${row.process_code.split("-").slice(-1)[0]} · ${row.process_name || row.process_code}` : "—", row.shift_name, row.equipment_name, <span className="pill warning">{row.failure_mode_name}</span>, row.damage_description, row.reason_description, `${formatNumber(row.downtime_minutes)} min`, formatNumber(row.frequency), row.reported_by, <ReportDeleteAction reportId={row.id} reportLabel={`reporte ${row.id} de ${row.equipment_name}`} canDelete={user.role === "admin"} onDelete={deleteReport} />])} />
      )}

    </>
  );
}

function ManagementReports() {
  const [reports, setReports] = useState<any[]>([]);
  const [options, setOptions] = useState<any>(null);
  const [filters, setFilters] = useState<FilterState>(emptyFilters);
  useEffect(() => { refresh(); api.request<any>("/dashboard/filters").then(setOptions); }, []);
  function refresh() { api.request<any[]>("/reports").then(setReports); }
  async function generate() {
    await api.request("/reports/management-pdf", { method: "POST", body: JSON.stringify(compactPayload({ date_from: filters.date_from, date_to: filters.date_to, production_line_id: filters.production_line_id ? Number(filters.production_line_id) : undefined, equipment_id: filters.equipment_id ? Number(filters.equipment_id) : undefined, shift_id: filters.shift_id ? Number(filters.shift_id) : undefined })) });
    refresh();
  }
  async function download(id: number, filename: string) {
    const response = await fetch(`${API_URL}/reports/${id}/download`, { headers: { Authorization: `Bearer ${api.token}` } });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="management-reports-page">
      <section className="management-report-hero">
        <div><span className="eyebrow">Acceso administrativo</span><h1>Reportes gerenciales</h1><p>Consolida la operación en documentos ejecutivos listos para descargar y compartir.</p></div>
        <div className="management-report-seal"><FileText size={34} /><span>PDF</span><small>Consolidado</small></div>
      </section>
      <PageTitle title="Exportación general" subtitle="Define los filtros y genera un PDF consolidado para administración." action={<button className="primary" onClick={generate}><FileDown size={18} />Generar PDF</button>} />
      <FilterBar filters={filters} setFilters={setFilters} options={options} onSubmit={(e) => e.preventDefault()} />
      <section className="management-report-history">
        <div><span className="eyebrow">Historial administrativo</span><h2>Exportaciones generadas</h2></div>
        {!reports.length ? <EmptyState title="Aún no hay exportaciones" text="El primer PDF generado aparecerá aquí para volver a descargarlo." /> : <DataTable headers={["Archivo", "Fecha", "Acción"]} rows={reports.map((row) => [row.file_path, new Date(row.created_at).toLocaleString(), <button className="text-button" onClick={() => download(row.id, row.file_path)}>Descargar</button>])} />}
      </section>
    </div>
  );
}

function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "plant_user" });
  useEffect(() => { refresh(); }, []);
  function refresh() { api.request<User[]>("/users").then(setUsers); }
  function setField(field: keyof typeof form, value: string) { setForm({ ...form, [field]: value }); }
  async function create(e: React.FormEvent) {
    e.preventDefault();
    await api.request("/users", { method: "POST", body: JSON.stringify(form) });
    setForm({ name: "", email: "", password: "", role: "plant_user" });
    refresh();
  }
  async function toggle(user: User) {
    await api.request(`/users/${user.id}/${user.is_active ? "deactivate" : "activate"}`, { method: "PATCH" });
    refresh();
  }
  async function changeRole(user: User, role: string) {
    await api.request(`/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ role }) });
    refresh();
  }
  return (
    <>
      <PageTitle title="Usuarios" subtitle="Administración básica de accesos y roles." />
      <form className="inline-form" onSubmit={create}>
        <input placeholder="Nombre" value={form.name} onChange={(e) => setField("name", e.target.value)} />
        <input placeholder="Email" value={form.email} onChange={(e) => setField("email", e.target.value)} />
        <input placeholder="Contraseña temporal" type="password" value={form.password} onChange={(e) => setField("password", e.target.value)} />
        <select value={form.role} onChange={(e) => setField("role", e.target.value)}>
          <option value="plant_user">Usuario planta</option>
          <option value="admin">Administrador</option>
        </select>
        <button disabled={!form.name || !form.email || !form.password}>Crear usuario</button>
      </form>
      <DataTable
        headers={["Nombre", "Email", "Rol", "Estado", "Acciones"]}
        rows={users.map((u) => [
          u.name,
          u.email,
          <select value={u.role} onChange={(e) => changeRole(u, e.target.value)}><option value="plant_user">Usuario planta</option><option value="admin">Administrador</option></select>,
          <span className={`pill ${u.is_active ? "good" : "danger"}`}>{u.is_active ? "Activo" : "Inactivo"}</span>,
          <ActionGroup><button onClick={() => toggle(u)}>{u.is_active ? "Desactivar" : "Activar"}</button></ActionGroup>
        ])}
      />
    </>
  );
}

function KpiGrid({ items }: { items: KpiItem[] }) {
  return (
    <section className="kpis">
      {items.map(([label, value, hint, tone = "neutral"]) => (
        <article key={label} className={`kpi ${tone}`}>
          <span>{label}</span>
          <strong>{value}</strong>
          {hint && <small>{hint}</small>}
        </article>
      ))}
    </section>
  );
}

function ChartGrid({ children }: { children: React.ReactNode }) {
  return <section className="chart-grid">{children}</section>;
}

function Chart({ title, data, type = "bar", color = "#254f55", horizontal = false, valueLabel = "Valor", unit = "" }: { title: string; data: any[]; type?: "bar" | "line"; color?: string; horizontal?: boolean; valueLabel?: string; unit?: string }) {
  return (
    <article className="chart">
      <h3>{title}</h3>
      <ResponsiveContainer height={280}>
        {type === "line" ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d9ded6" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line dataKey="downtime" stroke="#c98324" strokeWidth={3} dot={false} />
          </LineChart>
        ) : (
          <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={horizontal ? { left: 22, right: 18 } : undefined}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d9ded6" horizontal={!horizontal} vertical={horizontal} />
            {horizontal ? <>
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={132} tick={{ fontSize: 10 }} tickFormatter={truncateLabel} />
            </> : <>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
            </>}
            <Tooltip formatter={(value: any) => [`${formatNumber(value ?? 0)}${unit}`, valueLabel]} />
            <Bar dataKey="value" fill={color} radius={horizontal ? [0, 5, 5, 0] : [5, 5, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </article>
  );
}

function Pareto({ data }: { data: any[] }) {
  return (
    <article className="chart">
      <h3>Pareto de equipos</h3>
      <ResponsiveContainer height={280}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d9ded6" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="minutes" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="percent" orientation="right" domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value: any, name: any) => [name === "% acumulado" ? `${formatNumber(value ?? 0)}%` : `${formatNumber(value ?? 0)} min`, String(name)]} />
          <Legend />
          <Bar yAxisId="minutes" name="Tiempo perdido" dataKey="value" fill="#254f55" radius={[5, 5, 0, 0]} />
          <Line yAxisId="percent" name="% acumulado" dataKey="cumulative" stroke="#b45a2b" strokeWidth={3} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </article>
  );
}

function ScatterPanel({ data }: { data: any[] }) {
  return (
    <article className="chart">
      <h3>Tiempo vs frecuencia</h3>
      <ResponsiveContainer height={280}>
        <ScatterChart>
          <CartesianGrid stroke="#d9ded6" />
          <XAxis dataKey="frequency" name="Frecuencia" tick={{ fontSize: 11 }} />
          <YAxis dataKey="downtime" name="Tiempo" tick={{ fontSize: 11 }} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={data} fill="#b45a2b" />
        </ScatterChart>
      </ResponsiveContainer>
    </article>
  );
}

function DataTable({ headers, rows }: { headers: React.ReactNode[]; rows: React.ReactNode[][] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{headers.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
        <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

function ActionGroup({ children }: { children: React.ReactNode }) {
  return <div className="action-group">{children}</div>;
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <Clock3 size={24} />
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}

function taxonomyLevelLabel(level?: number | null) {
  const labels: Record<number, string> = {
    1: "Planta",
    2: "Área",
    3: "Proceso / Línea",
    4: "Equipo",
    5: "Sub-equipo / Componente",
  };
  return level ? labels[level] || `Nivel ${level}` : "Sin nivel";
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    uploaded: "Subida",
    validation_failed: "Validación fallida",
    pending_corrections: "Pendiente de corrección",
    ready_to_confirm: "Lista para confirmar",
    confirmed: "Confirmada",
    rejected: "Rechazada",
    valid: "Válido",
    warning: "Advertencia",
    pending_correction: "Pendiente"
  };
  return labels[status] || status;
}

function formatNumber(value: number | string) {
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 }).format(number) : value;
}

function formatDate(value: string) {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric" }).format(date);
}

function formatPeriod(from?: string, to?: string) {
  if (!from && !to) return "Sin datos para este alcance";
  if (from && from === to) return formatDate(from);
  return `${from ? formatDate(from) : "Inicio"} — ${to ? formatDate(to) : "Hoy"}`;
}

function shortDateLabel(value: string) {
  if (/^\d{4}-\d{2}$/.test(value)) {
    const [year, month] = value.split("-");
    return new Intl.DateTimeFormat("es-CO", { month: "short" }).format(new Date(Number(year), Number(month) - 1, 1));
  }
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short" }).format(date);
}

function formatChartDate(value: string) {
  if (/^\d{4}-\d{2}$/.test(value)) {
    const [year, month] = value.split("-");
    return new Intl.DateTimeFormat("es-CO", { month: "long", year: "numeric" }).format(new Date(Number(year), Number(month) - 1, 1));
  }
  return formatDate(value);
}

function truncateLabel(value: string) {
  return value.length > 22 ? `${value.slice(0, 21)}…` : value;
}

function queryString(filters: Record<string, string | number | boolean | undefined | null>) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value) !== "") params.set(key, String(value));
  });
  const text = params.toString();
  return text ? `?${text}` : "";
}

function compactPayload(payload: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== undefined && value !== null && value !== ""));
}

function initials(name: string) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

type PmpImportSummary = {
  id: number; total_rows: number; valid_rows: number; invalid_rows: number; approved_at?: string | null;
  reconciliation: { matches: boolean; expected: { global: { orders: number; planned_minutes: number } } };
  errors: PmpImportError[];
};

type LegacyPmpDashboardResponse = { metrics: { global: { orders: number; finalized_orders: number; pending_orders: number; planned_minutes: number; compliance_percent: number; compliant: boolean }; by_area: Record<string, { orders: number; pending_minutes: number; compliance_percent: number; compliant: boolean }>; alerts: { message: string }[] }; capacity: { area: string; shift: string; available_minutes: number; pending_minutes: number; gap_minutes: number; fte_required: number; alert: boolean }[] };

function LegacyPmpPage({ user }: { user: User }) {
  const [summary, setSummary] = useState<PmpImportSummary | null>(null);
  const [dashboard, setDashboard] = useState<LegacyPmpDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const weekStart = new Date().toISOString().slice(0, 10);

  async function refresh() {
    setLoading(true); setError("");
    try {
      const [importResult, dashboardResult] = await Promise.all([api.request<PmpImportSummary | null>("/pmp/imports/latest"), api.request<LegacyPmpDashboardResponse>(`/pmp/dashboard?week_start=${weekStart}`)]);
      setSummary(importResult); setDashboard(dashboardResult);
    } catch (err) { setError((err as Error).message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, []);
  async function executeImport() { setBusy(true); try { setSummary(await api.request<PmpImportSummary>("/pmp/imports/jose", { method: "POST" })); await refresh(); } catch (err) { setError((err as Error).message); } finally { setBusy(false); } }
  async function approve() { if (!summary) return; setBusy(true); try { setSummary(await api.request<PmpImportSummary>(`/pmp/imports/${summary.id}/approve`, { method: "POST" })); await refresh(); } catch (err) { setError((err as Error).message); } finally { setBusy(false); } }
  const metrics = dashboard?.metrics.global;
  return <section className="page-content">
    <PageTitle title="Plan de Mantenimiento Preventivo" subtitle="Carga controlada de JOSE.xlsx, reconciliación y capacidad por área." action={<div className="actions"><button className="secondary" onClick={refresh}><RefreshCw size={16} />Actualizar</button>{user.role === "admin" && <button className="primary" disabled={busy} onClick={executeImport}><UploadCloud size={16} />{busy ? "Procesando..." : "Cargar JOSE.xlsx"}</button>}</div>} />
    {error && <div className="error-banner">{error}</div>}
    {loading ? <div className="loading-panel"><RefreshCw className="spin" />Cargando indicadores PMP...</div> : <>
      {!summary ? <EmptyState title="Carga inicial pendiente" text="Un administrador debe ejecutar la carga obligatoria de JOSE.xlsx antes de validar el PMP." /> : <section className="kpi-grid">
        <article className="kpi"><span>Filas fuente</span><strong>{formatNumber(summary.total_rows)}</strong><small>{formatNumber(summary.valid_rows)} válidas · {formatNumber(summary.invalid_rows)} diagnósticos</small></article>
        <article className="kpi"><span>Reconciliación</span><strong>{summary.reconciliation.matches ? "Sin diferencias" : "Con diferencias"}</strong><small>{summary.approved_at ? "Aprobada para cierre de Fase 1" : "Pendiente de aprobación explícita"}</small></article>
        <article className="kpi"><span>Cumplimiento</span><strong>{metrics ? `${metrics.compliance_percent}%` : "—"}</strong><small className={metrics?.compliant ? "good" : "danger"}>{metrics?.compliant ? "Meta >90% cumplida" : "Meta >90% no cumplida"}</small></article>
        <article className="kpi"><span>Horas planeadas</span><strong>{metrics ? formatNumber(metrics.planned_minutes / 60) : "—"}</strong><small>Horas-hombre desde TiempoPlaneado</small></article>
      </section>}
      {summary && user.role === "admin" && summary.reconciliation.matches && !summary.approved_at && <button className="primary" disabled={busy} onClick={approve}><CheckCircle2 size={16} />Aprobar reconciliación de Fase 1</button>}
      {dashboard && <section className="content-grid two"><article className="panel"><h2>Avance por especialidad</h2><DataTable headers={["Área", "Órdenes", "Pendientes", "Cumplimiento"]} rows={Object.entries(dashboard.metrics.by_area).map(([area, value]) => [area, formatNumber(value.orders), `${formatNumber(value.pending_minutes / 60)} h`, <span className={value.compliant ? "pill success" : "pill warning"}>{value.compliance_percent}%</span>])} /></article><article className="panel"><h2>Capacidad y brechas</h2>{dashboard.capacity.length ? <DataTable headers={["Área", "Turno", "Capacidad", "Brecha", "FTE"]} rows={dashboard.capacity.map((row) => [row.area, row.shift, `${formatNumber(row.available_minutes / 60)} h`, `${formatNumber(row.gap_minutes / 60)} h`, row.fte_required])} /> : <p className="muted">Configure personal y programación semanal para calcular brechas por turno.</p>}</article></section>}
      {summary?.errors.length ? <section className="panel"><h2>Diagnósticos de importación</h2><DataTable headers={["Fila", "Campo", "Motivo"]} rows={summary.errors.slice(0, 20).map((item) => [item.row_number, item.field_name, item.message])} /></section> : null}
    </>}
  </section>;
}

function PmpPage({ user }: { user: User }) {
  const [summary, setSummary] = useState<PmpImportSummary | null>(null);
  const [dashboard, setDashboard] = useState<PmpDashboardResponse | null>(null);
  const [orders, setOrders] = useState<PmpOrdersResponse | null>(null);
  const [areas, setAreas] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [filters, setFilters] = useState<PmpFilters>(() => {
    try { return { area: "", status: "", as_of_date: "", shift: "", unit: "hours", ...JSON.parse(localStorage.getItem("pmp-dashboard-filters") || "{}") }; }
    catch { return { area: "", status: "", as_of_date: "", shift: "", unit: "hours" }; }
  });
  const [orderOffset, setOrderOffset] = useState(0);

  useEffect(() => { localStorage.setItem("pmp-dashboard-filters", JSON.stringify(filters)); }, [filters]);
  async function refresh(offset = orderOffset) {
    setLoading(true); setError("");
    try {
      const params = queryString({ area: filters.area, status: filters.status, as_of_date: filters.as_of_date, shift: filters.shift });
      const [importResult, dashboardResult, ordersResult, areaResult] = await Promise.all([
        api.request<PmpImportSummary | null>("/pmp/imports/latest"),
        api.request<PmpDashboardResponse>(`/pmp/dashboard${params}`),
        api.request<PmpOrdersResponse>(`/pmp/orders${queryString({ area: filters.area, status: filters.status, as_of_date: filters.as_of_date, offset, limit: 30 })}`),
        api.request<{ name: string }[]>("/pmp/areas"),
      ]);
      setSummary(importResult); setDashboard(dashboardResult); setOrders(ordersResult); setAreas(areaResult.map((area) => area.name)); setOrderOffset(offset);
    } catch (err) { setError((err as Error).message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(0); }, [filters.area, filters.status, filters.as_of_date, filters.shift]);
  async function executeImport() { setBusy(true); try { setSummary(await api.request<PmpImportSummary>("/pmp/imports/jose", { method: "POST" })); await refresh(); } catch (err) { setError((err as Error).message); } finally { setBusy(false); } }
  async function approve() { if (!summary) return; setBusy(true); try { setSummary(await api.request<PmpImportSummary>(`/pmp/imports/${summary.id}/approve`, { method: "POST" })); await refresh(); } catch (err) { setError((err as Error).message); } finally { setBusy(false); } }

  return <section className="page-content pmp-page">
    <PageTitle title="Plan de Mantenimiento Preventivo" subtitle="Cumplimiento, carga pendiente y capacidad verificable por área." action={<div className="actions"><button className="secondary" onClick={() => refresh()}><RefreshCw size={16} />Actualizar</button>{user.role === "admin" && <button className="primary" disabled={busy} onClick={executeImport}><UploadCloud size={16} />{busy ? "Procesando..." : "Cargar JOSE.xlsx"}</button>}</div>} />
    {error && <div className="error-banner">{error}</div>}
    {loading ? <div className="loading-panel"><RefreshCw className="spin" />Cargando indicadores PMP...</div> : <>
      {!summary ? <EmptyState title="Carga inicial pendiente" text="Un administrador debe ejecutar la carga obligatoria de JOSE.xlsx antes de validar el PMP." /> : <section className="pmp-import-strip"><span><Database size={16} />{formatNumber(summary.total_rows)} filas fuente</span><span>{formatNumber(summary.valid_rows)} válidas · {formatNumber(summary.invalid_rows)} diagnósticos</span><span className={summary.reconciliation.matches ? "good" : "danger"}>{summary.reconciliation.matches ? "Reconciliación sin diferencias" : "Reconciliación con diferencias"}</span>{summary.approved_at && <span className="good">Fase 1 aprobada</span>}</section>}
      {summary && user.role === "admin" && summary.reconciliation.matches && !summary.approved_at && <button className="primary" disabled={busy} onClick={approve}><CheckCircle2 size={16} />Aprobar reconciliación de Fase 1</button>}
      {dashboard && orders && <PmpDashboard dashboard={dashboard} orders={orders} errors={summary?.errors || []} areas={areas} filters={filters} onFiltersChange={setFilters} onOrderPage={(offset) => refresh(offset)} />}
    </>}
  </section>;
}

createRoot(document.getElementById("root")!).render(<App />);
