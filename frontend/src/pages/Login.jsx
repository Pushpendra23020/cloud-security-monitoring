import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Cloud, LockKeyhole } from "lucide-react";
import { useAuth } from "../context/authState";

export default function Login() {
  const { enabled, loading, user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && (!enabled || user)) return <Navigate to="/" replace />;

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  return <main className="login-page">
    <form className="login-card" onSubmit={submit}>
      <div className="login-brand"><Cloud size={28} /><div><h1>Cloud Sentinel</h1><span>Security Platform</span></div></div>
      <div className="login-heading"><LockKeyhole size={22} /><div><h2>Secure sign in</h2><p>Use your assigned production workspace account.</p></div></div>
      <label>Username<input autoFocus autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
      <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
      {error && <p className="login-error" role="alert">{error}</p>}
      <button type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button>
    </form>
  </main>;
}
