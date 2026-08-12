export type User = { id: number; name: string; email: string; role: "admin" | "plant_user"; is_active: boolean };
export type Upload = { id: number; original_filename: string; file_hash: string; uploaded_at: string; status: string; total_rows: number; valid_rows: number; error_rows: number; warning_rows: number };
export type ProductionLine = { id: number; name: string; code?: string | null; is_active: boolean };
export type Equipment = {
  id: number;
  name: string;
  production_line_id: number | null;
  code?: string | null;
  parent_code?: string | null;
  hierarchy_level?: number | null;
  plant_code?: string | null;
  plant_name?: string | null;
  area_code?: string | null;
  area_name?: string | null;
  process_code?: string | null;
  process_name?: string | null;
  is_reportable: boolean;
  brand?: string | null;
  model?: string | null;
  serial_number?: string | null;
  location?: string | null;
  qr_code?: string | null;
  criticality?: string | null;
  specialty?: string | null;
  grouping?: string | null;
  analysis_group?: string | null;
  pdt_group?: string | null;
  source_status?: string | null;
  financial_code?: string | null;
  cost_center?: string | null;
  is_active: boolean;
};

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiClient {
  token = localStorage.getItem("token") || "";

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("token", token);
  }

  logout() {
    this.token = "";
    localStorage.removeItem("token");
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    const response = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
    }
    return response.json();
  }

  login(email: string, password: string) {
    return this.request<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
  }

  me() {
    return this.request<User>("/auth/me");
  }
}

export const api = new ApiClient();
