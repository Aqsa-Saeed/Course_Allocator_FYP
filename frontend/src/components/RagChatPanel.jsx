import { useEffect, useRef } from "react";
import "../rag/rag-chat.css";
import "../rag/rag-chat.js"; // registers window.RagChat

// Where the FastAPI backend lives. Set VITE_API_URL in frontend/.env if it isn't on port 8000.
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Fallback used when no getHeaders prop is passed: looks for a JWT in localStorage.
// >>> If your auth.jsx stores the token under a different key, add it to this list. <<<
const TOKEN_KEYS = ["token", "access_token", "accessToken", "jwt"];

function defaultHeaders() {
  for (const key of TOKEN_KEYS) {
    const t = localStorage.getItem(key);
    if (t) return { Authorization: `Bearer ${t}` };
  }
  return {};
}

/**
 * Document chat (RAG). Props:
 *   apiBase    – defaults to `${VITE_API_URL}/rag`
 *   getHeaders – () => ({ Authorization: "Bearer ..." }); defaults to reading localStorage
 */
export default function RagChatPanel({ apiBase = `${API_URL}/rag`, getHeaders, style }) {
  const hostRef = useRef(null);
  const headersRef = useRef(getHeaders);
  headersRef.current = getHeaders; // always call the latest function without remounting

  useEffect(() => {
    const instance = window.RagChat.mount(hostRef.current, {
      apiBase,
      getHeaders: () => (headersRef.current ? headersRef.current() : defaultHeaders()),
    });
    return () => instance.destroy();
  }, [apiBase]);

  return <div ref={hostRef} style={{ height: "100%", ...style }} />;
}
