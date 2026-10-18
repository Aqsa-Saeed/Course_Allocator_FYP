import { useState } from "react";
import { api } from "../../api.js";
import { Card, Loading, Notice, PageHeader, Pill, Table, formatTime, useLoad } from "../../components/ui.jsx";

const ACTIONS = [
  "allocation_confirmed", "allocation_cancelled", "ranking_settings_updated",
  "preference_submitted", "preference_withdrawn", "preference_approved", "preference_rejected",
];
const TONES = {
  allocation_confirmed: "ok", allocation_cancelled: "warn",
  preference_approved: "ok", preference_rejected: "danger", preference_withdrawn: "warn",
};
const label = (action) => action.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export default function AuditLog() {
  const [action, setAction] = useState("");
  const logs = useLoad(() => api.get("/audit-logs", { action, limit: 200 }), [action]);

  return (
    <>
      <PageHeader title="Audit log" subtitle="Who changed what, and when" />
      <div className="toolbar">
        <select aria-label="Action" value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="">All actions</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{label(a)}</option>)}
        </select>
      </div>
      <Notice>{logs.error?.message}</Notice>
      <Card>
        {logs.loading && !logs.data ? (
          <Loading />
        ) : (
          <Table
            rows={logs.data}
            empty="No audit entries yet."
            columns={[
              { header: "When", className: "nowrap", render: (l) => formatTime(l.timestamp) },
              { header: "Who", render: (l) => l.actor_username },
              { header: "Action", render: (l) => <Pill tone={TONES[l.action] || "neutral"}>{label(l.action)}</Pill> },
              { header: "Details", render: (l) => l.details },
            ]}
          />
        )}
      </Card>
    </>
  );
}
