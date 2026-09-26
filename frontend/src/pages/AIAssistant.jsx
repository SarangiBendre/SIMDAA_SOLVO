import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { FaRobot, FaPaperPlane, FaUser, FaPaperclip, FaTimes, FaCheckCircle, FaHourglassHalf, FaTrash } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import MarkdownContent from "../components/MarkdownContent";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { formatDateTime } from "../utils/date";

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]); // strip "data:...;base64,"
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function stripMarkdown(text) {
  return text
    .replace(/[#*_`>]/g, "")
    .replace(/\n{2,}/g, " ")
    .replace(/\n/g, " ")
    .trim();
}

async function deleteReviewItem(questionId, setReviewHistory) {
  if (!window.confirm("Delete this submission? This cannot be undone.")) return;
  await api.delete(`/questions/${questionId}`);
  setReviewHistory((prev) => prev.filter((item) => item.QuestionID !== questionId));
}

const WELCOME_MESSAGE = {
  role: "assistant",
  content: "Hi! I'm the SIMDAA SOLVO AI Assistant. Ask me to explain a concept, help debug an error, write some code, or attach a screenshot. If an answer is worth keeping, hit \"Send for Mentor review\" and it'll be reviewed for the Knowledge Base.",
};

export default function AIAssistant() {
  const { user } = useAuth();
  const storageKey = `simdaa_ai_chat_${user?.UserID ?? "guest"}`;

  // Live chat is kept in the browser (not the database) - this is what
  // makes it survive switching to another page and back, or refreshing,
  // without saving every casual message as a reviewable question. It's
  // scoped per-account so different logins on the same browser don't
  // see each other's conversation.
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {
      // ignore malformed/unavailable storage and fall back to the greeting
    }
    return [WELCOME_MESSAGE];
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {
      // storage full or unavailable (e.g. private browsing) - chat still
      // works for this session, it just won't persist
    }
  }, [messages, storageKey]);

  const clearChat = () => {
    if (!window.confirm("Clear this conversation? This can't be undone.")) return;
    setMessages([WELCOME_MESSAGE]);
  };

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const bottomRef = useRef(null);

  const [reviewHistory, setReviewHistory] = useState([]);
  const [loadingReviewHistory, setLoadingReviewHistory] = useState(true);

  const loadReviewHistory = () => {
    api.get("/ai/my-questions").then(({ data }) => setReviewHistory(data)).finally(() => setLoadingReviewHistory(false));
  };

  useEffect(() => { loadReviewHistory(); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const send = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if ((!text && !imageFile) || sending) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const userMessage = text || "What do you see in this image?";
    setMessages((m) => [...m, { role: "user", content: userMessage, image: imagePreview }]);
    setInput("");
    setSending(true);

    try {
      let imagePayload = {};
      if (imageFile) {
        const base64 = await fileToBase64(imageFile);
        imagePayload = { ImageBase64: base64, ImageMimeType: imageFile.type };
      }
      removeImage();

      const { data } = await api.post("/ai/chat", { Message: userMessage, History: history, ...imagePayload });
      setMessages((m) => [...m, { role: "assistant", content: data.Reply, forQuestion: userMessage, submitted: false }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong reaching the AI Assistant. Please try again." }]);
    } finally {
      setSending(false);
    }
  };

  const submitForReview = async (index) => {
    const answerMsg = messages[index];
    setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, submitting: true } : msg)));
    try {
      await api.post("/ai/submit-for-review", {
        Message: answerMsg.forQuestion,
        AnswerText: answerMsg.content,
      });
      setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, submitted: true, submitting: false } : msg)));
      loadReviewHistory();
    } catch (err) {
      setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, submitting: false } : msg)));
    }
  };

  return (
    <Layout title="AI Assistant">
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 10 }}>
        <button type="button" className="btn btn-secondary" style={{ padding: "6px 12px", fontSize: 13 }} onClick={clearChat}>
          Clear chat
        </button>
      </div>

      <div className="card" style={{ display: "flex", flexDirection: "column", height: "60vh", marginBottom: 24 }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignSelf: m.role === "user" ? "flex-end" : "flex-start", maxWidth: "75%" }}>
              <div style={{ display: "flex", gap: 10, flexDirection: m.role === "user" ? "row-reverse" : "row" }}>
                <div
                  style={{
                    width: 30, height: 30, borderRadius: "50%", flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: m.role === "user" ? "var(--color-primary)" : "#EEF4FF",
                    color: m.role === "user" ? "#fff" : "var(--color-primary)",
                    fontSize: 13,
                  }}
                >
                  {m.role === "user" ? <FaUser /> : <FaRobot />}
                </div>
                <div
                  style={{
                    padding: "10px 14px",
                    borderRadius: "var(--radius-md)",
                    background: m.role === "user" ? "var(--color-primary)" : "var(--color-bg)",
                    color: m.role === "user" ? "#fff" : "var(--color-text)",
                    whiteSpace: m.role === "user" ? "pre-wrap" : "normal",
                    lineHeight: 1.5,
                    fontSize: 14.5,
                  }}
                >
                  {m.image && (
                    <img src={m.image} alt="Attached" style={{ maxWidth: 220, borderRadius: 8, marginBottom: 8, display: "block" }} />
                  )}
                  {m.role === "assistant" ? <MarkdownContent>{m.content}</MarkdownContent> : m.content}
                </div>
              </div>

              {m.role === "assistant" && m.forQuestion && (
                <div style={{ marginTop: 6, marginLeft: 40 }}>
                  {m.submitted ? (
                    <span className="pill pill-answered"><FaCheckCircle /> Sent for mentor review</span>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: "5px 12px", fontSize: 12.5 }}
                      onClick={() => submitForReview(i)}
                      disabled={m.submitting}
                    >
                      {m.submitting ? "Sending..." : "Send for Mentor review"}
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
          {sending && <div className="text-faint" style={{ fontSize: 13 }}>Thinking...</div>}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} style={{ display: "flex", flexDirection: "column", gap: 10, padding: 16, borderTop: "1px solid var(--color-border)" }}>
          {imagePreview && (
            <div style={{ position: "relative", display: "inline-block" }}>
              <img src={imagePreview} alt="Preview" style={{ maxWidth: 140, borderRadius: 8, border: "1px solid var(--color-border)" }} />
              <button
                type="button"
                onClick={removeImage}
                style={{ position: "absolute", top: 4, right: 4, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 20, height: 20, cursor: "pointer" }}
              >
                <FaTimes size={10} />
              </button>
            </div>
          )}
          <div style={{ display: "flex", gap: 10 }}>
            <label className="btn btn-secondary" style={{ cursor: "pointer", padding: "12px 16px" }} title="Attach an image">
              <FaPaperclip />
              <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleImageChange} style={{ display: "none" }} />
            </label>
            <input
              type="text"
              placeholder="Ask a question, paste an error, or describe what you're stuck on..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{ flex: 1, padding: "12px 16px", borderRadius: "999px", border: "1.5px solid var(--color-border)" }}
            />
            <button type="submit" className="btn btn-primary" disabled={sending || (!input.trim() && !imageFile)}>
              <FaPaperPlane />
            </button>
          </div>
        </form>
      </div>

      <h3 style={{ margin: "0 0 14px" }}>Sent for mentor review</h3>
      <p className="text-muted" style={{ fontSize: 13.5, marginTop: -8, marginBottom: 16 }}>
        Once a mentor accepts one of these, it becomes part of the <Link to="/knowledge-base">Knowledge Base</Link> for everyone.
      </p>

      {loadingReviewHistory ? (
        <Loader label="Loading..." />
      ) : reviewHistory.length === 0 ? (
        <p className="text-muted">Nothing submitted yet - use the button under an answer above once you get one worth keeping.</p>
      ) : (
        <div className="questions-list">
          {reviewHistory.map((item) => (
            <div key={item.QuestionID} className="card" style={{ padding: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10, marginBottom: 8 }}>
                <div style={{ fontWeight: 600 }}>{item.Title}</div>
                <button
                  type="button"
                  onClick={() => deleteReviewItem(item.QuestionID, setReviewHistory)}
                  style={{ border: "none", background: "none", color: "var(--color-text-faint)", cursor: "pointer", flexShrink: 0 }}
                  aria-label="Delete submission"
                  title="Delete this submission"
                >
                  <FaTrash />
                </button>
              </div>
              {item.Answer && (
                <div style={{ fontSize: 13.5, color: "var(--color-text-muted)", marginBottom: 10 }}>
                  {stripMarkdown(item.Answer.AnswerText).slice(0, 160)}{item.Answer.AnswerText.length > 160 ? "..." : ""}
                </div>
              )}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                {item.Answer?.IsAccepted ? (
                  <span className="pill pill-answered"><FaCheckCircle /> Accepted into Knowledge Base</span>
                ) : (
                  <span className="pill pill-open"><FaHourglassHalf /> Awaiting mentor review</span>
                )}
                <span className="text-faint" style={{ fontSize: 12 }}>{formatDateTime(item.CreatedAt)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
