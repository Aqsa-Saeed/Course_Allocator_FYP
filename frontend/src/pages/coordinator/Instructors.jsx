import { useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, Field, Loading, Modal, Notice, PageHeader, StatusPill, Table, useLoad,
} from "../../components/ui.jsx";

const EMPTY = {
  name: "", email: "", academic_rank: "", highest_qualification: "", status: "active", qualifications_text: "",
};

function InstructorForm({ instructor, onClose, onSaved }) {
  const [form, setForm] = useState(instructor ? { ...EMPTY, ...instructor } : EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  const save = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const body = {
      name: form.name.trim(),
      email: form.email.trim(),
      academic_rank: form.academic_rank.trim() || null,
      highest_qualification: form.highest_qualification.trim() || null,
      status: form.status,
      qualifications_text: form.qualifications_text.trim() || null,
    };
    try {
      const saved = instructor
        ? await api.patch(`/instructors/${instructor.id}`, body)
        : await api.post("/instructors", body);
      onSaved(saved);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal
      title={instructor ? "Edit instructor" : "Add instructor"}
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
        <Field label="Name"><input type="text" value={form.name} onChange={set("name")} required /></Field>
        <Field label="Email"><input type="email" value={form.email} onChange={set("email")} required /></Field>
        <div className="form-row" style={{ marginBottom: 14 }}>
          <Field label="Academic rank">
            <input type="text" list="ranks" value={form.academic_rank} onChange={set("academic_rank")} />
            <datalist id="ranks">
              {["Professor", "Associate Professor", "Assistant Professor", "Senior Lecturer", "Lecturer", "Assistant Lecturer"]
                .map((r) => <option key={r} value={r} />)}
            </datalist>
          </Field>
          <Field label="Qualification">
            <input type="text" list="quals" value={form.highest_qualification} onChange={set("highest_qualification")} />
            <datalist id="quals">
              {["PhD", "MS/M.Phil", "BSCS/MCS"].map((r) => <option key={r} value={r} />)}
            </datalist>
          </Field>
          <Field label="Status">
            <select value={form.status} onChange={set("status")}>
              <option value="active">Active</option>
              <option value="on_leave">On leave</option>
            </select>
          </Field>
        </div>
        <Field label="Specializations" hint="Comma separated. Changing this clears the instructor's embedding; re-run generate_embeddings afterwards.">
          <textarea value={form.qualifications_text} onChange={set("qualifications_text")} />
        </Field>
      </form>
    </Modal>
  );
}

export default function Instructors() {
  const { canWrite } = useAuth();
  const list = useLoad(() => api.get("/instructors", { limit: 200 }));
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [editing, setEditing] = useState(null); // null = closed, {} = new, instructor = edit
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if (list.loading && !list.data) return <Loading />;
  if (list.error) return <Notice>{list.error.message}</Notice>;

  const needle = search.trim().toLowerCase();
  const rows = list.data
    .filter((i) => !status || i.status === status)
    .filter((i) => !needle || `${i.name} ${i.qualifications_text || ""}`.toLowerCase().includes(needle));

  const remove = async (instructor) => {
    if (!window.confirm(`Delete ${instructor.name}?`)) return;
    setError("");
    setMessage("");
    try {
      await api.del(`/instructors/${instructor.id}`);
      setMessage(`Deleted ${instructor.name}.`);
      list.reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { header: "Name", render: (i) => <>{i.name}<div className="muted small">{i.email}</div></> },
    { header: "Rank", render: (i) => i.academic_rank || "—" },
    { header: "Qualification", render: (i) => i.highest_qualification || "—" },
    { header: "Status", render: (i) => <StatusPill status={i.status} /> },
    { header: "Specializations", render: (i) => i.qualifications_text || "—" },
  ];
  if (canWrite) {
    columns.push({
      header: "",
      className: "nowrap",
      render: (i) => (
        <span className="actions">
          <Button small onClick={() => setEditing(i)}>Edit</Button>
          <Button small variant="danger" onClick={() => remove(i)}>Delete</Button>
        </span>
      ),
    });
  }

  return (
    <>
      <PageHeader title="Instructors" subtitle={`${list.data.length} in the department`}>
        {canWrite && <Button variant="primary" onClick={() => setEditing({})}>Add instructor</Button>}
      </PageHeader>
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <div className="toolbar">
        <input type="search" placeholder="Search name or specialization…" aria-label="Search" value={search}
               onChange={(e) => setSearch(e.target.value)} />
        <select aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="on_leave">On leave</option>
        </select>
      </div>

      <Card><Table rows={rows} columns={columns} empty="No instructors match." /></Card>

      {editing && (
        <InstructorForm
          instructor={editing.id ? editing : null}
          onClose={() => setEditing(null)}
          onSaved={(saved) => {
            setMessage(`Saved ${saved.name}.`);
            setEditing(null);
            list.reload();
          }}
        />
      )}
    </>
  );
}
