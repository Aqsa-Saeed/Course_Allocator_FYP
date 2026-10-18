// The only place that talks to the backend. Every page calls api.get / api.post / ...
// It adds the login token to each request and turns errors into readable messages.

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

let token = localStorage.getItem("token");
let onUnauthorized = () => {};

export function setToken(value) {
  token = value;
  if (value) localStorage.setItem("token", value);
  else localStorage.removeItem("token");
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export class ApiError extends Error {
  constructor(status, message, conflicts = []) {
    super(message);
    this.status = status;
    this.conflicts = conflicts; // set when an allocation is refused: every reason, not just the first
  }
}

// FastAPI sends errors as {detail: "text"} or {detail: [{loc, msg}, ...]} for validation problems.
function messageFrom(body, status) {
  const detail = body && body.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail.message === "string") return detail.message;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => `${(d.loc || []).filter((p) => p !== "body").join(" ")}: ${d.msg}`)
      .join("; ");
  }
  return `Request failed (${status})`;
}

async function request(method, path, { params, body, form } = {}) {
  const url = new URL(BASE + path);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  });

  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url.toString(), { method, headers, body: payload });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the backend running?");
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized();
    throw new ApiError(response.status, messageFrom(data, response.status), data?.detail?.conflicts || []);
  }
  return data;
}

export const api = {
  get: (path, params) => request("GET", path, { params }),
  post: (path, body) => request("POST", path, { body }),
  put: (path, body) => request("PUT", path, { body }),
  patch: (path, body) => request("PATCH", path, { body }),
  del: (path) => request("DELETE", path),
  login: (username, password) => request("POST", "/auth/login", { form: { username, password } }),
};
