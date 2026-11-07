export interface Viewer3D {
  addModel: (data: string, format: string) => void;
  setStyle: (sel: Record<string, unknown>, style: Record<string, unknown>) => void;
  addStyle: (sel: Record<string, unknown>, style: Record<string, unknown>) => void;
  addSurface: (type: number, opts: Record<string, unknown>) => void;
  addLine: (spec: Record<string, unknown>) => void;
  clear: () => void;
  zoomTo: (sel?: Record<string, unknown>) => void;
  render: () => void;
  spin: (spinning: boolean) => void;
  removeAllModels?: () => void;
  removeAllShapes?: () => void;
}

declare global {
  interface Window {
    $3Dmol?: {
      createViewer: (element: HTMLElement, config?: Record<string, unknown>) => Viewer3D;
    };
  }
}

