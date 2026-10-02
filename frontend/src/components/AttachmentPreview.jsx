import { FaFilePdf, FaFileWord, FaFileExcel, FaFilePowerpoint, FaFileVideo, FaFileAlt, FaTimes } from "react-icons/fa";

const ICONS_BY_EXTENSION = {
  pdf: FaFilePdf,
  doc: FaFileWord,
  docx: FaFileWord,
  xls: FaFileExcel,
  xlsx: FaFileExcel,
  ppt: FaFilePowerpoint,
  pptx: FaFilePowerpoint,
  mp4: FaFileVideo,
  mov: FaFileVideo,
  webm: FaFileVideo,
  mkv: FaFileVideo,
  avi: FaFileVideo,
};

function isImage(file) {
  return file?.type?.startsWith("image/");
}

function isVideo(file) {
  return file?.type?.startsWith("video/");
}

/** Shows a real thumbnail for an image, an inline player for a video,
 * and a plain file-name card (with a type-appropriate icon) for
 * anything else - a document just rendered through a bare <img> tag
 * would otherwise show a broken-image icon instead of anything useful. */
export default function AttachmentPreview({ file, previewUrl, onRemove }) {
  if (!file || !previewUrl) return null;

  const ext = file.name.split(".").pop()?.toLowerCase();
  const Icon = ICONS_BY_EXTENSION[ext] || FaFileAlt;

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {isImage(file) ? (
        <img src={previewUrl} alt="Attachment preview" style={{ maxWidth: 240, borderRadius: 8, border: "1px solid var(--color-border)", display: "block" }} />
      ) : isVideo(file) ? (
        <video src={previewUrl} controls style={{ maxWidth: 240, maxHeight: 180, borderRadius: 8, border: "1px solid var(--color-border)", display: "block" }} />
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 8, border: "1px solid var(--color-border)", background: "var(--color-surface-alt, #F8FAFC)", maxWidth: 240 }}>
          <Icon size={22} style={{ color: "var(--color-primary)", flexShrink: 0 }} />
          <span style={{ fontSize: 13.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
        </div>
      )}
      <button
        type="button"
        onClick={onRemove}
        style={{ position: "absolute", top: 6, right: 6, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 24, height: 24, cursor: "pointer" }}
      >
        <FaTimes size={12} />
      </button>
    </div>
  );
}
