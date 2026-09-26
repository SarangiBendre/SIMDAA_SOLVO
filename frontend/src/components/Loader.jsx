export default function Loader({ label = "Loading..." }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "40px 0", color: "var(--color-text-muted)" }}>
      <span className="spinner" />
      {label}
    </div>
  );
}
