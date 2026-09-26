/**
 * The backend stores and returns timestamps as UTC, but without a
 * timezone suffix (e.g. "2026-09-15T10:23:45.123456" instead of
 * "...123456Z"). `new Date(...)` on a string with no timezone info
 * gets parsed as LOCAL time by the browser, not UTC - which silently
 * shifted every displayed timestamp by the viewer's UTC offset.
 *
 * This wraps every timestamp coming from the API so it's always
 * interpreted as UTC before being converted to the viewer's local time.
 */
export function parseServerDate(value) {
  if (!value) return null;
  const hasTimezone = /Z$|[+-]\d{2}:\d{2}$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

function pad(n) {
  return String(n).padStart(2, "0");
}

/** DD-MM-YYYY, project-wide standard date format (not locale-dependent). */
export function formatDate(value) {
  const date = parseServerDate(value);
  if (!date) return "";
  return `${pad(date.getDate())}-${pad(date.getMonth() + 1)}-${date.getFullYear()}`;
}

/** DD-MM-YYYY, HH:MM (24-hour, local time). */
export function formatDateTime(value) {
  const date = parseServerDate(value);
  if (!date) return "";
  return `${formatDate(value)}, ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
