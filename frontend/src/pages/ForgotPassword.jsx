import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { BrandMark } from "../components/Brand.jsx";
import { Button, Field, Notice } from "../components/ui.jsx";

const RESEND_SECONDS = 60; // matches the server's one-code-per-minute limit

const linkButton = {
  background: "none", border: 0, padding: 0, font: "inherit", cursor: "pointer",
  color: "var(--accent)", textDecoration: "underline",
};

// Three steps on one page: enter username -> enter the emailed code + new password -> done.
// The code goes to the email registered on the account; the user never types an email.
export default function ForgotPassword() {
  const { user } = useAuth();
  const [step, setStep] = useState("email");
  const [username, setUsername] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  if (user) return <Navigate to={user.role === "faculty" ? "/profile" : "/rankings"} replace />;

  const requestCode = async (resend = false) => {
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { username: username.trim() });
      setStep("reset");
      setCooldown(RESEND_SECONDS);
      setCode("");
      setInfo(
        resend
          ? "A new code has been requested. Use the newest email; older codes no longer work."
          : `If an account exists for “${username.trim()}”, a 6-digit code has been sent to its registered email address. It expires in 10 minutes.`
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const submitEmail = (event) => {
    event.preventDefault();
    requestCode(false);
  };

  const submitReset = async (event) => {
    event.preventDefault();
    setError("");
    if (!/^\d{6}$/.test(code.trim())) return setError("Enter the 6-digit code from the email.");
    if (password.length < 8) return setError("Use at least 8 characters for the new password.");
    if (new TextEncoder().encode(password).length > 72) return setError("That password is too long (72 bytes maximum).");
    if (password !== confirm) return setError("The two passwords don't match.");
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { username: username.trim(), code: code.trim(), new_password: password });
      setPassword("");
      setConfirm("");
      setStep("done");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      {step === "email" && (
        <form className="login-card" onSubmit={submitEmail}>
          <div className="login-brand"><BrandMark size={52} /></div>
          <h1>Reset password</h1>
          <p className="muted">Enter your username and we'll email a 6-digit code to the address registered on your account.</p>
          <Notice onClose={() => setError("")}>{error}</Notice>
          <Field label="Username">
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required autoComplete="username" />
          </Field>
          <Button variant="primary" type="submit" disabled={busy || !username.trim()}>
            {busy ? "Sending…" : "Send code"}
          </Button>
          <p className="small" style={{ textAlign: "center", marginTop: 16 }}>
            <Link to="/login">Back to sign in</Link>
          </p>
        </form>
      )}

      {step === "reset" && (
        <form className="login-card" onSubmit={submitReset}>
          <div className="login-brand"><BrandMark size={52} /></div>
          <h1>Enter your code</h1>
          <Notice tone="info">{info}</Notice>
          <Notice onClose={() => setError("")}>{error}</Notice>
          <Field label="6-digit code">
            <input
              type="text" inputMode="numeric" pattern="[0-9]*" maxLength={6} autoComplete="one-time-code"
              value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoFocus required
            />
          </Field>
          <Field label="New password" hint="At least 8 characters.">
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
          </Field>
          <Field label="Confirm new password">
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required />
          </Field>
          <Button variant="primary" type="submit" disabled={busy}>
            {busy ? "Saving…" : "Change password"}
          </Button>
          <p className="small muted" style={{ textAlign: "center", marginTop: 16 }}>
            Didn't get it?{" "}
            {cooldown > 0 ? (
              <span>You can request another code in {cooldown}s.</span>
            ) : (
              <button type="button" style={linkButton} disabled={busy} onClick={() => requestCode(true)}>
                Send a new code
              </button>
            )}
            <br />
            <button type="button" style={linkButton} onClick={() => { setStep("email"); setError(""); }}>
              Use a different username
            </button>
          </p>
        </form>
      )}

      {step === "done" && (
        <div className="login-card">
          <div className="login-brand"><BrandMark size={52} /></div>
          <h1>Password changed</h1>
          <Notice tone="success">Your password has been changed. You can now sign in with it.</Notice>
          <Link to="/login" className="btn primary" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
            Back to sign in
          </Link>
        </div>
      )}
    </div>
  );
}
