import { useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, Loading, Notice, PageHeader, StatusPill, Table, useLoad,
} from "../../components/ui.jsx";

const TABS = [
  ["pending", "Pending"],
  ["approved", "Approved"],
  ["rejected", "Rejected"],
  ["all", "All"],
];

export default function Review() {
  const { canWrite } = useAuth();
  const prefs = useLoad(() => api.get("/preferences", { limit: 500 }));
  const [tab, setTab] = useState("pending");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if (prefs.loading && !prefs.data) return <Loading />;
  if (prefs.error) return <Notice>{prefs.error.message}</Notice>;

  const all = prefs.data;
  const count = (status) => (status === "all" ? all.length : all.filter((p) => p.approval_status === status).length);
  const needle = search.trim().toLowerCase();
  const rows = all
    .filter((p) => tab === "all" || p.approval_status === tab)
    .filter((p) => !needle || `${p.instructor_name} ${p.course_code} ${p.course_title}`.toLowerCase().includes(needle));
  const semester = all[0]?.semester;

  const decide = async (preference, decision) => {
    setError("");
    setMessage("");
    try {
      await api.put(`/preferences/${preference.id}/${decision === "approved" ? "approve" : "reject"}`);
      setMessage(`${decision === "approved" ? "Approved" : "Rejected"}: ${preference.instructor_name} → ${preference.course_code}`);
      prefs.reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { header: "Course", render: (p) => `${p.course_code} ${p.course_title}` },
    { header: "Instructor", render: (p) => p.instructor_name },
    { header: "Choice", render: (p) => `#${p.priority_rank}` },
    { header: "Status", render: (p) => <StatusPill status={p.approval_status} /> },
  ];
  if (canWrite) {
    columns.push({
      header: "",
      className: "num",
      render: (p) => (
        <span className="actions" style={{ justifyContent: "flex-end" }}>
          {p.approval_status !== "approved" && (
            <Button small variant="primary" onClick={() => decide(p, "approved")}>Approve</Button>
          )}
          {p.approval_status !== "rejected" && (
            <Button small onClick={() => decide(p, "rejected")}>Reject</Button>
          )}
        </span>
      ),
    });
  }

  return (
    <>
      <PageHeader
        title="Preference review"
        subtitle={`${semester ? semester + " · " : ""}${canWrite ? "approve or reject what faculty requested" : "read-only view"}`}
      />
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <div className="toolbar">
        <div className="tabs" role="tablist">
          {TABS.map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={tab === key}
              className={`tab${tab === key ? " active" : ""}`}
              onClick={() => setTab(key)}
            >
              {label}
              <span className="count">{count(key)}</span>
            </button>
          ))}
        </div>
        <input type="search" placeholder="Search instructor or course…" value={search}
               aria-label="Search" onChange={(e) => setSearch(e.target.value)} />
      </div>

      <Card>
        <Table rows={rows} columns={columns} empty="No requests match." />
      </Card>
    </>
  );
}
