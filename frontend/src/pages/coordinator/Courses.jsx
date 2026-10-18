import { useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, Field, Loading, Modal, Notice, PageHeader, Table, useLoad,
} from "../../components/ui.jsx";

function CourseForm({ course, programs, onClose, onSaved }) {
  const [form, setForm] = useState({
    code: course?.code || "",
    title: course?.title || "",
    program_id: course?.program_id || programs[0]?.id || "",
    credit_hours: course?.credit_hours || 3,
    requirements_text: course?.requirements_text || "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  const save = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const body = {
      code: form.code.trim(),
      title: form.title.trim(),
      program_id: Number(form.program_id),
      credit_hours: Number(form.credit_hours),
      requirements_text: form.requirements_text.trim() || null,
    };
    try {
      const saved = course ? await api.patch(`/courses/${course.id}`, body) : await api.post("/courses", body);
      onSaved(saved);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal
      title={course ? "Edit course" : "Add course"}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={save} disabled={busy}>Save</Button>
        </>
      }
    >
      <form onSubmit={save}>
        <Notice>{error}</Notice>
        <div className="form-row" style={{ marginBottom: 14 }}>
          <Field label="Code"><input type="text" value={form.code} onChange={set("code")} required /></Field>
          <Field label="Credit hours">
            <input type="number" min="1" max="6" value={form.credit_hours} onChange={set("credit_hours")} required />
          </Field>
        </div>
        <Field label="Title"><input type="text" value={form.title} onChange={set("title")} required /></Field>
        <Field label="Program">
          <select value={form.program_id} onChange={set("program_id")} required>
            {programs.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </Field>
        <Field label="Requirements" hint="Topics taught and the expertise an instructor needs. Changing this clears the course's embedding; re-run generate_embeddings afterwards.">
          <textarea value={form.requirements_text} onChange={set("requirements_text")} />
        </Field>
      </form>
    </Modal>
  );
}

function CourseDetail({ course, allCourses, canWrite, onClose, onEdit, onDelete }) {
  const prereqs = useLoad(() => api.get(`/courses/${course.id}/prerequisites`), [course.id]);
  const [pick, setPick] = useState("");
  const [error, setError] = useState("");

  const add = async () => {
    setError("");
    try {
      await api.post(`/courses/${course.id}/prerequisites`, { prerequisite_course_id: Number(pick) });
      setPick("");
      prereqs.reload();
    } catch (err) {
      setError(err.message);
    }
  };
  const remove = async (id) => {
    setError("");
    try {
      await api.del(`/courses/${course.id}/prerequisites/${id}`);
      prereqs.reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const current = prereqs.data || [];
  const candidates = allCourses.filter(
    (c) => c.id !== course.id && !current.some((p) => p.prerequisite_course_id === c.id)
  );

  return (
    <Modal
      title={`${course.code} ${course.title}`}
      onClose={onClose}
      footer={
        <>
          {canWrite && <Button variant="danger" onClick={onDelete}>Delete</Button>}
          {canWrite && <Button onClick={onEdit}>Edit</Button>}
          <Button onClick={onClose}>Close</Button>
        </>
      }
    >
      <p className="muted small">{course.credit_hours} credit hours</p>
      <p>{course.requirements_text || <span className="muted">No requirements text.</span>}</p>
      <h3 style={{ fontSize: 15, margin: "18px 0 8px" }}>Prerequisites</h3>
      <Notice>{error}</Notice>
      {prereqs.loading && !prereqs.data ? <Loading /> : current.length === 0 ? (
        <p className="muted small">None.</p>
      ) : (
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          {current.map((p) => (
            <li key={p.prerequisite_course_id}>
              {p.prerequisite_code} {p.prerequisite_title}{" "}
              {canWrite && <Button small onClick={() => remove(p.prerequisite_course_id)}>Remove</Button>}
            </li>
          ))}
        </ul>
      )}
      {canWrite && (
        <div className="form-row" style={{ marginTop: 12 }}>
          <Field label="Add a prerequisite">
            <select value={pick} onChange={(e) => setPick(e.target.value)}>
              <option value="">Choose a course…</option>
              {candidates.map((c) => <option key={c.id} value={c.id}>{c.code} {c.title}</option>)}
            </select>
          </Field>
          <Button onClick={add} disabled={!pick}>Add</Button>
        </div>
      )}
    </Modal>
  );
}

export default function Courses() {
  const { canWrite } = useAuth();
  const courses = useLoad(() => api.get("/courses", { limit: 200 }));
  const programs = useLoad(() => api.get("/programs"));
  const [search, setSearch] = useState("");
  const [programId, setProgramId] = useState("");
  const [viewing, setViewing] = useState(null);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if ((courses.loading && !courses.data) || (programs.loading && !programs.data)) return <Loading />;
  const failure = courses.error || programs.error;
  if (failure) return <Notice>{failure.message}</Notice>;

  const programName = (id) => programs.data.find((p) => p.id === id)?.name || "";
  const needle = search.trim().toLowerCase();
  const rows = courses.data
    .filter((c) => !programId || c.program_id === Number(programId))
    .filter((c) => !needle || `${c.code} ${c.title}`.toLowerCase().includes(needle));

  const remove = async (course) => {
    if (!window.confirm(`Delete ${course.code} ${course.title}?`)) return;
    setError("");
    setMessage("");
    try {
      await api.del(`/courses/${course.id}`);
      setViewing(null);
      setMessage(`Deleted ${course.code}.`);
      courses.reload();
    } catch (err) {
      setViewing(null);
      setError(err.message);
    }
  };

  return (
    <>
      <PageHeader title="Courses" subtitle={`${courses.data.length} courses · click a row for details`}>
        {canWrite && <Button variant="primary" onClick={() => setEditing({})}>Add course</Button>}
      </PageHeader>
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <div className="toolbar">
        <input type="search" placeholder="Search code or title…" aria-label="Search" value={search}
               onChange={(e) => setSearch(e.target.value)} />
        <select aria-label="Program" value={programId} onChange={(e) => setProgramId(e.target.value)}>
          <option value="">All programs</option>
          {programs.data.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      <Card>
        <Table
          rows={rows}
          empty="No courses match."
          onRowClick={setViewing}
          columns={[
            { header: "Code", className: "nowrap", render: (c) => c.code },
            { header: "Title", render: (c) => c.title },
            { header: "Program", render: (c) => programName(c.program_id) },
            { header: "Credits", className: "num", render: (c) => c.credit_hours },
          ]}
        />
      </Card>

      {viewing && (
        <CourseDetail
          course={viewing}
          allCourses={courses.data}
          canWrite={canWrite}
          onClose={() => setViewing(null)}
          onEdit={() => { setEditing(viewing); setViewing(null); }}
          onDelete={() => remove(viewing)}
        />
      )}
      {editing && (
        <CourseForm
          course={editing.id ? editing : null}
          programs={programs.data}
          onClose={() => setEditing(null)}
          onSaved={(saved) => {
            setMessage(`Saved ${saved.code}.`);
            setEditing(null);
            courses.reload();
          }}
        />
      )}
    </>
  );
}
