import { useEffect, useRef, useState } from "react";
import { rag } from "../../rag/ragApi.js";
import AnswerView from "./AnswerView.jsx";

const TYPES = [["", "All"], ["course_outline", "Outlines"], ["faculty_feedback", "Feedback"]];

export default function ChatPanel({ meta, docs, onOpen }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [docType, setDocType] = useState("");
  const [instructorId, setInstructorId] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const logRef = useRef(null);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

  const instructors = (meta?.instructors || []).filter((i) => i.id != null);
  const courses = meta?.courses || [];

  async function send(text) {
    const question = (text ?? input).trim();
    if (!question || busy) return;
    setInput("");
    const history = messages.filter((m) => !m.error).slice(-8).map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: question }]);
    setBusy(true);
    try {
      const payload = { message: question, history };
      if (docType) payload.doc_type = docType;
      if (instructorId) payload.instructor_id = Number(instructorId);
      if (courseCode) payload.course_code = courseCode;
      const result = await rag.chat(payload);
      setMessages((m) => [...m, { role: "assistant", content: result.answer, result }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: e.message, error: true }]);
    } finally {
      setBusy(false);
    }
  }

  const examples = [];
  if (courses[0]) examples.push(`What topics and grading components does ${courses[0]} cover?`);
  if (meta?.instructors?.[0]) examples.push(`Summarize the student feedback about ${meta.instructors[0].name}.`);
  if (courses[0] && meta?.instructors?.[0]) examples.push(`Is ${meta.instructors[0].name} a good fit to teach ${courses[0]}?`);

  return (
    <div className="card rag-chatcard">
      <div className="rag-scope">
        <div className="tabs" role="group" aria-label="Document type">
          {TYPES.map(([value, label]) => (
            <button key={value} type="button" className={`tab${docType === value ? " active" : ""}`} aria-pressed={docType === value} onClick={() => setDocType(value)}>
              {label}
            </button>
          ))}
        </div>
        {instructors.length > 0 && (
          <select aria-label="Faculty member" value={instructorId} onChange={(e) => setInstructorId(e.target.value)}>
            <option value="">All faculty</option>
            {instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        )}
        {courses.length > 0 && (
          <select aria-label="Course" value={courseCode} onChange={(e) => setCourseCode(e.target.value)}>
            <option value="">All courses</option>
            {courses.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
        <span className="spacer" />
        {messages.length > 0 && <button type="button" className="btn small" onClick={() => setMessages([])}>New conversation</button>}
      </div>

      <div className="rag-log" ref={logRef} aria-live="polite">
        {messages.length === 0 && (
          <div className="rag-intro">
            <h2>Ask your documents</h2>
            <p>
              {docs.length
                ? "Answers come only from the files you uploaded, with a numbered reference for each claim."
                : "Upload a course outline or a faculty feedback file on the left, then ask a question here."}
            </p>
            {examples.map((q) => <button key={q} type="button" className="rag-example" onClick={() => send(q)}>{q}</button>)}
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="rag-msg user"><div className="rag-bubble">{m.content}</div></div>
          ) : (
            <div key={i} className="rag-msg bot">
              {m.error
                ? <div className="notice error" role="alert">Could not get an answer: {m.content}</div>
                : <AnswerView result={m.result} idPrefix={`rag-m${i}`} onOpen={onOpen} />}
            </div>
          )
        )}

        {busy && (
          <div className="rag-msg bot">
            <div className="rag-bubble"><span className="rag-typing" role="status" aria-label="Searching the documents"><i /><i /><i /></span></div>
          </div>
        )}
      </div>

      <div className="rag-composer">
        <textarea
          rows={1}
          value={input}
          placeholder="Ask about a course outline or faculty feedback"
          aria-label="Your question"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
        />
        <button type="button" className="btn primary" disabled={busy || !input.trim()} onClick={() => send()}>Send</button>
      </div>
    </div>
  );
}
