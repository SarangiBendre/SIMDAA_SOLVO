import { Link } from "react-router-dom";
import { FaEye, FaCommentDots, FaClock, FaRobot } from "react-icons/fa";
import StatusPill from "./StatusPill";
import { parseServerDate } from "../utils/date";

function timeAgo(dateStr) {
  const date = parseServerDate(dateStr);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  const units = [
    ["year", 31536000], ["month", 2592000], ["day", 86400],
    ["hour", 3600], ["minute", 60],
  ];
  for (const [name, secs] of units) {
    const value = Math.floor(seconds / secs);
    if (value >= 1) return `${value} ${name}${value > 1 ? "s" : ""} ago`;
  }
  return "just now";
}

export default function QuestionCard({ question }) {
  return (
    <Link to={`/questions/${question.QuestionID}`} className="question-card">
      <div className="question-card-top">
        <StatusPill status={question.Status} />
        {question.CategoryName && <span className="question-card-category">{question.CategoryName}</span>}
        {question.Source === "ai_assistant" && (
          <span className="pill pill-level"><FaRobot /> AI Assistant</span>
        )}
      </div>

      <h3 className="question-card-title">{question.Title}</h3>

      <div className="question-card-meta">
        <span><FaCommentDots /> {question.AnswersCount ?? 0} answers</span>
        <span><FaEye /> {question.ViewsCount ?? 0} {(question.ViewsCount ?? 0) === 1 ? "view" : "views"}</span>
        <span><FaClock /> {timeAgo(question.CreatedAt)}</span>
        {question.AuthorName && <span className="question-card-author">by {question.AuthorName}</span>}
      </div>
    </Link>
  );
}
