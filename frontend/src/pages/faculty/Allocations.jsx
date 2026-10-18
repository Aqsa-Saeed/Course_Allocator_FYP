import { api } from "../../api.js";
import { Card, Loading, Notice, PageHeader, StatusPill, Table, useLoad } from "../../components/ui.jsx";

export default function Allocations() {
  const { data: rows, loading, error } = useLoad(() => api.get("/faculty/me/allocations"));

  return (
    <>
      <PageHeader title="My allocations" subtitle="Sections your coordinator has confirmed for you" />
      <Notice>{error?.message}</Notice>
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            rows={rows}
            empty="No sections have been allocated to you yet."
            columns={[
              { header: "Semester", render: (a) => a.semester },
              { header: "Course", render: (a) => `${a.course_code} ${a.course_title}` },
              { header: "Section", render: (a) => a.section_label },
              { header: "Status", render: (a) => <StatusPill status={a.status} /> },
            ]}
          />
        )}
      </Card>
    </>
  );
}
