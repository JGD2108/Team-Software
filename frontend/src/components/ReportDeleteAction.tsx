import { AlertTriangle, Trash2 } from "lucide-react";
import { useState } from "react";

type ReportDeleteActionProps = {
  reportId: number;
  reportLabel: string;
  canDelete: boolean;
  onDelete: (reportId: number) => Promise<void>;
};

export function ReportDeleteAction({ reportId, reportLabel, canDelete, onDelete }: ReportDeleteActionProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  if (!canDelete) return null;

  async function confirmDeletion() {
    setDeleting(true);
    setError("");
    try {
      await onDelete(reportId);
      setConfirming(false);
    } catch (err) {
      setError((err as Error).message || "No fue posible eliminar el reporte.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="report-delete-action">
      <button className="text-button danger-text" type="button" onClick={() => { setError(""); setConfirming(true); }}>
        <Trash2 size={15} />Eliminar
      </button>
      {confirming && (
        <div className="report-delete-confirmation" role="alertdialog" aria-modal="true" aria-label={`Confirmar eliminación de ${reportLabel}`}>
          <p><AlertTriangle size={16} />¿Eliminar este reporte? Esta acción no se puede deshacer.</p>
          <div>
            <button className="secondary" type="button" disabled={deleting} onClick={() => setConfirming(false)}>Cancelar</button>
            <button className="danger-button" type="button" disabled={deleting} onClick={confirmDeletion}>{deleting ? "Eliminando..." : "Confirmar eliminación"}</button>
          </div>
          {error && <span className="report-delete-error" role="alert">{error}</span>}
        </div>
      )}
    </div>
  );
}
