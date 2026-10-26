import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { BrandMark } from "./Brand.jsx";

const FACULTY_LINKS = [
  ["/profile", "My Profile"],
  ["/history", "Teaching History"],
  ["/preferences", "Preferences"],
  ["/allocations", "My Allocations"],
];

const COORDINATOR_LINKS = [
  ["/rankings", "Rankings"],
  ["/allocations", "Allocations"],
  ["/review", "Preferences"],
  ["/courses", "Courses"],
  ["/sections", "Sections"],
  ["/instructors", "Instructors"],
  ["/semesters", "Semesters"],
  ["/document-chat", "Document chat"],
  ["/settings", "Policy Settings"],
];

const ROLE_LABELS = {
  faculty: "Faculty",
  department_coordinator: "Department Coordinator",
  program_coordinator: "Program Coordinator",
};

// Small outline icons (24x24 grid), one per page.
const ICONS = {
  "/profile": <><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>,
  "/history": <><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></>,
  "/preferences": <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />,
  "/review": <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />,
  "/allocations": <><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /><path d="m9 16 2 2 4-4" /></>,
  "/rankings": <><line x1="12" y1="20" x2="12" y2="10" /><line x1="18" y1="20" x2="18" y2="4" /><line x1="6" y1="20" x2="6" y2="16" /></>,
  "/courses": <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></>,
  "/sections": <><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></>,
  "/instructors": <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>,
  "/semesters": <><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></>,
  "/document-chat": <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />,
  "/settings": <><line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" /><line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" /><line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" /><line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" /></>,
  "/audit": <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
};

function NavIcon({ to }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICONS[to] || <circle cx="12" cy="12" r="4" />}
    </svg>
  );
}

export default function Layout() {
  const { user, logout, isFaculty, canWrite } = useAuth();
  const links = isFaculty
    ? FACULTY_LINKS
    : [...COORDINATOR_LINKS, ...(canWrite ? [["/audit", "Audit Log"]] : [])];

  return (
    <div className="app">
      <nav className="sidebar" aria-label="Main">
        <div className="brand">
          <BrandMark size={38} />
          <div className="brand-name">
            Course Allocation
            <small>Teaching assignments</small>
          </div>
        </div>
        <div className="role">{ROLE_LABELS[user.role]}</div>
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            <NavIcon to={to} />
            {label}
          </NavLink>
        ))}
        <div className="spacer" />
        <div className="who">
          <span className="avatar" aria-hidden="true">{user.username.charAt(0)}</span>
          <div>
            <strong>{user.username}</strong>
            {user.program ? user.program.name : user.department.name}
            {!isFaculty && !canWrite && " · read-only"}
          </div>
        </div>
        <button type="button" className="btn small" onClick={logout}>
          Log out
        </button>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
