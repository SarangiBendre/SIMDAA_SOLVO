import { useEffect, useState } from "react";
import { FaMedal, FaTrophy } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import api from "../api/client";

const RANK_COLORS = ["#F5A623", "#94A3B8", "#B45309"];

function currentYearMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(ym) {
  const [year, month] = ym.split("-");
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleString(undefined, { month: "long", year: "numeric" });
}

export default function Leaderboard() {
  const [leaders, setLeaders] = useState([]);
  const [badges, setBadges] = useState([]);
  const [months, setMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(currentYearMonth());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/gamification/badges"),
      api.get("/gamification/leaderboard/months"),
    ]).then(([b, m]) => {
      setBadges(b.data);
      setMonths(m.data);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    const isCurrentMonth = selectedMonth === currentYearMonth();
    const request = isCurrentMonth
      ? api.get("/gamification/leaderboard", { params: { limit: 20 } })
      : api.get("/gamification/leaderboard/history", { params: { month: selectedMonth, limit: 20 } });

    request.then(({ data }) => setLeaders(data)).finally(() => setLoading(false));
  }, [selectedMonth]);

  const isCurrentMonth = selectedMonth === currentYearMonth();
  const monthOptions = months.includes(currentYearMonth())
    ? months
    : [currentYearMonth(), ...months];

  return (
    <Layout title="Leaderboard">
      <div className="dashboard-columns">
        <div className="card section-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}><FaTrophy style={{ color: "var(--color-accent)", marginRight: 8 }} />Top contributors</h3>
            <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)}>
              {monthOptions.map((ym) => (
                <option key={ym} value={ym}>
                  {monthLabel(ym)}{ym === currentYearMonth() ? " (current)" : ""}
                </option>
              ))}
            </select>
          </div>

          {!isCurrentMonth && (
            <p className="text-muted" style={{ fontSize: 13, marginTop: -8, marginBottom: 14 }}>
              Frozen standings for {monthLabel(selectedMonth)} - the live leaderboard resets to zero every month.
            </p>
          )}

          {loading ? (
            <Loader label="Loading leaderboard..." />
          ) : leaders.length === 0 ? (
            <p className="text-muted" style={{ fontSize: 13.5 }}>No points recorded for this month yet.</p>
          ) : (
            <div className="table-scroll">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  {isCurrentMonth && <th>Level</th>}
                  <th>Points</th>
                  {isCurrentMonth && <th>Badges</th>}
                </tr>
              </thead>
              <tbody>
                {leaders.map((u, i) => (
                  <tr key={u.UserID}>
                    <td style={{ color: RANK_COLORS[i] || "var(--color-text-faint)", fontWeight: 700 }}>{i + 1}</td>
                    <td>{u.FullName}</td>
                    {isCurrentMonth && <td><span className="pill pill-level">{u.Level}</span></td>}
                    <td>{u.Points}</td>
                    {isCurrentMonth && <td>{u.BadgeCount}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>

        <div className="card section-card">
          <h3>Badge catalog</h3>
          {badges.map((b) => (
            <div key={b.BadgeID} className="recent-question-row" style={{ padding: "10px 0" }}>
              <div>
                <div className="rq-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <FaMedal style={{ color: "var(--color-accent)" }} /> {b.Name}
                </div>
                <div className="rq-meta">{b.Description}</div>
              </div>
              <span className="text-faint" style={{ fontSize: 12 }}>{b.Criteria}</span>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
