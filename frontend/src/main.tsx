import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Database,
  FileDown,
  FileSpreadsheet,
  Factory,
  Gauge,
  Home,
  LogOut,
  ShieldCheck,
  UploadCloud,
  Users,
  Wrench
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
import "./styles.css";

type View = "home" | "upload" | "loads" | "corrections" | "dashboard" | "quality" | "equipment" | "lines" | "reports" | "users";
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
  ["upload", UploadCloud, "Cargar archivo", "Excel diario"],
  ["loads", FileSpreadsheet, "Cargas", "Versiones"],
  ["corrections", ClipboardCheck, "Correcciones", "Pendientes"],
  ["dashboard", BarChart3, "Dashboard", "Gerencia"],
  ["quality", Gauge, "Calidad", "Dato"],
  ["equipment", Wrench, "Equipos", "Catálogo"],
  ["lines", Factory, "Líneas", "Producción"],
  ["reports", FileDown, "Reportes", "PDF"],
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
          <div className="brand-mark"><Factory size={24} /></div>
          <div>
            <strong>Mantto Control</strong>
            <span>Planta industrial</span>
          </div>
        </div>

        <nav className="side-nav" aria-label="Navegación principal">
          {nav.map(([id, Icon, label, meta]) => {
            if ((id === "reports" || id === "users") && user.role !== "admin") return null;
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
          <button onClick={() => { api.logout(); setUser(null); }}><LogOut size={16} />Salir</button>
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
        {view === "upload" && <UploadPage />}
        {view === "loads" && <LoadsPage />}
        {view === "corrections" && <CorrectionsPage />}
        {view === "dashboard" && <DashboardPage />}
        {view === "quality" && <QualityPage />}
        {view === "equipment" && <EquipmentPage user={user} />}
        {view === "lines" && <LinesPage user={user} />}
        {view === "reports" && <ReportsPage />}
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
        <div className="brand-mark large"><Factory size={34} /></div>
        <span className="eyebrow">MVP interno</span>
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

function HomePage({ setView }: { setView: (v: View) => void }) {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [dash, setDash] = useState<any>(null);
  const [quality, setQuality] = useState<any>(null);

  useEffect(() => {
    api.request<Upload[]>("/uploads").then(setUploads);
    api.request<any>("/dashboard/summary").then(setDash);
    api.request<any>("/data-quality/summary").then(setQuality);
  }, []);

  const last = uploads[0];
  const kpis = dash?.kpis;

  return (
    <>
      <PageTitle
        title="Centro de control"
        subtitle="Estado operativo de cargas, calidad y tiempo perdido validado."
        action={<button className="primary" onClick={() => setView("upload")}><UploadCloud size={18} />Nueva carga</button>}
      />
      <section className="command-panel">
        <div>
          <span className="eyebrow">Última carga</span>
          <h2>{last?.original_filename || "Sin cargas registradas"}</h2>
          <p>{last ? `${statusLabel(last.status)} · ${last.total_rows} filas leídas · ${last.valid_rows} confirmadas` : "Sube el primer archivo histórico para activar los indicadores."}</p>
        </div>
        <div className="command-strip">
          <span><CheckCircle2 size={18} />{quality?.pending_uploads ?? 0} cargas pendientes</span>
          <span><AlertTriangle size={18} />{quality?.open_errors ?? 0} errores abiertos</span>
          <span><Activity size={18} />{formatNumber(kpis?.total_events ?? 0)} eventos validados</span>
        </div>
      </section>
      <KpiGrid items={[
        ["Tiempo perdido", `${formatNumber(kpis?.total_minutes ?? 0)} min`, `${kpis?.total_hours ?? 0} horas`, "danger"],
        ["Equipo crítico", kpis?.critical_equipment ?? "Sin datos", "Mayor impacto por tiempo", "warn"],
        ["Calidad del dato", `${quality?.data_quality_percent ?? 100}%`, "Sobre cargas activas", "good"],
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
  useEffect(() => {
    api.request<any>("/dashboard/filters").then(setOptions);
    loadDashboard(filters);
  }, []);
  function loadDashboard(nextFilters: FilterState) {
    api.request<any>(`/dashboard/summary${queryString(nextFilters)}`).then(setData);
  }
  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    loadDashboard(filters);
  }
  if (!data) return <PageTitle title="Dashboard" subtitle="Cargando indicadores validados..." />;

  return (
    <>
      <PageTitle title="Dashboard gerencial" subtitle="Tiempo perdido vs frecuencia con datos confirmados." />
      <FilterBar filters={filters} setFilters={setFilters} options={options} onSubmit={applyFilters} />
      <KpiGrid items={[
        ["Tiempo perdido", `${formatNumber(data.kpis.total_minutes)} min`, `${data.kpis.total_hours} horas`, "danger"],
        ["Fallas/paradas", formatNumber(data.kpis.total_events), "Registros confirmados", "neutral"],
        ["Frecuencia total", formatNumber(data.kpis.total_frequency), "Ocurrencias", "neutral"],
        ["Equipo crítico", data.kpis.critical_equipment, "Mayor tiempo perdido", "warn"],
        ["Línea crítica", data.kpis.critical_line, "Mayor impacto", "warn"],
        ["Registros validados", formatNumber(data.kpis.validated_records), "Solo clean data", "good"],
      ]} />
      <ChartGrid>
        <Chart title="Tiempo perdido por mes" data={data.downtime_by_month} type="line" />
        <Pareto data={data.pareto} />
        <Chart title="Top 10 equipos por tiempo" data={data.top_equipment_downtime} />
        <Chart title="Top 10 equipos por frecuencia" data={data.top_equipment_frequency} color="#b45a2b" />
        <ScatterPanel data={data.downtime_vs_frequency} />
        <Chart title="Distribución por turno" data={data.by_shift} color="#596b4f" />
        <Chart title="Top daños por tiempo" data={data.top_damages} />
        <Chart title="Top razones por tiempo" data={data.top_reasons} />
      </ChartGrid>
    </>
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

function FilterBar({ filters, setFilters, options, onSubmit }: { filters: FilterState; setFilters: (filters: FilterState) => void; options: any; onSubmit: (e: React.FormEvent) => void }) {
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
      <button type="button" className="secondary" onClick={() => setFilters(emptyFilters)}>Limpiar</button>
    </form>
  );
}

function EquipmentPage({ user }: { user: User }) {
  const [items, setItems] = useState<Equipment[]>([]);
  const [lines, setLines] = useState<ProductionLine[]>([]);
  const [name, setName] = useState("");
  const [lineId, setLineId] = useState("");
  const [search, setSearch] = useState("");
  useEffect(() => { refresh(); api.request<ProductionLine[]>("/production-lines?include_inactive=true").then(setLines); }, []);
  function refresh(nextSearch = search) { api.request<Equipment[]>(`/equipment${queryString({ include_inactive: true, search: nextSearch })}`).then(setItems); }
  async function create() {
    await api.request("/equipment", { method: "POST", body: JSON.stringify({ name, production_line_id: Number(lineId), is_active: true }) });
    setName("");
    refresh();
  }
  async function rename(item: Equipment) {
    const next = window.prompt("Nuevo nombre del equipo", item.name);
    if (!next || !next.trim()) return;
    await api.request(`/equipment/${item.id}`, { method: "PATCH", body: JSON.stringify({ name: next.trim(), production_line_id: item.production_line_id, is_active: item.is_active }) });
    refresh();
  }
  async function toggle(item: Equipment) {
    await api.request(`/equipment/${item.id}/${item.is_active ? "deactivate" : "activate"}`, { method: "PATCH" });
    refresh();
  }
  return (
    <Catalog
      title="Equipos"
      subtitle="Catálogo maestro: cada equipo pertenece a una sola línea."
      user={user}
      name={name}
      setName={setName}
      canCreate={!!lineId}
      create={create}
      search={search}
      onSearch={(value: string) => { setSearch(value); refresh(value); }}
      extra={<select value={lineId} onChange={(e) => setLineId(e.target.value)}><option value="">Línea</option>{lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}</select>}
      headers={["Equipo", "Línea", "Estado", "Acciones"]}
      rows={items.map((i) => [
        i.name,
        lines.find((l) => l.id === i.production_line_id)?.name || "-",
        <span className={`pill ${i.is_active ? "good" : "danger"}`}>{i.is_active ? "Activo" : "Inactivo"}</span>,
        user.role === "admin" ? <ActionGroup><button onClick={() => rename(i)}>Renombrar</button><button onClick={() => toggle(i)}>{i.is_active ? "Desactivar" : "Activar"}</button></ActionGroup> : "-"
      ])}
    />
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

function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [options, setOptions] = useState<any>(null);
  const [filters, setFilters] = useState<FilterState>(emptyFilters);
  useEffect(() => { refresh(); api.request<any>("/dashboard/filters").then(setOptions); }, []);
  function refresh() { api.request<any[]>("/reports").then(setReports); }
  async function generate() {
    await api.request("/reports/management-pdf", {
      method: "POST",
      body: JSON.stringify(compactPayload({
        date_from: filters.date_from,
        date_to: filters.date_to,
        production_line_id: filters.production_line_id ? Number(filters.production_line_id) : undefined,
        equipment_id: filters.equipment_id ? Number(filters.equipment_id) : undefined,
        shift_id: filters.shift_id ? Number(filters.shift_id) : undefined,
      }))
    });
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
    <>
      <PageTitle title="Reportes" subtitle="PDF gerencial disponible solo para administradores." action={<button className="primary" onClick={generate}><FileDown size={18} />Generar PDF</button>} />
      <FilterBar filters={filters} setFilters={setFilters} options={options} onSubmit={(e) => e.preventDefault()} />
      {!reports.length ? <EmptyState title="Sin reportes" text="Genera el primer PDF gerencial desde datos confirmados." /> : (
        <DataTable
          headers={["Archivo", "Fecha", "Acción"]}
          rows={reports.map((r) => [r.file_path, new Date(r.created_at).toLocaleString(), <button className="text-button" onClick={() => download(r.id, r.file_path)}>Descargar</button>])}
        />
      )}
    </>
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

function Chart({ title, data, type = "bar", color = "#254f55" }: { title: string; data: any[]; type?: "bar" | "line"; color?: string }) {
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
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d9ded6" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" fill={color} radius={[5, 5, 0, 0]} />
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
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#254f55" radius={[5, 5, 0, 0]} />
          <Line dataKey="cumulative" stroke="#b45a2b" strokeWidth={3} />
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
  return Number.isFinite(number) ? new Intl.NumberFormat("es-CO").format(number) : value;
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

createRoot(document.getElementById("root")!).render(<App />);
