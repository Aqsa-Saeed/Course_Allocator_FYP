import { api } from "../../api.js";
import { Card, Loading, Notice, PageHeader, Table, useLoad } from "../../components/ui.jsx";

export default function History() {
  const { data: rows, loading, error } = useLoad(() => api.get("/faculty/me/history"));

  return (
    <>
      <PageHeader title="Teaching history" subtitle="Every section you have taught, newest first" />
      <Notice>{error?.message}</Notice>
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table
            rows={rows}
            rowKey={(r) => `${r.semester}-${r.course_code}-${r.section_label}`}
            empty="No teaching history on record."
            columns={[
              { header: "Semester", render: (r) => r.semester },
              { header: "Course", render: (r) => `${r.course_code} ${r.course_title}` },
              { header: "Section", render: (r) => r.section_label },
              {
                header: "Feedback",
                className: "num",
                render: (r) =>
                  r.feedback_score === null ? (
                    <span className="muted">Not collected yet</span>
                  ) : (
                    `${r.feedback_score.toFixed(2)} / 5`
                  ),
              },
            ]}
          />
        )}
      </Card>
    </>
  );
}
