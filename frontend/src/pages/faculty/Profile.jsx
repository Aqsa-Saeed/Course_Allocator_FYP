import { api } from "../../api.js";
import { Card, Loading, Notice, PageHeader, StatusPill, useLoad } from "../../components/ui.jsx";

export default function Profile() {
  const { data: me, loading, error } = useLoad(() => api.get("/faculty/me"));

  if (loading) return <Loading />;
  if (error) return <Notice>{error.message}</Notice>;

  const details = [
    ["Department", me.department],
    ["Academic rank", me.academic_rank || "—"],
    ["Qualification", me.highest_qualification || "—"],
    ["Email", me.email],
    ["Specializations", me.qualifications_text || "—"],
  ];

  return (
    <>
      <PageHeader title={`Welcome, ${me.name}`} subtitle={me.department} />
      <Card title="My profile">
        <table>
          <tbody>
            {details.map(([label, value]) => (
              <tr key={label}>
                <th scope="row" style={{ width: 180 }}>{label}</th>
                <td>{value}</td>
              </tr>
            ))}
            <tr>
              <th scope="row">Status</th>
              <td><StatusPill status={me.status} /></td>
            </tr>
          </tbody>
        </table>
        {me.status === "on_leave" && (
          <p className="muted small" style={{ marginTop: 12 }}>
            While you are on leave you cannot submit course preferences and are not offered for allocation.
          </p>
        )}
      </Card>
    </>
  );
}
