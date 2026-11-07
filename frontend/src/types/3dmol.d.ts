export interface Viewer3D {
  addModel: (data: string, format: string) => void;
  setStyle: (sel: Record<string, unknown>, style: Record<string, unknown>) => void;
  addSurface: (type: number, opts: Record<string, unknown>) => void;
  zoomTo: (sel?: Record<string, unknown>) => void;
  render: () => void;
  spin: (spinning: boolean) => void;
}

declare global {
  interface Window {
    $3Dmol?: {
      createViewer: (element: HTMLElement, config?: Record<string, unknown>) => Viewer3D;
    };
  }
}
