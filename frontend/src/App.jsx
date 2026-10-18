import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import { Loading } from "./components/ui.jsx";
import Login from "./pages/Login.jsx";
import Profile from "./pages/faculty/Profile.jsx";
import History from "./pages/faculty/History.jsx";
import MyPreferences from "./pages/faculty/Preferences.jsx";
import Allocations from "./pages/faculty/Allocations.jsx";
import Rankings from "./pages/coordinator/Rankings.jsx";
import Review from "./pages/coordinator/Review.jsx";
import Courses from "./pages/coordinator/Courses.jsx";
import Sections from "./pages/coordinator/Sections.jsx";
import Instructors from "./pages/coordinator/Instructors.jsx";
import Semesters from "./pages/coordinator/Semesters.jsx";
import AllocationsOverview from "./pages/coordinator/Allocations.jsx";
import Settings from "./pages/coordinator/Settings.jsx";
import AuditLog from "./pages/coordinator/AuditLog.jsx";

const homeFor = (user) => (user.role === "faculty" ? "/profile" : "/rankings");

// Wraps pages that need a login. `allow` limits a page to some roles.
function Protected({ allow, children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (allow && !allow(user)) return <Navigate to={homeFor(user)} replace />;
  return children;
}

// One address, two different pages: faculty see their own allocations, coordinators see everyone's.
function ByRole({ faculty, coordinator }) {
  const { user } = useAuth();
  return user.role === "faculty" ? faculty : coordinator;
}

const forFaculty = (user) => user.role === "faculty";
const forCoordinators = (user) => user.role !== "faculty";
const forDepartment = (user) => user.role === "department_coordinator";

export default function App() {
  const { user, loading } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route path="/profile" element={<Protected allow={forFaculty}><Profile /></Protected>} />
        <Route path="/history" element={<Protected allow={forFaculty}><History /></Protected>} />
        <Route path="/preferences" element={<Protected allow={forFaculty}><MyPreferences /></Protected>} />

        <Route path="/rankings" element={<Protected allow={forCoordinators}><Rankings /></Protected>} />
        <Route path="/allocations" element={<ByRole faculty={<Allocations />} coordinator={<AllocationsOverview />} />} />
        <Route path="/settings" element={<Protected allow={forCoordinators}><Settings /></Protected>} />
        <Route path="/review" element={<Protected allow={forCoordinators}><Review /></Protected>} />
        <Route path="/courses" element={<Protected allow={forCoordinators}><Courses /></Protected>} />
        <Route path="/sections" element={<Protected allow={forCoordinators}><Sections /></Protected>} />
        <Route path="/instructors" element={<Protected allow={forCoordinators}><Instructors /></Protected>} />
        <Route path="/semesters" element={<Protected allow={forCoordinators}><Semesters /></Protected>} />
        <Route path="/audit" element={<Protected allow={forDepartment}><AuditLog /></Protected>} />
      </Route>
      <Route
        path="*"
        element={loading ? <Loading /> : <Navigate to={user ? homeFor(user) : "/login"} replace />}
      />
    </Routes>
  );
}
