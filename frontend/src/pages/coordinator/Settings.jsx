import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAuth } from "../../auth.jsx";
import { Button, Card, ErrorNotice, Field, Loading, Notice, PageHeader, useLoad } from "../../components/ui.jsx";

const WEIGHTS = [
  ["weight_content_match", "Expertise match", "How closely their specializations fit the course"],
  ["weight_history", "Teaching history", "Semesters they taught this or a related course"],
  ["weight_recency", "Recent teaching", "How recently they taught it"],
  ["weight_feedback", "Student feedback", "Their average rating, smoothed"],
  ["weight_preference", "Instructor preference", "Whether they asked for the course"],
  ["weight_workload", "Workload balance", "Fewer sections already allocated scores higher"],
];

const toForm = (settings) => Object.fromEntries(Object.entries(settings).map(([k, v]) => [k, String(v)]));

export default function Settings() {
  const { canWrite } = useAuth();
  const settings = useLoad(() => api.get("/settings/ranking"));
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (settings.data) setForm(toForm(settings.data));
  }, [settings.data]);

  if (settings.error) return <Notice>{settings.error.message}</Notice>;
  if (!form) return <Loading />;

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const total = WEIGHTS.reduce((sum, [key]) => sum + (Number(form[key]) || 0), 0);

  const save = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const body = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, Number(v)]));
      await api.patch("/settings/ranking", body);
      setMessage("Settings saved. They apply to the next ranking and the next allocation.");
      settings.reload();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Policy settings"
        subtitle={canWrite ? "The rules for allocating and the weights behind the rankings" : "Read-only view"}
      />
      <ErrorNotice error={error} onClose={() => setError(null)} />
      <Notice tone="success" onClose={() => setMessage("")}>{message}</Notice>

      <form onSubmit={save}>
        <Card title="Policy limits">
          <p className="muted small" style={{ marginTop: 0 }}>
            These block an allocation. If a limit stops a choice you want to make, raise it here or pick someone else.
          </p>
          <div className="form-row">
            <Field label="Most sections per instructor" hint="1 to 10">
              <input type="number" min="1" max="10" step="1" value={form.max_courses_per_instructor}
                     onChange={set("max_courses_per_instructor")} disabled={!canWrite} />
            </Field>
            <Field label="Minimum feedback score" hint="Out of 5. Smoothed, so one low rating cannot decide it">
              <input type="number" min="0" max="5" step="0.1" value={form.min_feedback_score}
                     onChange={set("min_feedback_score")} disabled={!canWrite} />
            </Field>
          </div>
        </Card>

        <Card title="Ranking weights">
          <p className="muted small" style={{ marginTop: 0 }}>
            These shape the ranking but never block anyone. They do not need to add up to 1; each one is shown as a share of the total.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Signal</th><th>Weight (0 to 1)</th><th className="num">Share</th></tr>
              </thead>
              <tbody>
                {WEIGHTS.map(([key, label, hint]) => (
                  <tr key={key}>
                    <td>{label}<div className="muted small">{hint}</div></td>
                    <td style={{ width: 150 }}>
                      <input type="number" min="0" max="1" step="0.05" aria-label={`${label} weight`}
                             value={form[key]} onChange={set(key)} disabled={!canWrite} />
                    </td>
                    <td className="num">{total > 0 ? Math.round(((Number(form[key]) || 0) / total) * 100) : 0}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {canWrite && (
          <Button variant="primary" type="submit" disabled={busy}>{busy ? "Saving…" : "Save settings"}</Button>
        )}
      </form>
    </>
  );
}
