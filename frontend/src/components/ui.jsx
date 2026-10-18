import { useEffect, useRef, useState } from "react";

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <div className="subtitle">{subtitle}</div>}
      </div>
      {children && <div className="actions">{children}</div>}
    </div>
  );
}

export function Card({ title, actions, children }) {
  return (
    <section className="card">
      {title && (
        <div className="card-head">
          <h2>{title}</h2>
          {actions && <div className="actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Button({ variant = "secondary", small, className = "", ...props }) {
  const classes = ["btn", variant === "secondary" ? "" : variant, small ? "small" : "", className]
    .filter(Boolean)
    .join(" ");
  return <button type="button" className={classes} {...props} />;
}

export function Pill({ tone = "neutral", children }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

const TONES = { approved: "ok", active: "ok", confirmed: "ok", pending: "warn", on_leave: "warn", rejected: "danger", cancelled: "danger" };
const LABELS = { on_leave: "On leave" };
export function StatusPill({ status }) {
  const label = LABELS[status] || status.charAt(0).toUpperCase() + status.slice(1);
  return <Pill tone={TONES[status] || "neutral"}>{label}</Pill>;
}

export function Notice({ tone = "error", onClose, children }) {
  if (!children) return null;
  return (
    <div className={`notice ${tone}`} role={tone === "error" ? "alert" : "status"}>
      <span>{children}</span>
      {onClose && (
        <button type="button" aria-label="Dismiss" onClick={onClose}>
          ×
        </button>
      )}
    </div>
  );
}

// Shows an API error. A refused allocation carries a list of conflicts: show them all.
export function ErrorNotice({ error, onClose }) {
  const ref = useRef(null);
  // Bring the alert into view: the button that caused it may be far down the page.
  useEffect(() => {
    if (error) ref.current?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
  }, [error]);
  if (!error) return null;
  const message = typeof error === "string" ? error : error.message;
  const conflicts = (typeof error === "object" && error.conflicts) || [];
  return (
    <div className="notice error" role="alert" ref={ref}>
      <div>
        <strong>{message}</strong>
        {conflicts.length > 0 && (
          <ul className="conflicts">
            {conflicts.map((c) => <li key={c.code}>{c.message}</li>)}
          </ul>
        )}
      </div>
      {onClose && (
        <button type="button" aria-label="Dismiss" onClick={onClose}>×</button>
      )}
    </div>
  );
}

export const Loading = ({ children = "Loading…" }) => <div className="loading">{children}</div>;
export const Empty = ({ children }) => <div className="empty">{children}</div>;

// A label wrapped around its input, so clicking the label focuses the field.
export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  );
}

export function Modal({ title, onClose, children, footer }) {
  useEffect(() => {
    const onKey = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <h2>{title}</h2>
        {children}
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

// columns: [{ header, render: (row) => node, className }]
export function Table({ columns, rows, rowKey = (row) => row.id, onRowClick, empty = "Nothing to show." }) {
  if (!rows || rows.length === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.header} className={c.className}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              className={onRowClick ? "clickable" : ""}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((c) => (
                <td key={c.header} className={c.className}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ScoreBar({ value }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="bar" role="img" aria-label={`${pct}%`}>
      <div style={{ width: `${pct}%` }} />
    </div>
  );
}

// Loads data when the page opens (and again when `deps` change or reload() is called).
export function useLoad(load, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    Promise.resolve()
      .then(load)
      .then(
        (data) => !cancelled && setState({ data, loading: false, error: null }),
        (error) => !cancelled && setState({ data: null, loading: false, error })
      );
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}

// The backend stores times in UTC without a "Z", so add it before showing local time.
export function formatTime(value) {
  if (!value) return "";
  const iso = /[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`;
  return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
