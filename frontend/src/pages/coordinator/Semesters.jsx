import { useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, Field, Loading, Modal, Notice, PageHeader, Pill, Table, useLoad,
} from "../../components/ui.jsx";

function AddSemester({ onClose, onSaved }) {
  const [name, setName] = useState("Spring");
  const [year, setYear] = useState(new Date().getFullYear() + 1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const save = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/semesters", { name, year: Number(year) });
      onSaved();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal
      title="Add semester"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={save} disabled={busy}>Add</Button>
        </>
      }
    >
      <form onSubmit={save}>
        <Notice>{error}</Notice>
        <div className="form-row">
          <Field label="Term">
            <select value={name} onChange={(e) => setName(e.target.value)}>
              <option>Spring</option>
              <option>Fall</option>
            </select>
          </Field>
          <Field label="Year">
            <input type="number" min="2000" max="2100" value={year} onChange={(e) => setYear(e.target.value)} required />
          </Field>
        </div>
      </form>
    </Modal>
  );
}

export default function Semesters() {
  const { canWrite } = useAuth();
  const list = useLoad(() => api.get("/semesters"));
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if (list.loading && !list.data) return <Loading />;
  if (list.error) return <Notice>{list.error.message}</Notice>;

  const run = async (action, success) => {
    setError("");
    setMessage("");
    try {
      await action();
      setMessage(success);
      list.reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { header: "Semester", render: (s) => `${s.name} ${s.year}` },
    { header: "Status", render: (s) => (
      <span className="actions">
        {s.is_active && <Pill tone="ok">Active</Pill>}
        {s.is_locked && <Pill tone="warn">Locked</Pill>}
        {!s.is_active && !s.is_locked && <span className="muted">—</span>}
      </span>
    ) },
  ];
  if (canWrite) {
    columns.push({
      header: "",
      className: "num",
      render: (s) => (
        <span className="actions" style={{ justifyContent: "flex-end" }}>
          {!s.is_active && (
            <Button small onClick={() => run(() => api.patch(`/semesters/${s.id}`, { is_active: true }), `${s.name} ${s.year} is now the active semester.`)}>
              Make active
            </Button>
          )}
          <Button small onClick={() => run(() => api.patch(`/semesters/${s.id}`, { is_locked: !s.is_locked }), `${s.name} ${s.year} ${s.is_locked ? "unlocked" : "locked"}.`)}>
            {s.is_locked ? "Unlock" : "Lock"}
          </Button>
          <Button small variant="danger" onClick={() => window.confirm(`Delete ${s.name} ${s.year}?`) && run(() => api.del(`/semesters/${s.id}`), `Deleted ${s.name} ${s.year}.`)}>
            Delete
          </Button>
        </span>
      ),
    });
  }

  return (
    <>
      <PageHeader title="Semesters" subtitle="The active semester is the one being allocated; locked semesters are frozen">
        {canWrite && <Button variant="primary" onClick={() => setAdding(true)}>Add semester</Button>}
      </PageHeader>
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>
      <Card><Table rows={list.data} columns={columns} /></Card>
      {adding && (
        <AddSemester
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            setMessage("Semester added.");
            list.reload();
          }}
        />
      )}
    </>
  );
}
