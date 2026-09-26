import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { FaCheckCircle, FaThumbsUp, FaComment, FaEye, FaClock, FaEdit, FaTrash, FaPaperclip, FaTimes, FaRobot } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import StatusPill from "../components/StatusPill";
import MarkdownContent from "../components/MarkdownContent";
import api, { uploadImage, attachmentUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { formatDateTime } from "../utils/date";
import "../styles/questions.css";

function AnswerComments({ answerId, currentUserId }) {
  const [comments, setComments] = useState([]);
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const load = useCallback(() => {
    api.get(`/comments/answer/${answerId}`).then(({ data }) => setComments(data));
  }, [answerId]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    await api.post("/comments/", { AnswerID: answerId, CommentText: text });
    setText("");
    load();
  };

  const startEdit = (c) => {
    setEditingId(c.CommentID);
    setEditText(c.CommentText);
  };

  const saveEdit = async (commentId) => {
    if (!editText.trim()) return;
    await api.put(`/comments/${commentId}`, { CommentText: editText });
    setEditingId(null);
    load();
  };

  const remove = async (commentId) => {
    if (!window.confirm("Delete this comment?")) return;
    await api.delete(`/comments/${commentId}`);
    load();
  };

  return (
    <div style={{ marginTop: 12 }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{ border: "none", background: "none", color: "var(--color-text-muted)", fontSize: 13, cursor: "pointer", padding: 0 }}
      >
        <FaComment style={{ marginRight: 6 }} />{open ? "Hide comments" : "View comments"}
      </button>

      {open && (
        <div style={{ marginTop: 10, paddingLeft: 4 }}>
          {comments.map((c) => (
            <div key={c.CommentID} style={{ fontSize: 13.5, padding: "8px 0", borderTop: "1px solid var(--color-border)" }}>
              {editingId === c.CommentID ? (
                <div style={{ display: "flex", gap: 8 }}>
                  <input
                    type="text"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    style={{ flex: 1, padding: "6px 10px", borderRadius: 8, border: "1.5px solid var(--color-border)" }}
                  />
                  <button type="button" className="btn btn-secondary" style={{ padding: "6px 12px" }} onClick={() => saveEdit(c.CommentID)}>Save</button>
                  <button type="button" className="btn btn-secondary" style={{ padding: "6px 12px" }} onClick={() => setEditingId(null)}>Cancel</button>
                </div>
              ) : (
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                  <span>{c.CommentText}</span>
                  {c.UserID === currentUserId && (
                    <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                      <button type="button" onClick={() => startEdit(c)} style={{ border: "none", background: "none", color: "var(--color-text-faint)", cursor: "pointer" }}>
                        <FaEdit />
                      </button>
                      <button type="button" onClick={() => remove(c.CommentID)} style={{ border: "none", background: "none", color: "var(--color-text-faint)", cursor: "pointer" }}>
                        <FaTrash />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <form onSubmit={submit} style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <input
              type="text"
              placeholder="Add a comment..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--color-border)" }}
            />
            <button type="submit" className="btn btn-secondary" style={{ padding: "8px 14px" }}>Send</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default function QuestionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isMentor, isAdmin } = useAuth();
  const [question, setQuestion] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [answerText, setAnswerText] = useState("");
  const [posting, setPosting] = useState(false);
  const [answerAttachmentFile, setAnswerAttachmentFile] = useState(null);
  const [answerAttachmentPreview, setAnswerAttachmentPreview] = useState(null);
  const [uploadingAnswerAttachment, setUploadingAnswerAttachment] = useState(false);

  const [editingQuestion, setEditingQuestion] = useState(false);
  const [qTitle, setQTitle] = useState("");
  const [qDescription, setQDescription] = useState("");
  const [qCategoryId, setQCategoryId] = useState("");

  const [editingAnswerId, setEditingAnswerId] = useState(null);
  const [editAnswerText, setEditAnswerText] = useState("");

  const load = useCallback(() => {
    api.get(`/questions/${id}/details`).then(({ data }) => setQuestion(data)).finally(() => setLoading(false));
  }, [id]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    api.get("/categories/").then(({ data }) => setCategories(data)).catch(() => {});
  }, []);

  // Records a view for the current user (deduped server-side, per user
  // per question - see the /view endpoint) whenever this question is
  // opened. React StrictMode may call this twice in dev; that's fine,
  // the backend is idempotent for the same user/question pair.
  useEffect(() => {
    api.post(`/questions/${id}/view`).catch(() => {});
  }, [id]);

  const isOwner = question && user && question.UserID === user.UserID;

  const handleAnswerAttachmentChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnswerAttachmentFile(file);
    setAnswerAttachmentPreview(URL.createObjectURL(file));
  };

  const removeAnswerAttachment = () => {
    setAnswerAttachmentFile(null);
    setAnswerAttachmentPreview(null);
  };

  const submitAnswer = async (e) => {
    e.preventDefault();
    if (!answerText.trim()) return;
    setPosting(true);
    try {
      let attachmentPath = null;
      if (answerAttachmentFile) {
        setUploadingAnswerAttachment(true);
        attachmentPath = await uploadImage(answerAttachmentFile);
        setUploadingAnswerAttachment(false);
      }
      await api.post("/answers/", { QuestionID: Number(id), AnswerText: answerText, AttachmentPath: attachmentPath });
      setAnswerText("");
      removeAnswerAttachment();
      load();
    } finally {
      setPosting(false);
      setUploadingAnswerAttachment(false);
    }
  };

  const acceptAnswer = async (answerId) => {
    await api.put(`/answers/${answerId}/accept`);
    load();
  };

  const upvote = async (answerId) => {
    await api.put(`/answers/${answerId}/upvote`);
    load();
  };

  const startEditQuestion = () => {
    setQTitle(question.Title);
    setQDescription(question.Description);
    setQCategoryId(String(question.CategoryID));
    setEditingQuestion(true);
  };

  const saveQuestion = async (e) => {
    e.preventDefault();
    await api.put(`/questions/${id}`, {
      Title: qTitle,
      Description: qDescription,
      CategoryID: Number(qCategoryId),
    });
    setEditingQuestion(false);
    load();
  };

  const deleteQuestion = async () => {
    if (!window.confirm("Delete this question? This also removes all its answers and comments. This cannot be undone.")) return;
    await api.delete(`/questions/${id}`);
    navigate("/questions");
  };

  const startEditAnswer = (a) => {
    setEditingAnswerId(a.AnswerID);
    setEditAnswerText(a.AnswerText);
  };

  const saveAnswer = async (answerId) => {
    if (!editAnswerText.trim()) return;
    await api.put(`/answers/${answerId}`, { AnswerText: editAnswerText });
    setEditingAnswerId(null);
    load();
  };

  const deleteAnswer = async (answerId) => {
    if (!window.confirm("Delete this answer? This cannot be undone.")) return;
    await api.delete(`/answers/${answerId}`);
    load();
  };

  if (loading || !question) {
    return (
      <Layout title="Question">
        <Loader label="Loading question..." />
      </Layout>
    );
  }

  return (
    <Layout title="Question details">
      <div className="card qd-header" style={{ padding: 24 }}>
        {editingQuestion ? (
          <form onSubmit={saveQuestion}>
            <div className="field">
              <label>Category</label>
              <select value={qCategoryId} onChange={(e) => setQCategoryId(e.target.value)} required>
                {categories.map((c) => (
                  <option key={c.CategoryID} value={c.CategoryID}>{c.CategoryName}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Title</label>
              <input value={qTitle} onChange={(e) => setQTitle(e.target.value)} required />
            </div>
            <div className="field">
              <label>Description</label>
              <textarea rows={6} value={qDescription} onChange={(e) => setQDescription(e.target.value)} required />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="submit" className="btn btn-primary">Save changes</button>
              <button type="button" className="btn btn-secondary" onClick={() => setEditingQuestion(false)}>Cancel</button>
            </div>
          </form>
        ) : (
          <>
            <div className="question-card-top">
              <StatusPill status={question.Status} />
              <span className="question-card-category">{question.CategoryName}</span>
              {question.Source === "ai_assistant" && (
                <span className="pill pill-level"><FaRobot /> AI Assistant</span>
              )}
              {isOwner && (
                <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                  <button type="button" onClick={startEditQuestion} style={{ border: "none", background: "none", color: "var(--color-text-faint)", cursor: "pointer" }} aria-label="Edit question">
                    <FaEdit />
                  </button>
                  <button type="button" onClick={deleteQuestion} style={{ border: "none", background: "none", color: "var(--color-text-faint)", cursor: "pointer" }} aria-label="Delete question">
                    <FaTrash />
                  </button>
                </div>
              )}
            </div>
            <h2>{question.Title}</h2>
            <p className="qd-description">{question.Description}</p>
            {question.AttachmentPath && (
              <img
                src={attachmentUrl(question.AttachmentPath)}
                alt="Question attachment"
                style={{ maxWidth: 480, borderRadius: 8, border: "1px solid var(--color-border)", marginTop: 12 }}
              />
            )}
            <div className="qd-meta-row">
              <span><FaEye /> {question.ViewsCount} {question.ViewsCount === 1 ? "view" : "views"}</span>
              <span><FaClock /> {formatDateTime(question.CreatedAt)}</span>
              <span>Asked by {question.AuthorName}</span>
            </div>
          </>
        )}
      </div>

      <h3 style={{ margin: "28px 0 14px" }}>{question.Answers.length} Answer{question.Answers.length === 1 ? "" : "s"}</h3>

      {question.Answers.map((a) => (
        <div key={a.AnswerID} className={`card answer-item ${a.IsAccepted ? "accepted" : ""}`}>
          <div className="answer-item-head">
            <span>{a.AuthorName}</span>
            <span>{formatDateTime(a.CreatedAt)}</span>
          </div>

          {editingAnswerId === a.AnswerID ? (
            <div>
              <div className="field">
                <textarea rows={5} value={editAnswerText} onChange={(e) => setEditAnswerText(e.target.value)} />
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button type="button" className="btn btn-primary" style={{ padding: "8px 16px" }} onClick={() => saveAnswer(a.AnswerID)}>Save</button>
                <button type="button" className="btn btn-secondary" style={{ padding: "8px 16px" }} onClick={() => setEditingAnswerId(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <div className="answer-text">
              <MarkdownContent>{a.AnswerText}</MarkdownContent>
            </div>
          )}

          {a.AttachmentPath && (
            <img
              src={attachmentUrl(a.AttachmentPath)}
              alt="Answer attachment"
              style={{ maxWidth: 420, borderRadius: 8, border: "1px solid var(--color-border)", marginTop: 12 }}
            />
          )}

          {a.IsAIGenerated && (
            <div className="pill pill-level" style={{ marginTop: 10, marginBottom: a.IsAccepted ? 6 : 0 }}>
              AI-suggested{a.IsAccepted ? " - accepted into Knowledge Base" : " - awaiting mentor review"}
            </div>
          )}

          {a.IsAccepted && (
            <div className="accepted-tag" style={{ marginTop: 10 }}>
              <FaCheckCircle /> Accepted answer
            </div>
          )}

          <div className="answer-actions">
            <button type="button" onClick={() => upvote(a.AnswerID)}>
              <FaThumbsUp /> {a.Upvotes}
            </button>
            {!a.IsAccepted && (isOwner || (a.IsAIGenerated && (isMentor || isAdmin))) && (
              <button type="button" onClick={() => acceptAnswer(a.AnswerID)}>
                <FaCheckCircle /> Accept
              </button>
            )}
            {a.UserID === user.UserID && editingAnswerId !== a.AnswerID && (
              <>
                <button type="button" onClick={() => startEditAnswer(a)}>
                  <FaEdit /> Edit
                </button>
                <button type="button" onClick={() => deleteAnswer(a.AnswerID)}>
                  <FaTrash /> Delete
                </button>
              </>
            )}
          </div>

          <AnswerComments answerId={a.AnswerID} currentUserId={user.UserID} />
        </div>
      ))}

      <div className="card section-card">
        <h3>Your answer</h3>
        <form onSubmit={submitAnswer}>
          <div className="field">
            <textarea
              rows={6}
              placeholder="Share what you know..."
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label>Attachment (optional)</label>
            {answerAttachmentPreview ? (
              <div style={{ position: "relative", display: "inline-block" }}>
                <img src={answerAttachmentPreview} alt="Attachment preview" style={{ maxWidth: 220, borderRadius: 8, border: "1px solid var(--color-border)" }} />
                <button
                  type="button"
                  onClick={removeAnswerAttachment}
                  style={{ position: "absolute", top: 6, right: 6, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 24, height: 24, cursor: "pointer" }}
                >
                  <FaTimes size={12} />
                </button>
              </div>
            ) : (
              <label className="btn btn-secondary" style={{ width: "fit-content", cursor: "pointer" }}>
                <FaPaperclip /> Attach a screenshot or image
                <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleAnswerAttachmentChange} style={{ display: "none" }} />
              </label>
            )}
          </div>

          <button type="submit" className="btn btn-primary" disabled={posting || uploadingAnswerAttachment}>
            {uploadingAnswerAttachment ? "Uploading attachment..." : posting ? "Posting..." : "Post answer"}
          </button>
        </form>
      </div>
    </Layout>
  );
}
