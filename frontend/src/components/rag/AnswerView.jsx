import { useState } from "react";

export const KIND = { course_outline: "Course outline", faculty_feedback: "Faculty feedback" };

// Text with **bold** and [n] citation chips. Built from React elements, never raw HTML.
function Inline({ text, byN, onChip }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).filter(Boolean);
  return (
    <>
      {parts.map((part, i) => {
        const cite = /^\[(\d+)\]$/.exec(part);
        const bold = /^\*\*([^*]+)\*\*$/.exec(part);
        if (cite && byN[+cite[1]]) {
          const n = +cite[1];
          const s = byN[n];
          return (
            <button
              key={i}
              type="button"
              className={`rag-chip ${s.doc_type}`}
              title={`${s.title}${s.page ? `, page ${s.page}` : ""}`}
              aria-label={`Source ${n}: ${s.title}`}
              onClick={() => onChip(n)}
            >
              {n}
            </button>
          );
        }
        if (bold) return <strong key={i}>{bold[1]}</strong>;
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// Splits the answer into paragraphs and bullet / numbered lists.
function parseBlocks(answer) {
  const blocks = [];
  let list = null;
  for (const raw of answer.split("\n")) {
    const line = raw.trim();
    if (!line) { list = null; continue; }
    const li = /^([-*•]|\d+[.)])\s+(.*)$/.exec(line);
    if (li) {
      const ordered = /\d/.test(li[1]);
      if (!list || list.ordered !== ordered) {
        list = { type: ordered ? "ol" : "ul", ordered, items: [] };
        blocks.push(list);
      }
      list.items.push(li[2]);
    } else {
      list = null;
      blocks.push({ type: "p", text: line.replace(/^#+\s*/, "") });
    }
  }
  return blocks;
}

function SourceCard({ s, idPrefix, onOpen }) {
  const [open, setOpen] = useState(false);
  const meta = [
    KIND[s.doc_type], s.instructor_name, s.course_code, s.semester,
    s.page ? `page ${s.page}` : null, `match ${Math.round(s.score * 100)}%`,
  ].filter(Boolean).join(", ");
  return (
    <div id={`${idPrefix}-${s.n}`} className={`rag-src ${s.doc_type}`}>
      <span className={`rag-chip ${s.doc_type}`}>{s.n}</span>
      <div className="head">
        <button type="button" className="rag-linkbtn" onClick={() => onOpen(s.document_id, s.page)}>{s.title}</button>
        <span className="muted small">{meta}</span>
      </div>
      <p className={`text${open ? " open" : ""}`}>{s.snippet}</p>
      <button type="button" className="more" onClick={() => setOpen(!open)}>{open ? "Show less" : "Show more"}</button>
    </div>
  );
}

export default function AnswerView({ result, idPrefix, onOpen }) {
  const byN = Object.fromEntries(result.sources.map((s) => [s.n, s]));
  const cited = result.sources.filter((s) => s.cited);
  const rest = result.sources.filter((s) => !s.cited);

  const focusSource = (n) => {
    const card = document.getElementById(`${idPrefix}-${n}`);
    if (!card) return;
    const details = card.closest("details");
    if (details) details.open = true;
    card.scrollIntoView({ block: "nearest", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    card.classList.add("flash");
    setTimeout(() => card.classList.remove("flash"), 1400);
  };

  const auto = result.scope?.auto_detected;
  const autoNames = auto ? [...(auto.instructors || []), ...(auto.courses || [])] : [];

  return (
    <>
      <div className="rag-bubble">
        {parseBlocks(result.answer).map((b, i) =>
          b.type === "p" ? (
            <p key={i}><Inline text={b.text} byN={byN} onChip={focusSource} /></p>
          ) : (
            (b.type === "ol" ? <ol key={i}>{b.items.map((t, j) => <li key={j}><Inline text={t} byN={byN} onChip={focusSource} /></li>)}</ol>
              : <ul key={i}>{b.items.map((t, j) => <li key={j}><Inline text={t} byN={byN} onChip={focusSource} /></li>)}</ul>)
          )
        )}
      </div>

      {autoNames.length > 0 && (
        <div className="muted small">Searched only documents for {autoNames.join(", ")}, based on your question.</div>
      )}
      {result.warning && <div className="notice info" role="alert">{result.warning}</div>}

      {cited.length > 0 && (
        <div className="rag-sources" aria-label="Sources cited">
          {cited.map((s) => <SourceCard key={s.n} s={s} idPrefix={idPrefix} onOpen={onOpen} />)}
        </div>
      )}
      {rest.length > 0 && (
        <details className="rag-more" open={cited.length === 0}>
          <summary>
            {cited.length ? `${rest.length} more ${rest.length === 1 ? "passage" : "passages"} considered` : `Passages found (${rest.length})`}
          </summary>
          <div className="rag-sources">
            {rest.map((s) => <SourceCard key={s.n} s={s} idPrefix={idPrefix} onOpen={onOpen} />)}
          </div>
        </details>
      )}
    </>
  );
}
