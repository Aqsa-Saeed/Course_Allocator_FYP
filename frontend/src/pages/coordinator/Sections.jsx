import { useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, Field, Loading, Modal, Notice, PageHeader, Pill, Table, useLoad,
} from "../../components/ui.jsx";

function AddSection({ semester, courses, onClose, onSaved }) {
  const [courseId, setCourseId] = useState("");
  const [label, setLabel] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const save = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/sections", {
        course_id: Number(courseId),
        semester_id: semester.id,
        section_label: label.trim(),
      });
      onSaved();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal
      title={`Add a section to ${semester.name} ${semester.year}`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={save} disabled={busy || !courseId || !label.trim()}>Add</Button>
        </>
      }
    >
      <form onSubmit={save}>
        <Notice>{error}</Notice>
        <Field label="Course">
          <select value={courseId} onChange={(e) => setCourseId(e.target.value)} required>
            <option value="">Choose a course…</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.code} {c.title}</option>)}
          </select>
        </Field>
        <Field label="Section label" hint="For example A, B or 01">
          <input type="text" maxLength={10} value={label} onChange={(e) => setLabel(e.target.value)} required />
        </Field>
      </form>
    </Modal>
  );
}

export default function Sections() {
  const { canWrite } = useAuth();
  const semesters = useLoad(() => api.get("/semesters"));
  const courses = useLoad(() => api.get("/courses", { limit: 200 }));
  const [semesterId, setSemesterId] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const chosen = semesterId
    ? semesters.data?.find((s) => s.id === Number(semesterId))
    : semesters.data?.find((s) => s.is_active) || semesters.data?.[0];
  const sections = useLoad(
    () => (chosen ? api.get("/sections", { semester_id: chosen.id, limit: 500 }) : []),
    [chosen?.id]
  );

  if ((semesters.loading && !semesters.data) || (courses.loading && !courses.data)) return <Loading />;
  const failure = semesters.error || courses.error || sections.error;
  if (failure) return <Notice>{failure.message}</Notice>;
  if (!chosen) return <Notice tone="info">No semesters exist yet.</Notice>;

  const remove = async (section) => {
    if (!window.confirm(`Delete ${section.course_code} section ${section.section_label}?`)) return;
    setError("");
    setMessage("");
    try {
      await api.del(`/sections/${section.id}`);
      setMessage(`Deleted ${section.course_code} section ${section.section_label}.`);
      sections.reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { header: "Course", render: (s) => `${s.course_code} ${s.course_title}` },
    { header: "Section", render: (s) => s.section_label },
  ];
  if (canWrite) {
    columns.push({
      header: "",
      className: "num",
      render: (s) => <Button small variant="danger" onClick={() => remove(s)}>Delete</Button>,
    });
  }

  return (
    <>
      <PageHeader title="Sections" subtitle={`${sections.data?.length ?? 0} sections in ${chosen.name} ${chosen.year}`}>
        {canWrite && !chosen.is_locked && <Button variant="primary" onClick={() => setAdding(true)}>Add section</Button>}
      </PageHeader>
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <div className="toolbar">
        <select aria-label="Semester" value={chosen.id} onChange={(e) => setSemesterId(e.target.value)}>
          {semesters.data.map((s) => (
            <option key={s.id} value={s.id}>{s.name} {s.year}{s.is_active ? " (active)" : ""}</option>
          ))}
        </select>
        {chosen.is_locked && <Pill tone="warn">Locked: sections cannot be changed</Pill>}
      </div>

      <Card>
        {sections.loading && !sections.data ? <Loading /> : <Table rows={sections.data} columns={columns} empty="No sections in this semester." />}
      </Card>

      {adding && (
        <AddSection
          semester={chosen}
          courses={courses.data}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            setMessage("Section added.");
            sections.reload();
          }}
        />
      )}
    </>
  );
}
