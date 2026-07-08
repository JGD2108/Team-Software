import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  BarChart3,
  ClipboardCheck,
  FileDown,
  FileSpreadsheet,
  Factory,
  Gauge,
  Home,
  LogOut,
  Settings,
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

const nav = [
  ["home", Home, "Inicio"],
  ["upload", UploadCloud, "Cargar archivo"],
  ["loads", FileSpreadsheet, "Cargas"],
  ["corrections", ClipboardCheck, "Correcciones"],
  ["dashboard", BarChart3, "Dashboard"],
  ["quality", Gauge, "Calidad"],
  ["equipment", Wrench, "Equipos"],
  ["lines", Factory, "Líneas"],
  ["reports", FileDown, "Reportes"],
  ["users", Users, "Usuarios"]
] as const;

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>("home");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.me().then(setUser).catch(() => null).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="boot">Cargando sistema...</div>;
  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><Factory size={28} /><div><strong>Mantto</strong><span>Control interno</span></div></div>
        <nav>
          {nav.map(([id, Icon, label]) => {
            if ((id === "reports" || id === "users") && user.role !== "admin") return null;
            return <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}><Icon size={18} />{label}</button>;
          })}
        </nav>
        <div className="account">
          <span>{user.name}</span>
          <small>{user.role === "admin" ? "Administrador" : "Usuario planta"}</small>
          <button onClick={() => { api.logout(); setUser(null); }}><LogOut size={16} />Salir</button>
        </div>
      </aside>
      <main>
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
      <form onSubmit={submit} className="login-card">
        <div className="mark"><Factory /></div>
        <h1>Mantenimiento Industrial</h1>
        <p>Control de cargas, validación y tablero gerencial.</p>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Contraseña<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary">Entrar</button>
        <small>Admin: admin@mantenimiento.local / Admin123!<br />Planta: planta@mantenimiento.local / Planta123!</small>
      </form>
    </div>
  );
}

function PageTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return <header className="page-title"><div><h1>{title}</h1><p>{subtitle}</p></div><Settings size={22} /></header>;
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
  return (
    <>
      <PageTitle title="Inicio" subtitle="Estado operativo de mantenimiento y calidad del dato." />
      <section className="hero-panel">
        <div><span>Última carga</span><strong>{last?.original_filename || "Sin cargas"}</strong><small>{last?.status || "Pendiente de operación"}</small></div>
        <button className="primary" onClick={() => setView("upload")}><UploadCloud size={18} />Cargar archivo</button>
      </section>
      <KpiGrid items={[
        ["Tiempo perdido mes", `${dash?.kpis?.total_minutes ?? 0} min`],
        ["Equipo crítico", dash?.kpis?.critical_equipment ?? "Sin datos"],
        ["Registros pendientes", `${quality?.open_errors ?? 0}`],
        ["Calidad del dato", `${quality?.data_quality_percent ?? 100}%`],
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
      <PageTitle title="Cargar archivo" subtitle="Suba el .xlsx diario para validarlo antes de confirmar." />
      <form className="upload-box" onSubmit={submit}>
        <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button className="primary"><UploadCloud size={18} />Validar Excel</button>
      </form>
      {error && <div className="error">{error}</div>}
      {result && <StatusBand upload={result} onConfirm={confirm} />}
      <PreviewTable rows={preview} />
    </>
  );
}

function StatusBand({ upload, onConfirm }: { upload: Upload; onConfirm: () => void }) {
  return <div className="status-band"><strong>{upload.status}</strong><span>{upload.total_rows} filas</span><span>{upload.error_rows} errores</span><span>{upload.warning_rows} advertencias</span>{upload.status === "ready_to_confirm" && <button onClick={onConfirm}>Confirmar carga</button>}</div>;
}

function PreviewTable({ rows }: { rows: any[] }) {
  if (!rows.length) return null;
  return <div className="table-wrap"><table><thead><tr>{["Fila","Fecha","Línea","Turno","Equipo","Daño","Razón","Tiempo","Frecuencia","Estado"].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map(r => <tr key={r.id} className={r.status}><td>{r.row_number}</td><td>{r.fecha}</td><td>{r.linea}</td><td>{r.turno}</td><td>{r.equipo}</td><td>{r.dano}</td><td>{r.razon}</td><td>{r.tiempo}</td><td>{r.frecuencia}</td><td>{r.status}</td></tr>)}</tbody></table></div>;
}

function LoadsPage() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  useEffect(() => { api.request<Upload[]>("/uploads").then(setUploads); }, []);
  return <><PageTitle title="Cargas" subtitle="Histórico de archivos, versiones y estados." /><UploadTable uploads={uploads} /></>;
}

function UploadTable({ uploads }: { uploads: Upload[] }) {
  return <div className="table-wrap"><table><thead><tr><th>Archivo</th><th>Estado</th><th>Filas</th><th>Válidas</th><th>Errores</th><th>Advertencias</th><th>Fecha</th></tr></thead><tbody>{uploads.map(u => <tr key={u.id}><td>{u.original_filename}</td><td><span className="pill">{u.status}</span></td><td>{u.total_rows}</td><td>{u.valid_rows}</td><td>{u.error_rows}</td><td>{u.warning_rows}</td><td>{new Date(u.uploaded_at).toLocaleString()}</td></tr>)}</tbody></table></div>;
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
      <PageTitle title="Correcciones pendientes" subtitle="El usuario corrige seleccionando equipos existentes; no crea catálogo." />
      <div className="table-wrap"><table><thead><tr><th>Fila</th><th>Línea</th><th>Equipo original</th><th>Daño</th><th>Corrección</th></tr></thead><tbody>{rows.map(r => <tr key={r.id}><td>{r.row_number}</td><td>{r.linea}</td><td>{r.equipo}</td><td>{r.dano}</td><td><select onChange={(e) => e.target.value && correct(r.id, e.target.value)}><option>Seleccionar equipo</option>{equipment.map(eq => <option key={eq.id} value={eq.id}>{eq.name}</option>)}</select></td></tr>)}</tbody></table></div>
    </>
  );
}

function DashboardPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => { api.request<any>("/dashboard/summary").then(setData); }, []);
  if (!data) return <PageTitle title="Dashboard" subtitle="Cargando indicadores..." />;
  return (
    <>
      <PageTitle title="Dashboard gerencial" subtitle="Tiempo perdido vs frecuencia con datos confirmados." />
      <KpiGrid items={[
        ["Tiempo perdido", `${data.kpis.total_minutes} min`],
        ["Horas perdidas", `${data.kpis.total_hours} h`],
        ["Fallas/paradas", data.kpis.total_events],
        ["Frecuencia total", data.kpis.total_frequency],
        ["Equipo crítico", data.kpis.critical_equipment],
        ["Línea crítica", data.kpis.critical_line],
      ]} />
      <ChartGrid>
        <Chart title="Tiempo perdido por mes" data={data.downtime_by_month} type="line" />
        <Chart title="Top equipos por tiempo" data={data.top_equipment_downtime} />
        <Chart title="Top equipos por frecuencia" data={data.top_equipment_frequency} />
        <Pareto data={data.pareto} />
        <ScatterPanel data={data.downtime_vs_frequency} />
        <Chart title="Distribución por turno" data={data.by_shift} />
        <Chart title="Top daños por tiempo" data={data.top_damages} />
        <Chart title="Top razones por tiempo" data={data.top_reasons} />
      </ChartGrid>
    </>
  );
}

function KpiGrid({ items }: { items: [string, any][] }) {
  return <section className="kpis">{items.map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>;
}

function ChartGrid({ children }: { children: React.ReactNode }) {
  return <section className="chart-grid">{children}</section>;
}

function Chart({ title, data, type = "bar" }: { title: string; data: any[]; type?: "bar" | "line" }) {
  return <article className="chart"><h3>{title}</h3><ResponsiveContainer height={260}>{type === "line" ? <LineChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Line dataKey="downtime" stroke="#ffb000" strokeWidth={3} /></LineChart> : <BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis /><Tooltip /><Bar dataKey="value" fill="#225e63" radius={[4,4,0,0]} /></BarChart>}</ResponsiveContainer></article>;
}

function Pareto({ data }: { data: any[] }) {
  return <article className="chart"><h3>Pareto de equipos</h3><ResponsiveContainer height={260}><ComposedChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis /><Tooltip /><Legend /><Bar dataKey="value" fill="#225e63" /><Line dataKey="cumulative" stroke="#c24e2d" strokeWidth={3} /></ComposedChart></ResponsiveContainer></article>;
}

function ScatterPanel({ data }: { data: any[] }) {
  return <article className="chart"><h3>Tiempo vs frecuencia</h3><ResponsiveContainer height={260}><ScatterChart><CartesianGrid /><XAxis dataKey="frequency" name="Frecuencia" /><YAxis dataKey="downtime" name="Tiempo" /><Tooltip cursor={{ strokeDasharray: "3 3" }} /><Scatter data={data} fill="#c24e2d" /></ScatterChart></ResponsiveContainer></article>;
}

function QualityPage() {
  const [q, setQ] = useState<any>(null);
  useEffect(() => { api.request<any>("/data-quality/summary").then(setQ); }, []);
  return <><PageTitle title="Calidad de datos" subtitle="Pendientes, advertencias y errores de captura." />{q && <><KpiGrid items={[["Archivos cargados", q.uploads],["Archivos pendientes", q.pending_uploads],["Errores abiertos", q.open_errors],["Advertencias", q.warnings],["Registros corregidos", q.corrected_records],["Calidad", `${q.data_quality_percent}%`]]} /><ChartGrid><Chart title="Errores por tipo" data={q.errors_by_type.map((x:any) => ({ name: x.type, value: x.count }))} /></ChartGrid></>}</>;
}

function EquipmentPage({ user }: { user: User }) {
  const [items, setItems] = useState<Equipment[]>([]);
  const [lines, setLines] = useState<ProductionLine[]>([]);
  const [name, setName] = useState("");
  const [lineId, setLineId] = useState("");
  useEffect(() => { refresh(); api.request<ProductionLine[]>("/production-lines").then(setLines); }, []);
  function refresh() { api.request<Equipment[]>("/equipment").then(setItems); }
  async function create() { await api.request("/equipment", { method: "POST", body: JSON.stringify({ name, production_line_id: Number(lineId), is_active: true }) }); setName(""); refresh(); }
  return <Catalog title="Equipos" subtitle="Un equipo pertenece a una sola línea." user={user} name={name} setName={setName} canCreate={!!lineId} create={create} extra={<select value={lineId} onChange={e => setLineId(e.target.value)}><option value="">Línea</option>{lines.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select>} rows={items.map(i => [i.name, lines.find(l => l.id === i.production_line_id)?.name || "-", i.is_active ? "Activo" : "Inactivo"])} />;
}

function LinesPage({ user }: { user: User }) {
  const [items, setItems] = useState<ProductionLine[]>([]);
  const [name, setName] = useState("");
  useEffect(() => { refresh(); }, []);
  function refresh() { api.request<ProductionLine[]>("/production-lines").then(setItems); }
  async function create() { await api.request("/production-lines", { method: "POST", body: JSON.stringify({ name, is_active: true }) }); setName(""); refresh(); }
  return <Catalog title="Líneas" subtitle="Catálogo maestro de líneas de producción." user={user} name={name} setName={setName} create={create} rows={items.map(i => [i.name, i.is_active ? "Activa" : "Inactiva"])} />;
}

function Catalog({ title, subtitle, user, name, setName, create, rows, extra, canCreate = true }: any) {
  return <><PageTitle title={title} subtitle={subtitle} />{user.role === "admin" && <div className="inline-form"><input placeholder="Nombre" value={name} onChange={(e) => setName(e.target.value)} />{extra}<button disabled={!name || !canCreate} onClick={create}>Crear</button></div>}<div className="table-wrap"><table><tbody>{rows.map((r: any[], idx: number) => <tr key={idx}>{r.map(c => <td key={c}>{c}</td>)}</tr>)}</tbody></table></div></>;
}

function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  useEffect(() => { refresh(); }, []);
  function refresh() { api.request<any[]>("/reports").then(setReports); }
  async function generate() { await api.request("/reports/management-pdf", { method: "POST", body: JSON.stringify({}) }); refresh(); }
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
  return <><PageTitle title="Reportes" subtitle="PDF gerencial disponible solo para administradores." /><button className="primary" onClick={generate}><FileDown size={18} />Generar PDF</button><div className="table-wrap"><table><tbody>{reports.map(r => <tr key={r.id}><td>{r.file_path}</td><td>{new Date(r.created_at).toLocaleString()}</td><td><button onClick={() => download(r.id, r.file_path)}>Descargar</button></td></tr>)}</tbody></table></div></>;
}

function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  useEffect(() => { api.request<User[]>("/users").then(setUsers); }, []);
  return <><PageTitle title="Usuarios" subtitle="Administración básica de accesos." /><div className="table-wrap"><table><thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Estado</th></tr></thead><tbody>{users.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.is_active ? "Activo" : "Inactivo"}</td></tr>)}</tbody></table></div></>;
}

createRoot(document.getElementById("root")!).render(<App />);
