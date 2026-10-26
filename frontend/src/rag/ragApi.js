// Calls the /rag endpoints. JSON calls reuse your api.js (token, error messages, auto-logout on 401).
// Only two things need their own fetch: multipart uploads and downloading a file with the login token.
import { api, ApiError } from "../api.js";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const authHeaders = () => {
  const token = localStorage.getItem("token"); // same key api.js writes in setToken()
  return token ? { Authorization: `Bearer ${token}` } : {};
};

function messageFrom(body, status) {
  const detail = body && body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return `Request failed (${status})`;
}

async function upload(formData) {
  let res;
  try {
    res = await fetch(`${BASE}/rag/documents`, { method: "POST", headers: authHeaders(), body: formData });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the backend running?");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, messageFrom(data, res.status));
  return data;
}

// PDFs open in a new tab at the cited page; other formats download.
async function openFile(doc, page) {
  const isPdf = /\.pdf$/i.test(doc.filename);
  const win = isPdf ? window.open("", "_blank") : null; // opened synchronously so pop-up blockers allow it
  try {
    const res = await fetch(`${BASE}/rag/documents/${doc.id}/file`, { headers: authHeaders() });
    if (!res.ok) {
      throw new ApiError(res.status, res.status === 410 ? "The original file is no longer on the server." : "Could not open the file.");
    }
    const url = URL.createObjectURL(await res.blob());
    if (win) {
      win.location.href = url + (page ? `#page=${page}` : "");
    } else {
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    if (win) win.close();
    throw e;
  }
}

export const rag = {
  meta: () => api.get("/rag/meta"),
  documents: () => api.get("/rag/documents"),
  remove: (id) => api.del(`/rag/documents/${id}`),
  chat: (payload) => api.post("/rag/chat", payload),
  upload,
  openFile,
};
