import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Cloud, LockKeyhole } from "lucide-react";
import { useAuth } from "../context/authState";

export default function Login() {
  const { enabled, loading, user, login, completeMfa, oidcEnabled, oidcLoginUrl } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [challengeToken, setChallengeToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");

  if (!loading && (!enabled || user)) return <Navigate to="/" replace />;

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(username, password);
      if (result?.mfa_required) {
        setChallengeToken(result.challenge_token);
        setPassword("");
        return;
      }
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  const submitMfa = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await completeMfa(challengeToken, mfaCode);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to verify the authentication code.");
    } finally {
      setSubmitting(false);
    }
  };

  return <main className="login-page">
    <form className="login-card" onSubmit={challengeToken ? submitMfa : submit}>
      <div className="login-brand"><Cloud size={28} /><div><h1>Cloud Sentinel</h1><span>Security Platform</span></div></div>
      <div className="login-heading"><LockKeyhole size={22} /><div><h2>{challengeToken ? "Verify your identity" : "Secure sign in"}</h2><p>{challengeToken ? "Enter your six-digit authenticator code or a recovery code." : "Use your assigned production workspace account."}</p></div></div>
      {challengeToken ? <label>Authentication code<input autoFocus inputMode="numeric" autoComplete="one-time-code" value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} required /></label> : <>
        <label>Username<input autoFocus autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
        <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
      </>}
      {error && <p className="login-error" role="alert">{error}</p>}
      <button type="submit" disabled={submitting}>{submitting ? "Verifying…" : challengeToken ? "Verify and sign in" : "Sign in"}</button>
      {challengeToken && <button className="login-secondary-button" type="button" onClick={() => { setChallengeToken(""); setMfaCode(""); setError(""); }}>Use a different account</button>}
      {!challengeToken && oidcEnabled && oidcLoginUrl && <>
        <div className="login-divider"><span>or</span></div>
        <a className="login-sso-button" href={oidcLoginUrl}>Continue with company SSO</a>
      </>}
    </form>
  </main>;
}
