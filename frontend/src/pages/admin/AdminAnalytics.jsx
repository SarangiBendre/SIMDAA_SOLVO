import { useEffect, useState } from "react";
import { FaUsers, FaQuestionCircle, FaExclamationTriangle, FaChartBar } from "react-icons/fa";
import Layout from "../../components/Layout";
import Loader from "../../components/Loader";
import StatCard from "../../components/StatCard";
import api from "../../api/client";
import "../../styles/admin.css";

export default function AdminAnalytics() {
  const [data, setData] = useState(null);
  const [unanswered, setUnanswered] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/admin/analytics"),
      api.get("/admin/reports/unanswered"),
    ])
      .then(([a, u]) => {
        setData(a.data);
        setUnanswered(u.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <Layout title="Analytics">
        <Loader label="Crunching numbers..." />
      </Layout>
    );
  }

  const maxCategoryCount = Math.max(1, ...data.QuestionsPerCategory.map((c) => c.Count));

  return (
    <Layout title="Analytics">
      <div className="admin-grid">
        <StatCard icon={<FaUsers />} label="Active users" value={`${data.ActiveUsers}/${data.TotalUsers}`} />
        <StatCard icon={<FaQuestionCircle />} label="Questions (last 30 days)" value={data.QuestionsLast30Days} />
        <StatCard icon={<FaExclamationTriangle />} label="Unanswered open questions" value={data.UnansweredOpenQuestions} />
      </div>

      <div className="dashboard-columns">
        <div className="card section-card">
          <h3><FaChartBar style={{ marginRight: 8, color: "var(--color-secondary)" }} />Questions per category</h3>
          {data.QuestionsPerCategory.map((c) => (
            <div key={c.Category} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, marginBottom: 4 }}>
                <span>{c.Category}</span>
                <span className="text-muted">{c.Count}</span>
              </div>
              <div className="progress-track" style={{ background: "var(--color-bg)" }}>
                <div
                  className="progress-fill"
                  style={{ width: `${(c.Count / maxCategoryCount) * 100}%`, background: "var(--color-secondary)" }}
                />
              </div>
            </div>
          ))}
        </div>

        <div>
          <div className="card section-card">
            <h3>Top askers</h3>
            {data.TopAskers.map((t) => (
              <div key={t.FullName} className="recent-question-row" style={{ padding: "8px 0" }}>
                <span>{t.FullName}</span>
                <span className="text-faint">{t.Count}</span>
              </div>
            ))}
          </div>
          <div className="card section-card">
            <h3>Top mentors</h3>
            {data.TopMentors.map((t) => (
              <div key={t.FullName} className="recent-question-row" style={{ padding: "8px 0" }}>
                <span>{t.FullName}</span>
                <span className="text-faint">{t.Count} accepted</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card section-card">
        <h3>Unanswered questions</h3>
        {unanswered.length === 0 ? (
          <p className="text-muted" style={{ fontSize: 13.5 }}>Nothing outstanding - great work team.</p>
        ) : (
          <div className="table-scroll">
          <table className="admin-table">
            <thead>
              <tr><th>Title</th><th>Author</th><th>Category</th><th>Days open</th></tr>
            </thead>
            <tbody>
              {unanswered.map((q) => (
                <tr key={q.QuestionID}>
                  <td>{q.Title}</td>
                  <td>{q.AuthorName}</td>
                  <td>{q.CategoryName}</td>
                  <td>{q.DaysOpen}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
