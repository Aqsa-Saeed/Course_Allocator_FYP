import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, ErrorNotice, Loading, Notice, PageHeader, Pill, ScoreBar, Table, formatTime, useLoad,
} from "../../components/ui.jsx";

export default function Allocations() {
  const { canWrite } = useAuth();
  const [error, setError] = useState(null);
  const [message, setMessage] = useState("");

  const semester = useLoad(() => api.get("/semesters/active"));
  const sections = useLoad(
    () => (semester.data ? api.get("/sections", { semester_id: semester.data.id, limit: 500 }) : []),
    [semester.data?.id]
  );
  const allocations = useLoad(
    () => (semester.data ? api.get("/allocations", { semester_id: semester.data.id }) : []),
    [semester.data?.id]
  );
  const settings = useLoad(() => api.get("/settings/ranking"));

  const waiting = [semester, sections, allocations, settings].some((r) => r.loading && !r.data);
  if (waiting) return <Loading />;
  const failure = [semester, sections, allocations, settings].find((r) => r.error);
  if (failure) return <Notice>{failure.error.message}</Notice>;

  const done = allocations.data;
  const doneIds = new Set(done.map((a) => a.section_id));
  const open = sections.data.filter((s) => !doneIds.has(s.id));
  const cap = settings.data.max_courses_per_instructor;

  const perInstructor = {};
  done.forEach((a) => {
    perInstructor[a.instructor_id] = perInstructor[a.instructor_id] || { name: a.instructor_name, count: 0 };
    perInstructor[a.instructor_id].count += 1;
  });
  const workload = Object.entries(perInstructor)
    .map(([id, w]) => ({ id, ...w }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

  const cancel = async (allocation) => {
    if (!window.confirm(`Cancel ${allocation.instructor_name}'s allocation for ${allocation.course_code} section ${allocation.section_label}?`)) return;
    setError(null);
    setMessage("");
    try {
      await api.post(`/allocations/${allocation.id}/cancel`);
      setMessage(`Cancelled ${allocation.instructor_name}'s allocation for ${allocation.course_code} section ${allocation.section_label}.`);
    } catch (err) {
      setError(err);
    }
    allocations.reload();
  };

  const total = sections.data.length;
  const columns = [
    { header: "Course", render: (a) => <Link to={`/rankings?section=${a.section_id}`}>{a.course_code} {a.course_title}</Link> },
    { header: "Section", render: (a) => a.section_label },
    { header: "Instructor", render: (a) => a.instructor_name },
    { header: "Score", className: "num", render: (a) => (a.score == null ? "—" : a.score.toFixed(3)) },
    { header: "Confirmed", className: "nowrap", render: (a) => formatTime(a.allocated_at) },
  ];
  if (canWrite) {
    columns.push({
      header: "",
      className: "num",
      render: (a) => <Button small variant="danger" onClick={() => cancel(a)}>Cancel</Button>,
    });
  }

  return (
    <>
      <PageHeader
        title="Allocations"
        subtitle={`${semester.data.name} ${semester.data.year} · ${done.length} of ${total} sections allocated`}
      />
      <ErrorNotice error={error} onClose={() => setError(null)} />
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <Card>
        <ScoreBar value={total ? done.length / total : 0} />
        <p className="muted small" style={{ margin: "8px 0 0" }}>
          {open.length === 0 ? "Every section has an instructor." : `${open.length} section${open.length === 1 ? "" : "s"} still need an instructor.`}
        </p>
      </Card>

      <Card title="Allocated sections">
        <Table rows={done} columns={columns} empty="Nothing has been allocated yet." />
      </Card>

      <Card title="Workload this semester">
        <Table
          rows={workload}
          empty="No instructor has any sections yet."
          columns={[
            { header: "Instructor", render: (w) => w.name },
            { header: "Sections", className: "nowrap", render: (w) => `${w.count} of ${cap}` },
            { header: "", render: (w) => <ScoreBar value={w.count / cap} /> },
            { header: "", render: (w) => (w.count >= cap ? <Pill tone="warn">At the cap</Pill> : null) },
          ]}
        />
      </Card>

      <Card title={`Still unallocated (${open.length})`}>
        <Table
          rows={open}
          empty="Every section is allocated."
          columns={[
            { header: "Course", render: (s) => `${s.course_code} ${s.course_title}` },
            { header: "Section", render: (s) => s.section_label },
            { header: "", className: "num", render: (s) => <Link to={`/rankings?section=${s.id}`}>Find an instructor</Link> },
          ]}
        />
      </Card>

    </>
  );
}
