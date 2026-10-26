import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { BrandMark } from "../components/Brand.jsx";
import { Button, Field, Notice } from "../components/ui.jsx";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={user.role === "faculty" ? "/profile" : "/rankings"} replace />;

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const me = await login(username.trim(), password);
      navigate(me.role === "faculty" ? "/profile" : "/rankings", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-hero" aria-label="About this system">
        <h1>Course Allocation</h1>
        <p>Fair, explainable teaching assignments for every semester.</p>
        <ul>
          <li>Rank instructors for every course section</li>
          <li>Respect preferences, qualifications and workload limits</li>
          <li>See exactly why each allocation was made</li>
        </ul>
      </section>

      <form className="login-card" onSubmit={submit}>
        <div className="login-brand"><BrandMark size={52} /></div>
        <h1>Welcome back</h1>
        <p className="muted">Sign in to continue</p>
        <Notice>{error}</Notice>
        <Field label="Username">
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required autoComplete="username" />
        </Field>
        <Field label="Password">
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        </Field>
        <Button variant="primary" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
        <p className="small" style={{ textAlign: "center", marginTop: 16 }}>
          <Link to="/forgot-password">Forgot password?</Link>
        </p>
      </form>
    </div>
  );
}
