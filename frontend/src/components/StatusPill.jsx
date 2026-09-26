const MAP = {
  Open: "pill-open",
  Answered: "pill-answered",
  Closed: "pill-closed",
};

export default function StatusPill({ status }) {
  return <span className={`pill ${MAP[status] || "pill-open"}`}>{status}</span>;
}
