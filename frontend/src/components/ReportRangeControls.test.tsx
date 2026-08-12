import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { ReportRangeControls, validateReportDateRange } from "./ReportRangeControls";

function RangeHarness({ onApply }: { onApply: () => void }) {
  const [dateFrom, setDateFrom] = useState("2026-08-10");
  const [dateTo, setDateTo] = useState("2026-08-12");
  return <ReportRangeControls dateFrom={dateFrom} dateTo={dateTo} maxDate="2026-08-12" loading={false} onDateFromChange={setDateFrom} onDateToChange={setDateTo} onApply={onApply} />;
}

describe("ReportRangeControls", () => {
  it("submits an inclusive selected range", () => {
    const onApply = vi.fn();
    render(<RangeHarness onApply={onApply} />);

    fireEvent.click(screen.getByRole("button", { name: "Actualizar" }));
    expect(onApply).toHaveBeenCalledTimes(1);
    expect(validateReportDateRange("2026-08-10", "2026-08-12")).toBeNull();
  });

  it("blocks reversed ranges with a visible validation error", () => {
    const onApply = vi.fn();
    render(<RangeHarness onApply={onApply} />);

    fireEvent.change(screen.getByLabelText("Fecha inicial"), { target: { value: "2026-08-12" } });
    fireEvent.change(screen.getByLabelText("Fecha final"), { target: { value: "2026-08-10" } });
    fireEvent.click(screen.getByRole("button", { name: "Actualizar" }));

    expect(screen.getByRole("alert").textContent).toContain("La fecha inicial no puede ser posterior a la fecha final.");
    expect(onApply).not.toHaveBeenCalled();
  });
});
