import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HandoffDialog } from "../HandoffDialog";
import type { BrainstormArtifact } from "@/types/api";

const mockArtifact: BrainstormArtifact = {
  id: "a1",
  session_id: "s1",
  type: "design",
  path: "docs/plans/2026-01-18-caching-design.md",
  title: "Caching Layer Design",
  created_at: "2026-01-18T10:00:00Z",
};

describe("HandoffDialog", () => {
  it("renders dialog when open", () => {
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText("Hand off to Implementation")).toBeInTheDocument();
  });

  it("pre-fills issue title from artifact title", () => {
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByLabelText(/issue title/i)).toHaveValue(
      "Implement Caching Layer Design"
    );
  });

  it("calls onConfirm with title when confirmed", async () => {
    const onConfirm = vi.fn();
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    await userEvent.click(
      screen.getByRole("button", { name: /create workflow/i })
    );

    expect(onConfirm).toHaveBeenCalledWith("Implement Caching Layer Design");
  });

  it("calls onConfirm with custom title", async () => {
    const onConfirm = vi.fn();
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    const input = screen.getByLabelText(/issue title/i);
    await userEvent.clear(input);
    await userEvent.type(input, "Custom Title");
    await userEvent.click(
      screen.getByRole("button", { name: /create workflow/i })
    );

    expect(onConfirm).toHaveBeenCalledWith("Custom Title");
  });

  it("calls onCancel when cancel button is clicked", async () => {
    const onCancel = vi.fn();
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });

  it("disables confirm when isLoading", () => {
    render(
      <HandoffDialog
        open={true}
        artifact={mockArtifact}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        isLoading={true}
      />
    );

    expect(
      screen.getByRole("button", { name: /creating/i })
    ).toBeDisabled();
  });
});
