import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { ReportDeleteAction } from "./ReportDeleteAction";

describe("ReportDeleteAction", () => {
  it("shows Eliminar only when the current user can delete", () => {
    const onDelete = vi.fn();
    const { rerender } = render(<ReportDeleteAction reportId={12} reportLabel="reporte 12" canDelete={false} onDelete={onDelete} />);
    expect(screen.queryByRole("button", { name: "Eliminar" })).toBeNull();

    rerender(<ReportDeleteAction reportId={12} reportLabel="reporte 12" canDelete onDelete={onDelete} />);
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeTruthy();
  });

  it("requires confirmation and refreshes the report list after deletion", async () => {
    function ReportList() {
      const [reports, setReports] = useState([6]);
      const [message, setMessage] = useState("");
      async function removeReport(id: number) {
        setReports((current) => current.filter((reportId) => reportId !== id));
        setMessage("Reporte eliminado correctamente.");
      }
      return <><span>{message}</span>{reports.map((id) => <div key={id}>Reporte {id}<ReportDeleteAction reportId={id} reportLabel={`reporte ${id}`} canDelete onDelete={removeReport} /></div>)}</>;
    }

    render(<ReportList />);
    fireEvent.click(screen.getByRole("button", { name: "Eliminar" }));
    expect(screen.getByRole("alertdialog")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar eliminación" }));

    await waitFor(() => expect(screen.queryByText("Reporte 6")).toBeNull());
    expect(screen.getByText("Reporte eliminado correctamente.")).toBeTruthy();
  });

  it("shows the API error and keeps the report when deletion fails", async () => {
    const onDelete = vi.fn().mockRejectedValue(new Error("No autorizado"));
    render(<ReportDeleteAction reportId={6} reportLabel="reporte 6" canDelete onDelete={onDelete} />);

    fireEvent.click(screen.getByRole("button", { name: "Eliminar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar eliminación" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No autorizado");
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeTruthy();
  });
});
