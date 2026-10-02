import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", gap: 12, textAlign: "center",
    }}>
      <h1 style={{ fontSize: 64, color: "var(--color-primary)" }}>404</h1>
      <p className="text-muted">This page doesn't exist.</p>
      <Link to="/dashboard" className="btn btn-primary">Back to dashboard</Link>
    </div>
  );
}
