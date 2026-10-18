import { Fragment, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import {
  Button, Card, ErrorNotice, Field, Loading, Notice, PageHeader, Pill, ScoreBar, formatTime, useLoad,
} from "../../components/ui.jsx";

const pct = (n) => `${Math.round(n * 100)}%`;

function Breakdown({ candidate }) {
  return (
    <div className="why">
      <p>{candidate.explanation}</p>
      <div className="breakdown">
        <span className="head">Signal</span>
        <span className="head">Strength</span>
        <span className="head">Value</span>
        <span className="head">Adds</span>
        {candidate.components.map((c) => (
          <Fragment key={c.key}>
            <span>{c.label} <span className="muted">({pct(c.weight)})</span></span>
            <ScoreBar value={c.value} />
            <span>{c.value.toFixed(2)}</span>
            <span>+{c.contribution.toFixed(3)}</span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}

export default function Rankings() {
  const { canWrite } = useAuth();
  const [params, setParams] = useSearchParams();
  const sectionId = params.get("section") || "";
  const [openId, setOpenId] = useState(null);
  const [limit, setLimit] = useState(10);   // show the top 10 first; "Show all" asks for up to 50
  const [otherId, setOtherId] = useState("");
  const [error, setError] = useState(null);
  const [message, setMessage] = useState("");

  const semester = useLoad(() => api.get("/semesters/active"));
  const sections = useLoad(
    () => (semester.data ? api.get("/sections", { semester_id: semester.data.id, limit: 500 }) : []),
    [semester.data?.id]
  );
  const result = useLoad(
    () => (sectionId ? api.get(`/sections/${sectionId}/recommendations`, { limit }) : null),
    [sectionId, limit]
  );
  const current = useLoad(() => (sectionId ? api.get("/allocations", { section_id: sectionId }) : []), [sectionId]);
  const instructors = useLoad(() => (canWrite ? api.get("/instructors", { limit: 200 }) : []), [canWrite]);

  const choose = (event) => {
    setOpenId(null);
    setLimit(10);
    setOtherId("");
    setError(null);
    setMessage("");
    setParams(event.target.value ? { section: event.target.value } : {});
  };

  const refresh = () => {
    result.reload();
    current.reload();
  };

  // Try to allocate. If the server refuses, it lists every conflict and nothing is saved.
  // Either way we reload, so the screen shows the true current state.
  const allocate = async (instructorId, name) => {
    setError(null);
    setMessage("");
    try {
      await api.post("/allocations", { section_id: Number(sectionId), instructor_id: instructorId });
      setMessage(`Allocated ${name} to ${result.data.course_code} section ${result.data.section_label}.`);
      setOtherId("");
    } catch (err) {
      setError(err);
    }
    refresh();
  };

  const cancelAllocation = async (allocation) => {
    if (!window.confirm(`Cancel the allocation of ${allocation.instructor_name}?`)) return;
    setError(null);
    setMessage("");
    try {
      await api.post(`/allocations/${allocation.id}/cancel`);
      setMessage(`Cancelled ${allocation.instructor_name}'s allocation.`);
    } catch (err) {
      setError(err);
    }
    refresh();
  };

  if (semester.loading) return <Loading />;
  if (semester.error) return <Notice>{semester.error.message}</Notice>;

  const data = result.data;
  const allocated = current.data?.[0];
  const otherName = instructors.data?.find((i) => i.id === Number(otherId))?.name;

  return (
    <>
      <PageHeader
        title="Instructor rankings"
        subtitle={`${semester.data.name} ${semester.data.year} · pick a section to see who fits best`}
      />

      <ErrorNotice error={error} onClose={() => setError(null)} />
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <Card>
        <Field label="Section">
          <select value={sectionId} onChange={choose} style={{ maxWidth: 480 }}>
            <option value="">Choose a section…</option>
            {(sections.data || []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.course_code} {s.course_title} — Section {s.section_label}
              </option>
            ))}
          </select>
        </Field>
      </Card>

      {sectionId && result.loading && !data && <Loading>Ranking instructors…</Loading>}
      <Notice>{result.error?.message}</Notice>

      {allocated && (
        <Card
          title="Allocated"
          actions={canWrite && <Button small variant="danger" onClick={() => cancelAllocation(allocated)}>Cancel allocation</Button>}
        >
          <p style={{ margin: 0 }}>
            <strong>{allocated.instructor_name}</strong>{" "}
            <span className="muted">
              · confirmed {formatTime(allocated.allocated_at)}
              {allocated.score != null && ` · ranking score ${allocated.score.toFixed(3)}`}
            </span>
          </p>
          {canWrite && <p className="muted small" style={{ margin: "8px 0 0" }}>Cancel this allocation to choose someone else.</p>}
        </Card>
      )}

      {data && (
        <>
          <Card
            title={`${data.course_code} ${data.course_title} · Section ${data.section_label}`}
            actions={
              <>
                <span className="muted small">
                  {limit === 10 && data.candidates.length === 10 ? "Top 10" : `${data.candidates.length} eligible`}
                </span>
                {limit === 10 && data.candidates.length === 10 && (
                  <Button small onClick={() => setLimit(50)}>Show all</Button>
                )}
                {limit === 50 && <Button small onClick={() => setLimit(10)}>Show top 10</Button>}
              </>
            }
          >
            {data.message && <Notice tone="info">{data.message}</Notice>}
            {data.candidates.length > 0 && (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Instructor</th>
                      <th>Score</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.candidates.map((c) => (
                      <Fragment key={c.instructor_id}>
                        <tr>
                          <td>{c.rank}</td>
                          <td>
                            {c.instructor_name}
                            {c.academic_rank && <div className="muted small">{c.academic_rank}</div>}
                          </td>
                          <td>
                            <div className="score-cell">
                              <ScoreBar value={c.score} />
                              <strong>{c.score.toFixed(3)}</strong>
                            </div>
                          </td>
                          <td className="num">
                            <span className="actions" style={{ justifyContent: "flex-end" }}>
                              <Button small onClick={() => setOpenId(openId === c.instructor_id ? null : c.instructor_id)}>
                                {openId === c.instructor_id ? "Hide why" : "Why?"}
                              </Button>
                              {allocated?.instructor_id === c.instructor_id && <Pill tone="ok">Allocated</Pill>}
                              {canWrite && !allocated && (
                                <Button small variant="primary" onClick={() => allocate(c.instructor_id, c.instructor_name)}>
                                  Allocate
                                </Button>
                              )}
                            </span>
                          </td>
                        </tr>
                        {openId === c.instructor_id && (
                          <tr>
                            <td />
                            <td colSpan={3}><Breakdown candidate={c} /></td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {canWrite && !allocated && (
            <Card title="Choose another instructor">
              <p className="muted small" style={{ marginTop: 0 }}>
                Pick anyone in the department. If they break a policy, the allocation is blocked and you will see why.
              </p>
              <div className="form-row">
                <Field label="Instructor">
                  <select value={otherId} onChange={(e) => setOtherId(e.target.value)}>
                    <option value="">Choose an instructor…</option>
                    {(instructors.data || []).map((i) => (
                      <option key={i.id} value={i.id}>{i.name}{i.status === "on_leave" ? " (on leave)" : ""}</option>
                    ))}
                  </select>
                </Field>
                <Button variant="primary" disabled={!otherId} onClick={() => allocate(Number(otherId), otherName)}>
                  Allocate
                </Button>
              </div>
            </Card>
          )}

          {data.excluded.length > 0 && (
            <Card>
              <details className="excluded">
                <summary>{data.excluded.length} instructor{data.excluded.length === 1 ? "" : "s"} not eligible</summary>
                <ul>
                  {data.excluded.map((e) => (
                    <li key={e.instructor_id}>
                      <strong>{e.instructor_name}</strong> <span className="muted">· {e.reason}</span>
                    </li>
                  ))}
                </ul>
              </details>
            </Card>
          )}
        </>
      )}
    </>
  );
}
