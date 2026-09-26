import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaQuestionCircle, FaComments, FaCheckCircle, FaUsers, FaMedal } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import StatCard from "../components/StatCard";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import "../styles/dashboard.css";

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [levels, setLevels] = useState([]);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/dashboard/summary"),
      api.get("/gamification/levels"),
      api.get("/gamification/my-badges"),
    ])
      .then(([summaryRes, levelsRes, badgesRes]) => {
        setSummary(summaryRes.data);
        setLevels(levelsRes.data);
        setBadges(badgesRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading || !summary) {
    return (
      <Layout title="Dashboard">
        <Loader label="Loading your dashboard..." />
      </Layout>
    );
  }

  const points = summary.Me.Points || 0;
  const currentIndex = levels.findIndex((l, i) => {
    const next = levels[i + 1];
    return points >= l.MinPoints && (!next || points < next.MinPoints);
  });
  const current = levels[currentIndex] || { MinPoints: 0, Level: summary.Me.Level };
  const next = levels[currentIndex + 1];
  const progressPct = next
    ? Math.min(100, Math.round(((points - current.MinPoints) / (next.MinPoints - current.MinPoints)) * 100))
    : 100;

  return (
    <Layout title="Dashboard">
      <div className="welcome-banner">
        <div>
          <h2>Welcome, {summary.Me.FullName || user?.Username}</h2>
          <p>
            You've asked {summary.Me.QuestionsAsked} question{summary.Me.QuestionsAsked === 1 ? "" : "s"} and
            {" "}answered {summary.Me.AnswersPosted}, with {summary.Me.AcceptedAnswers} accepted. Keep it up.
          </p>
        </div>
        <div className="welcome-progress">
          <div className="level-name">{summary.Me.Level}</div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <span style={{ fontSize: 12.5, color: "rgba(255,255,255,0.85)" }}>
            {points} pts{next ? ` \u00b7 ${next.MinPoints - points} to ${next.Level}` : " \u00b7 top level"}
          </span>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard icon={<FaQuestionCircle />} label="Total questions" value={summary.Stats.TotalQuestions} />
        <StatCard icon={<FaComments />} label="Total answers" value={summary.Stats.TotalAnswers} />
        <StatCard icon={<FaCheckCircle />} label="Accepted answers" value={summary.Stats.AcceptedAnswers} />
        <StatCard icon={<FaUsers />} label="Team members" value={summary.Stats.TotalUsers} />
      </div>

      <div className="dashboard-columns">
        <div className="card section-card">
          <h3>Recent questions</h3>
          {summary.RecentQuestions.length === 0 ? (
            <p className="text-muted">Nothing posted yet. Be the first to ask something.</p>
          ) : (
            summary.RecentQuestions.map((q) => (
              <Link key={q.QuestionID} to={`/questions/${q.QuestionID}`} className="recent-question-row">
                <div>
                  <div className="rq-title">{q.Title}</div>
                  <div className="rq-meta">{q.CategoryName} &middot; by {q.AuthorName}</div>
                </div>
                <span className="text-faint" style={{ fontSize: 13 }}>{q.AnswersCount} answers</span>
              </Link>
            ))
          )}
          <div style={{ marginTop: 16 }}>
            <Link to="/questions" className="btn btn-secondary">Browse all questions</Link>
          </div>
        </div>

        <div>
          <div className="card section-card">
            <h3><FaMedal style={{ color: "var(--color-accent)", marginRight: 8 }} />Your badges</h3>
            {badges.length === 0 ? (
              <p className="text-muted" style={{ fontSize: 13.5 }}>
                No badges yet - ask or answer a question to earn your first one.
              </p>
            ) : (
              <div className="badge-strip">
                {badges.map((b) => (
                  <div key={b.BadgeID} className="badge-chip">
                    <FaMedal /> {b.Name}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
