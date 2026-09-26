import { useEffect, useState } from "react";
import { FaBookOpen, FaSearch } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import QuestionCard from "../components/QuestionCard";
import api from "../api/client";
import "../styles/questions.css";

const STATUS_ANSWERED = 2;

export default function KnowledgeBase() {
  const [keyword, setKeyword] = useState("");
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const request = keyword
      ? api.get("/questions/search", { params: { keyword } })
      : api.get("/questions/", { params: { status: STATUS_ANSWERED } });

    request
      .then(({ data }) => {
        const answered = keyword ? data.filter((q) => q.Status === "Answered") : data;
        setQuestions(answered);
      })
      .finally(() => setLoading(false));
  }, [keyword]);

  return (
    <Layout title="Knowledge Base">
      <div className="card" style={{ padding: 20, marginBottom: 20, display: "flex", gap: 14, alignItems: "center" }}>
        <FaBookOpen style={{ fontSize: 22, color: "var(--color-primary)", flexShrink: 0 }} />
        <div>
          <strong>Organizational memory that grows over time.</strong>
          <p className="text-muted" style={{ margin: "4px 0 0", fontSize: 13.5 }}>
            Every solved question lives here, permanently searchable, so the answer only has to be found once.
          </p>
        </div>
      </div>

      <div className="questions-toolbar">
        <div className="topbar-search" style={{ maxWidth: 480, flex: 1 }}>
          <FaSearch />
          <input
            type="text"
            placeholder="Search solved questions..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <Loader label="Loading the knowledge base..." />
      ) : questions.length === 0 ? (
        <EmptyState
          icon={<FaBookOpen />}
          title="Nothing solved yet"
          description="Once a question gets an accepted answer, it shows up here for everyone to reuse."
        />
      ) : (
        <div className="questions-list">
          {questions.map((q) => (
            <QuestionCard key={q.QuestionID} question={q} />
          ))}
        </div>
      )}
    </Layout>
  );
}
