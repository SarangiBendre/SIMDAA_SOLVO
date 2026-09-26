import axios from "axios";

// Set VITE_API_URL in frontend/.env to point at a deployed backend.
// Defaults to the local FastAPI dev server.
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // A failed login attempt (wrong username/password) also returns 401,
    // but that's not a "session expired" event - it must never trigger
    // the redirect-to-login logic below, or the login page ends up
    // reloading itself instead of just showing the error inline.
    const isLoginRequest = error.config?.url?.includes("/auth/login");

    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

/** Uploads an image file (question/answer attachment) and returns its
 * server URL (e.g. "/uploads/abc123.png"). Used for attachments on
 * questions and answers - not for AI Assistant images, which are sent
 * inline as base64 instead of being persisted. */
export async function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/uploads/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.url;
}

/** Turns the server-relative attachment path ("/uploads/x.png") into a
 * full URL the browser can load, using the same API base as axios. */
export function attachmentUrl(path) {
  if (!path) return null;
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}
