import { CalendarDays, RefreshCw } from "lucide-react";
import { useState } from "react";

type ReportRangeControlsProps = {
  dateFrom: string;
  dateTo: string;
  maxDate: string;
  loading: boolean;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onApply: () => void;
  className?: string;
};

export function validateReportDateRange(dateFrom: string, dateTo: string): string | null {
  if (!dateFrom || !dateTo) return "Selecciona una fecha inicial y una fecha final.";
  if (dateFrom > dateTo) return "La fecha inicial no puede ser posterior a la fecha final.";
  return null;
}

export function ReportRangeControls({ dateFrom, dateTo, maxDate, loading, onDateFromChange, onDateToChange, onApply, className = "incident-date-actions" }: ReportRangeControlsProps) {
  const [validationError, setValidationError] = useState("");

  function applyRange() {
    const error = validateReportDateRange(dateFrom, dateTo);
    setValidationError(error || "");
    if (!error) onApply();
  }

  return (
    <div className={className}>
      <label><span><CalendarDays size={16} />Fecha inicial</span><input aria-label="Fecha inicial" type="date" max={maxDate} value={dateFrom} onChange={(event) => { setValidationError(""); onDateFromChange(event.target.value); }} /></label>
      <label><span><CalendarDays size={16} />Fecha final</span><input aria-label="Fecha final" type="date" max={maxDate} value={dateTo} onChange={(event) => { setValidationError(""); onDateToChange(event.target.value); }} /></label>
      <button className="secondary" type="button" disabled={loading} onClick={applyRange}><RefreshCw size={16} className={loading ? "spin" : ""} />Actualizar</button>
      {validationError && <span className="report-range-error" role="alert">{validationError}</span>}
    </div>
  );
}
