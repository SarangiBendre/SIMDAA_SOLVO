import ReactMarkdown from "react-markdown";
import "./MarkdownContent.css";

/** Renders AI-generated text (which comes back as Markdown - bold,
 * headings, lists, code) as actual formatted HTML instead of showing
 * the raw **asterisks** and ### hashes. Used for the AI Assistant chat
 * and for any AI-generated answer shown elsewhere (Question Details,
 * Knowledge Base) once it's been accepted. */
export default function MarkdownContent({ children }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}
