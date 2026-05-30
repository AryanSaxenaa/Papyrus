export function MathGridBg() {
  return (
    <div
      className="pointer-events-none fixed inset-0 opacity-[0.07]"
      style={{
        backgroundImage:
          "linear-gradient(#40916c 1px, transparent 0), linear-gradient(90deg, #40916c 1px, transparent 0)",
        backgroundSize: "40px 40px",
      }}
      aria-hidden
    />
  );
}
