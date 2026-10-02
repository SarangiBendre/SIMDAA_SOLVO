const MAP = {
  Open: "pill-open",
  Answered: "pill-answered",
};

export default function StatusPill({ status }) {
  return <span className={`pill ${MAP[status] || "pill-open"}`}>{status}</span>;
}
