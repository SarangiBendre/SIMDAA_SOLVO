import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaRobot, FaLightbulb, FaPaperclip, FaTimes } from "react-icons/fa";
import Layout from "../components/Layout";
import StatusPill from "../components/StatusPill";
import MarkdownContent from "../components/MarkdownContent";
import api, { uploadImage } from "../api/client";
import { Link } from "react-router-dom";
import "../styles/questions.css";

export default function AskQuestion() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [attachmentFile, setAttachmentFile] = useState(null);
  const [attachmentPreview, setAttachmentPreview] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [suggestion, setSuggestion] = useState(null);
  const [suggestError, setSuggestError] = useState("");
  const [checking, setChecking] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    api.get("/categories/").then(({ data }) => {
      setCategories(data);
      if (data.length) setCategoryId(String(data[0].CategoryID));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (title.trim().length < 8) {
      setSuggestion(null);
      setSuggestError("");
      return;
    }

    debounceRef.current = setTimeout(() => {
      setChecking(true);
      setSuggestError("");
      api.post("/questions/suggest", { Title: title, Description: description })
        .then(({ data }) => setSuggestion(data))
        .catch((err) => {
          console.error("Knowledge Base suggest failed:", err);
          setSuggestion(null);
          setSuggestError(
            err.response
              ? `Server error (${err.response.status}): ${err.response.data?.detail || "check backend logs"}`
              : "Could not reach the backend - is it running and is VITE_API_URL correct?"
          );
        })
        .finally(() => setChecking(false));
    }, 1500);

    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, description]);

  const handleAttachmentChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachmentFile(file);
    setAttachmentPreview(URL.createObjectURL(file));
  };

  const removeAttachment = () => {
    setAttachmentFile(null);
    setAttachmentPreview(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      let attachmentPath = null;
      if (attachmentFile) {
        setUploading(true);
        attachmentPath = await uploadImage(attachmentFile);
        setUploading(false);
      }

      const { data } = await api.post("/questions/", {
        CategoryID: Number(categoryId),
        Title: title,
        Description: description,
        AttachmentPath: attachmentPath,
      });
      navigate(`/questions/${data.QuestionID}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not post your question. Please try again.");
    } finally {
      setSubmitting(false);
      setUploading(false);
    }
  };

  return (
    <Layout title="Ask a Question">
      <div className="dashboard-columns">
        <div className="card section-card">
          {error && <div className="alert alert-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="category">Category</label>
              <select id="category" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
                {categories.map((c) => (
                  <option key={c.CategoryID} value={c.CategoryID}>{c.CategoryName}</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="title">Title</label>
              <input
                id="title"
                type="text"
                placeholder="Summarize your question in one line"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                placeholder="Add as much detail as possible - what you tried, error messages, context..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                rows={8}
              />
            </div>

            <div className="field">
              <label>Attachment (optional)</label>
              {attachmentPreview ? (
                <div style={{ position: "relative", display: "inline-block" }}>
                  <img src={attachmentPreview} alt="Attachment preview" style={{ maxWidth: 240, borderRadius: 8, border: "1px solid var(--color-border)" }} />
                  <button
                    type="button"
                    onClick={removeAttachment}
                    style={{ position: "absolute", top: 6, right: 6, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 24, height: 24, cursor: "pointer" }}
                  >
                    <FaTimes size={12} />
                  </button>
                </div>
              ) : (
                <label className="btn btn-secondary" style={{ width: "fit-content", cursor: "pointer" }}>
                  <FaPaperclip /> Attach a screenshot or image
                  <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleAttachmentChange} style={{ display: "none" }} />
                </label>
              )}
            </div>

            <button type="submit" className="btn btn-primary" disabled={submitting || uploading}>
              {uploading ? "Uploading attachment..." : submitting ? "Posting..." : "Post question"}
            </button>
          </form>
        </div>

        <div>
          <div className="card section-card">
            <h3><FaRobot style={{ color: "var(--color-secondary)", marginRight: 8 }} />Knowledge Base check</h3>

            {title.trim().length < 8 ? (
              <p className="text-muted" style={{ fontSize: 13.5 }}>
                Start typing a title (8+ characters) and we'll check for similar
                questions that may already be solved.
              </p>
            ) : checking ? (
              <p className="text-muted" style={{ fontSize: 13.5 }}>Checking the knowledge base...</p>
            ) : suggestError ? (
              <div className="alert alert-error" style={{ fontSize: 13 }}>{suggestError}</div>
            ) : suggestion ? (
              <>
                <div className="alert alert-info" style={{ display: "flex", gap: 10 }}>
                  <FaLightbulb style={{ marginTop: 2, flexShrink: 0 }} />
                  <div>
                    {suggestion.AISource === "heuristic" ? (
                      <span style={{ whiteSpace: "pre-wrap" }}>{suggestion.AISuggestion}</span>
                    ) : (
                      <MarkdownContent>{suggestion.AISuggestion}</MarkdownContent>
                    )}
                    <div className="text-faint" style={{ fontSize: 11, marginTop: 6 }}>
                      {suggestion.AISource === "heuristic"
                        ? ""
                        : `Generated by "Simdaa Solvo"`}
                    </div>
                  </div>
                </div>

                {suggestion.RelatedQuestions.length > 0 && (
                  <>
                    <p className="text-muted" style={{ fontSize: 12.5, marginBottom: 8 }}>
                      Related questions:
                    </p>
                    {suggestion.RelatedQuestions.map((q) => (
                      <Link
                        key={q.QuestionID}
                        to={`/questions/${q.QuestionID}`}
                        className="recent-question-row"
                        style={{ padding: "8px 0" }}
                      >
                        <div>
                          <div className="rq-title" style={{ fontSize: 13.5 }}>{q.Title}</div>
                          <StatusPill status={q.Status} />
                        </div>
                        <span className="text-faint" style={{ fontSize: 12 }}>{q.MatchScore}% match</span>
                      </Link>
                    ))}
                  </>
                )}
              </>
            ) : null}
          </div>
        </div>
      </div>
    </Layout>
  );
}
