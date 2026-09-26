import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FaPlusCircle } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import QuestionCard from "../components/QuestionCard";
import api from "../api/client";
import { Link } from "react-router-dom";
import "../styles/questions.css";

export default function Questions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const keyword = searchParams.get("q") || "";

  const [categories, setCategories] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/categories/").then(({ data }) => setCategories(data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const request = keyword
      ? api.get("/questions/search", { params: { keyword } })
      : api.get("/questions/", { params: { category_id: categoryId || undefined, status: status || undefined } });

    request
      .then(({ data }) => setQuestions(data))
      .finally(() => setLoading(false));
  }, [keyword, categoryId, status]);

  const clearSearch = () => {
    searchParams.delete("q");
    setSearchParams(searchParams);
  };

  return (
    <Layout title="Questions">
      <div className="questions-toolbar">
        {keyword ? (
          <span className="text-muted">
            Showing results for <strong>&ldquo;{keyword}&rdquo;</strong>
            {" "}&middot;{" "}
            <button className="btn btn-secondary" style={{ padding: "4px 10px" }} onClick={clearSearch}>Clear</button>
          </span>
        ) : (
          <>
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c.CategoryID} value={c.CategoryID}>{c.CategoryName}</option>
              ))}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All statuses</option>
              <option value="1">Open</option>
              <option value="2">Answered</option>
              <option value="3">Closed</option>
            </select>
          </>
        )}
        <Link to="/ask-question" className="btn btn-primary" style={{ marginLeft: "auto" }}>
          <FaPlusCircle /> Ask a question
        </Link>
      </div>

      {loading ? (
        <Loader label="Loading questions..." />
      ) : questions.length === 0 ? (
        <EmptyState
          title="No questions found"
          description="Try a different filter, or be the first to ask something in this category."
          action={<Link to="/ask-question" className="btn btn-primary">Ask a question</Link>}
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
