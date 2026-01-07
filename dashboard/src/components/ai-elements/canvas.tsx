import { ReactFlow, type ReactFlowProps } from "@xyflow/react";
import type { ReactNode } from "react";
import "@xyflow/react/dist/style.css";

type CanvasProps = ReactFlowProps & {
  children?: ReactNode;
};

/**
 * Base canvas component for React Flow visualizations.
 *
 * Defaults are optimized for interactive canvases (selection enabled).
 * For read-only canvases, override with selectionOnDrag={false} and
 * elementsSelectable={false}.
 */
export const Canvas = ({ children, ...props }: CanvasProps) => (
  <ReactFlow
    deleteKeyCode={["Backspace", "Delete"]}
    fitView
    panOnDrag={false}
    panOnScroll
    selectionOnDrag={true}
    zoomOnDoubleClick={false}
    style={{ background: "var(--sidebar)" }}
    {...props}
  >
    {children}
  </ReactFlow>
);
