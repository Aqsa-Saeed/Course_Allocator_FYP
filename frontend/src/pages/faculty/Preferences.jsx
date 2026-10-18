import { useState } from "react";
import { api } from "../../api.js";
import {
  Button, Card, Field, Loading, Notice, PageHeader, StatusPill, Table, useLoad,
} from "../../components/ui.jsx";

const MAX_REQUESTS = 5;

export default function Preferences() {
  const offered = useLoad(() => api.get("/faculty/me/offered-courses"));
  const mine = useLoad(() => api.get("/faculty/me/preferences"));
  const [courseId, setCourseId] = useState("");
  const [rank, setRank] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = () => {
    offered.reload();
    mine.reload();
  };

  if ((offered.loading && !offered.data) || (mine.loading && !mine.data)) return <Loading />;
  const loadError = offered.error || mine.error;
  if (loadError) return <Notice>{loadError.message}</Notice>;

  const requests = mine.data;
  const available = offered.data.filter((c) => !c.requested);
  const usedRanks = new Set(requests.map((p) => p.priority_rank));
  const freeRanks = Array.from({ length: MAX_REQUESTS }, (_, i) => i + 1).filter((r) => !usedRanks.has(r));
  const full = requests.length >= MAX_REQUESTS;
  const semester = requests[0]?.semester;

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await api.post("/faculty/me/preferences", {
        course_id: Number(courseId),
        priority_rank: rank ? Number(rank) : null,
      });
      setMessage("Request submitted. It is pending review by your coordinator.");
      setCourseId("");
      setRank("");
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const withdraw = async (preference) => {
    setError("");
    setMessage("");
    try {
      await api.del(`/faculty/me/preferences/${preference.id}`);
      setMessage(`Withdrew your request for ${preference.course_code}.`);
      refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <PageHeader
        title="Course preferences"
        subtitle={`${semester ? semester + " · " : ""}${requests.length} of ${MAX_REQUESTS} requests used`}
      />
      <Notice onClose={() => setError("")}>{error}</Notice>
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <Card title="Request a course">
        {full ? (
          <p className="muted">You have used all {MAX_REQUESTS} requests. Withdraw a pending one to add another.</p>
        ) : (
          <form className="form-row" onSubmit={submit}>
            <Field label="Course">
              <select value={courseId} onChange={(e) => setCourseId(e.target.value)} required>
                <option value="">Choose a course…</option>
                {available.map((c) => (
                  <option key={c.course_id} value={c.course_id}>
                    {c.code} {c.title}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Priority">
              <select value={rank} onChange={(e) => setRank(e.target.value)}>
                <option value="">Next available</option>
                {freeRanks.map((r) => (
                  <option key={r} value={r}>
                    Choice {r}
                  </option>
                ))}
              </select>
            </Field>
            <Button variant="primary" type="submit" disabled={busy || !courseId}>
              Submit
            </Button>
          </form>
        )}
      </Card>

      <Card title="My requests">
        <Table
          rows={requests}
          empty="You have not requested any courses yet."
          columns={[
            { header: "Choice", render: (p) => `#${p.priority_rank}` },
            { header: "Course", render: (p) => `${p.course_code} ${p.course_title}` },
            { header: "Status", render: (p) => <StatusPill status={p.approval_status} /> },
            {
              header: "",
              className: "num",
              render: (p) =>
                p.approval_status === "pending" ? (
                  <Button small onClick={() => withdraw(p)}>Withdraw</Button>
                ) : null,
            },
          ]}
        />
      </Card>
    </>
  );
}
