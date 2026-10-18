import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth.jsx";

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
  ["/settings", "Policy Settings"],
];

const ROLE_LABELS = {
  faculty: "Faculty",
  department_coordinator: "Department Coordinator",
  program_coordinator: "Program Coordinator",
};

export default function Layout() {
  const { user, logout, isFaculty, canWrite } = useAuth();
  const links = isFaculty
    ? FACULTY_LINKS
    : [...COORDINATOR_LINKS, ...(canWrite ? [["/audit", "Audit Log"]] : [])];

  return (
    <div className="app">
      <nav className="sidebar" aria-label="Main">
        <div className="role">{ROLE_LABELS[user.role]}</div>
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            {label}
          </NavLink>
        ))}
        <div className="spacer" />
        <div className="who">
          <strong>{user.username}</strong>
          {user.program ? user.program.name : user.department.name}
          {!isFaculty && !canWrite && " · read-only"}
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
