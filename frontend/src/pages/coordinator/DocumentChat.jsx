import { useCallback, useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import ChatPanel from "../../components/rag/ChatPanel.jsx";
import DocumentLibrary from "../../components/rag/DocumentLibrary.jsx";
import { rag } from "../../rag/ragApi.js";
import "../../rag/rag.css";

const asList = (r) => (Array.isArray(r) ? r : r?.items || r?.results || []);

// Field names differ between schemas, so try the likely ones. Anything unrecognised is skipped,
// and the upload form falls back to a plain text box.
const instructorName = (i) =>
  i.name || i.full_name || i.instructor_name || [i.first_name, i.last_name].filter(Boolean).join(" ") || null;
const courseCode = (c) => c.code || c.course_code || null;

export default function DocumentChat() {
  const { canWrite } = useAuth();
  const [docs, setDocs] = useState(null);
  const [meta, setMeta] = useState(null);
  const [instructors, setInstructors] = useState([]);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = useCallback(async () => {
    try {
      const [d, m] = await Promise.all([rag.documents(), rag.meta()]);
      setDocs(d);
      setMeta(m);
    } catch (e) {
      setError(e.message);
      setDocs((d) => d || []);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Real instructors and courses from your database, so uploads are linked to them by id.
  useEffect(() => {
    api.get("/instructors").then((r) => {
      setInstructors(asList(r).map((i) => ({ id: i.id, name: instructorName(i) })).filter((i) => i.id != null && i.name));
    }).catch(() => {});
    api.get("/courses").then((r) => {
      setCourses(asList(r).map((c) => {
        const code = courseCode(c);
        return code ? { id: c.id, code, label: c.title || c.name ? `${code}, ${c.title || c.name}` : code } : null;
      }).filter(Boolean));
    }).catch(() => {});
  }, []);

  const openDoc = async (id, page) => {
    const doc = (docs || []).find((d) => d.id === id);
    if (!doc) return setError("That document is no longer in the library.");
    try { await rag.openFile(doc, page); } catch (e) { setError(e.message); }
  };

  if (docs === null) return <div className="loading">Loading…</div>;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Document chat</h1>
          <div className="subtitle">Ask questions about course outlines and faculty feedback. Every answer cites its sources.</div>
        </div>
      </div>

      {error && <div className="notice error" role="alert"><span>{error}</span><button type="button" aria-label="Dismiss" onClick={() => setError("")}>×</button></div>}
      {success && <div className="notice success" role="status"><span>{success}</span><button type="button" aria-label="Dismiss" onClick={() => setSuccess("")}>×</button></div>}
      {meta && !meta.llm_configured && (
        <div className="notice info">The server has no Hugging Face token (HF_TOKEN), so chat will list matching passages without a written answer.</div>
      )}

      <div className="rag-grid">
        <DocumentLibrary
          docs={docs} meta={meta} instructors={instructors} courses={courses} canWrite={canWrite}
          onChanged={load} onOpen={openDoc}
          onError={(m) => { setSuccess(""); setError(m); }}
          onSuccess={(m) => { setError(""); setSuccess(m); }}
        />
        <ChatPanel meta={meta} docs={docs} onOpen={openDoc} />
      </div>
    </>
  );
}
