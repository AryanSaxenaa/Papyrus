import { useEffect, useRef } from "react";

export function GridCanvasBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0;
    let h = 0;
    let animId = 0;

    function resize() {
      const parent = canvas?.parentElement;
      if (!parent || !canvas) return;
      w = parent.clientWidth;
      h = parent.clientHeight;
      canvas.width = w;
      canvas.height = h;
    }

    resize();
    window.addEventListener("resize", resize);

    const fg: [number, number, number] = [65, 145, 108];
    const accent: [number, number, number] = [82, 183, 136];

    function rgbaStr(c: [number, number, number], a: number) {
      return `rgba(${c[0]},${c[1]},${c[2]},${a})`;
    }

    const chars = "0123456789ABCDEF";
    let start = performance.now();

    function draw(now: number) {
      if (!ctx || !canvas) return;
      const t = (now - start) / 1000;

      ctx.clearRect(0, 0, w, h);

      const cellSize = 32;
      const cols = Math.ceil(w / cellSize);
      const rows = Math.ceil(h / cellSize);
      const fontSize = Math.floor(cellSize * 0.45);
      ctx.font = `bold ${fontSize}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const x = c * cellSize + cellSize / 2;
          const y = r * cellSize + cellSize / 2;

          const phase = Math.floor(t * 2 + r * 0.5 + c * 0.3);
          const charIdx =
            ((phase + r * 7 + c * 13) % chars.length + chars.length) % chars.length;

          const wave = Math.sin(t * 1.5 + r * 0.4 + c * 0.3) * 0.5 + 0.5;
          const alpha = 0.08 + wave * 0.20;

          if (wave > 0.75) {
            ctx.fillStyle = rgbaStr(accent, (wave - 0.75) * 0.10);
            ctx.fillRect(
              c * cellSize + 1,
              r * cellSize + 1,
              cellSize - 2,
              cellSize - 2,
            );
          }

          ctx.fillStyle = rgbaStr(fg, alpha);
          ctx.fillText(chars[charIdx], x, y);
        }
      }

      ctx.strokeStyle = rgbaStr(fg, 0.05);
      ctx.lineWidth = 1;
      for (let r = 0; r <= rows; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * cellSize);
        ctx.lineTo(w, r * cellSize);
        ctx.stroke();
      }
      for (let c = 0; c <= cols; c++) {
        ctx.beginPath();
        ctx.moveTo(c * cellSize, 0);
        ctx.lineTo(c * cellSize, h);
        ctx.stroke();
      }

      animId = requestAnimationFrame(draw);
    }

    animId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 block h-full w-full opacity-50"
      aria-hidden
    />
  );
}
