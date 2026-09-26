import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaRobot, FaCheckCircle, FaUser } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import MarkdownContent from "../components/MarkdownContent";
import api, { attachmentUrl } from "../api/client";
import { formatDateTime } from "../utils/date";

export default function AIReviewQueue() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acceptingId, setAcceptingId] = useState(null);

  const load = () => {
    api.get("/ai/pending-review").then(({ data }) => setItems(data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const accept = async (answerId) => {
    setAcceptingId(answerId);
    try {
      await api.put(`/answers/${answerId}/accept`);
      load();
    } finally {
      setAcceptingId(null);
    }
  };

  return (
    <Layout title="AI Review Queue">
      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <p className="text-muted" style={{ margin: 0, fontSize: 13.5 }}>
          Every AI-generated answer someone submitted for review, from any user, waiting to be accepted into the{" "}
          <Link to="/knowledge-base">Knowledge Base</Link>. Casual AI Assistant chat that nobody submitted never shows up here.
        </p>
      </div>

      {loading ? (
        <Loader label="Loading the review queue..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<FaRobot />}
          title="Nothing waiting for review"
          description="When someone submits an AI Assistant answer for review, it'll show up here."
        />
      ) : (
        <div className="questions-list">
          {items.map((item) => (
            <div key={item.QuestionID} className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15.5 }}>{item.Title}</div>
                  <div className="text-faint" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
                    <FaUser /> {item.AuthorName} &middot; {formatDateTime(item.CreatedAt)}
                  </div>
                </div>
                <span className="pill pill-level"><FaRobot /> AI-suggested</span>
              </div>

              {item.AttachmentPath && (
                <img
                  src={attachmentUrl(item.AttachmentPath)}
                  alt="Attachment"
                  style={{ maxWidth: 220, borderRadius: 8, border: "1px solid var(--color-border)", marginBottom: 12 }}
                />
              )}

              {item.Answer && (
                <div style={{ background: "var(--color-bg)", borderRadius: 10, padding: 14, marginBottom: 12 }}>
                  <MarkdownContent>{item.Answer.AnswerText}</MarkdownContent>
                </div>
              )}

              <button
                type="button"
                className="btn btn-primary"
                onClick={() => accept(item.Answer.AnswerID)}
                disabled={acceptingId === item.Answer.AnswerID}
              >
                <FaCheckCircle /> {acceptingId === item.Answer.AnswerID ? "Accepting..." : "Accept into Knowledge Base"}
              </button>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
