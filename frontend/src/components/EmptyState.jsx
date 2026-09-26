export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="card" style={{ padding: "48px 32px", textAlign: "center", color: "var(--color-text-muted)" }}>
      {icon && <div style={{ fontSize: 34, color: "var(--color-text-faint)", marginBottom: 12 }}>{icon}</div>}
      <h3 style={{ marginBottom: 8, color: "var(--color-text)" }}>{title}</h3>
      {description && <p style={{ maxWidth: 420, margin: "0 auto 16px" }}>{description}</p>}
      {action}
    </div>
  );
}
