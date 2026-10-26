import { useState } from "react";
import { rag } from "../../rag/ragApi.js";
import { KIND } from "./AnswerView.jsx";

export default function DocumentLibrary({ docs, meta, instructors, courses, canWrite, onChanged, onOpen, onError, onSuccess }) {
  const [kind, setKind] = useState("course_outline");
  const [files, setFiles] = useState([]); // [{file, status}]
  const [title, setTitle] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const [facultyKey, setFacultyKey] = useState(""); // instructor id (select) or typed name
  const [semester, setSemester] = useState("");
  const [uploading, setUploading] = useState(false);
  const [over, setOver] = useState(false);
  const [confirmId, setConfirmId] = useState(null);

  const feedback = kind === "faculty_feedback";
  const pickFiles = (list) => setFiles(Array.from(list).map((file) => ({ file, status: "" })));
  const setStatus = (idx, status) => setFiles((fs) => fs.map((f, i) => (i === idx ? { ...f, status } : f)));

  async function submit(e) {
    e.preventDefault();
    if (feedback && !facultyKey.trim()) return onError("Choose the faculty member this feedback is about.");
    setUploading(true);
    const selected = instructors.find((i) => String(i.id) === facultyKey);
    const course = courses.find((c) => c.code === courseCode);
    let ok = 0;
    for (let idx = 0; idx < files.length; idx++) {
      if (files[idx].status === "Done") continue;
      setStatus(idx, "Indexing…");
      const fd = new FormData();
      fd.append("file", files[idx].file);
      fd.append("doc_type", kind);
      if (files.length === 1 && title.trim()) fd.append("title", title.trim());
      if (courseCode.trim()) fd.append("course_code", courseCode.trim());
      if (course?.id != null) fd.append("course_id", String(course.id));
      if (semester.trim()) fd.append("semester", semester.trim());
      if (selected) {
        fd.append("instructor_id", String(selected.id));
        fd.append("instructor_name", selected.name);
      } else if (facultyKey.trim()) {
        fd.append("instructor_name", facultyKey.trim());
      }
      try {
        await rag.upload(fd);
        setStatus(idx, "Done");
        ok++;
      } catch (err) {
        setStatus(idx, "Failed");
        onError(`${files[idx].file.name}: ${err.message}`);
      }
    }
    setUploading(false);
    if (ok) {
      onSuccess(`${ok} ${ok === 1 ? "document is" : "documents are"} ready to chat with.`);
      setFiles((fs) => fs.filter((f) => f.status !== "Done"));
      setTitle("");
      onChanged();
    }
  }

  async function remove(doc) {
    if (confirmId !== doc.id) {
      setConfirmId(doc.id);
      setTimeout(() => setConfirmId((c) => (c === doc.id ? null : c)), 3500);
      return;
    }
    setConfirmId(null);
    try {
      await rag.remove(doc.id);
      onSuccess(`Deleted “${doc.title}”.`);
      onChanged();
    } catch (e) {
      onError(e.message);
    }
  }

  return (
    <div className="card">
      <div className="card-head"><h2>Documents</h2></div>

      {canWrite ? (
        <form className="rag-upload" onSubmit={submit}>
          <div className="tabs rag-kind" role="group" aria-label="Document type">
            {Object.entries(KIND).map(([value, label]) => (
              <button key={value} type="button" className={`tab${kind === value ? " active" : ""}`} aria-pressed={kind === value} onClick={() => setKind(value)}>{label}</button>
            ))}
          </div>

          <label className={`rag-drop${over ? " over" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setOver(true); }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); pickFiles(e.dataTransfer.files); }}>
            <strong>Choose files or drop them here</strong>
            <span className="small">PDF, Word or text</span>
            <input type="file" multiple accept=".pdf,.docx,.txt,.md" onChange={(e) => pickFiles(e.target.files)} />
          </label>
          {files.length > 0 && (
            <ul className="rag-picked" aria-live="polite">
              {files.map((f, i) => (
                <li key={i}>
                  <span className="name">{f.file.name}</span>
                  <span className={f.status === "Done" ? "ok" : f.status === "Failed" ? "bad" : "muted"}>{f.status}</span>
                </li>
              ))}
            </ul>
          )}

          {files.length <= 1 && (
            <label className="field"><span>Title</span>
              <input type="text" value={title} placeholder="Defaults to the file name" onChange={(e) => setTitle(e.target.value)} />
            </label>
          )}
          <label className="field"><span>Course</span>
            {courses.length > 0 ? (
              <select value={courseCode} onChange={(e) => setCourseCode(e.target.value)}>
                <option value="">Not specified</option>
                {courses.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
              </select>
            ) : (
              <input type="text" value={courseCode} placeholder="e.g. CS-301" onChange={(e) => setCourseCode(e.target.value)} />
            )}
          </label>
          <label className="field"><span>Faculty member{feedback ? " (required)" : " (optional)"}</span>
            {instructors.length > 0 ? (
              <select value={facultyKey} onChange={(e) => setFacultyKey(e.target.value)}>
                <option value="">{feedback ? "Choose…" : "Not specified"}</option>
                {instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            ) : (
              <input type="text" value={facultyKey} placeholder="Full name" onChange={(e) => setFacultyKey(e.target.value)} />
            )}
          </label>
          <label className="field"><span>Semester</span>
            <input type="text" value={semester} placeholder="e.g. Fall 2025" onChange={(e) => setSemester(e.target.value)} />
          </label>
          <button type="submit" className="btn primary" disabled={uploading || !files.some((f) => f.status !== "Done")}>
            {uploading ? "Reading and indexing…" : "Upload and index"}
          </button>
        </form>
      ) : (
        <p className="muted small">Your account has read-only access. You can chat with the documents but not upload or delete them.</p>
      )}

      <div className="rag-doclist">
        {docs.length === 0 ? (
          <div className="empty">No documents yet.</div>
        ) : (
          docs.map((d) => (
            <div key={d.id} className="rag-doc">
              <div>
                <span className={`pill ${d.doc_type === "course_outline" ? "neutral" : "warn"}`}>{KIND[d.doc_type] || d.doc_type}</span>{" "}
                <button type="button" className="rag-linkbtn" onClick={() => onOpen(d.id)}>{d.title}</button>
              </div>
              {canWrite && (
                <button type="button" className={`btn small${confirmId === d.id ? " danger" : ""} del`} aria-label={`Delete ${d.title}`} onClick={() => remove(d)}>
                  {confirmId === d.id ? "Confirm" : "Delete"}
                </button>
              )}
              <div className="meta muted small">
                {[d.course_code, d.instructor_name, d.semester, d.num_pages ? `${d.num_pages} ${d.num_pages === 1 ? "page" : "pages"}` : null, `${d.num_chunks} passages`].filter(Boolean).join(", ")}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
