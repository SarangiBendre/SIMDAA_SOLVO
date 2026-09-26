import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";
import "../styles/auth.css";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid username or password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-brand-panel">
        <div className="auth-brand-tag">
          <span className="auth-logo-chip"><Logo size={30} /></span>
          <strong>SIMDAA SOLVO</strong>
        </div>
        <h1>Ask. Solve. Share.</h1>
        <p>
          The internal doubt-clearance and knowledge-sharing platform for
          Simdaa Technologies. Post a question, get answers from mentors,
          and build a knowledge base the whole team can reuse.
        </p>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-box">
          <div className="auth-mobile-brand">
            <span className="auth-logo-chip auth-logo-chip-light"><Logo size={26} /></span>
            <strong>SIMDAA SOLVO</strong>
          </div>
          <h2>Welcome</h2>
          <p className="auth-sub">Sign in to keep learning and helping others learn.</p>

          {error && <div className="alert alert-error">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <div className="password-input">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="auth-hint">
            <Link to="/forgot-password">Forgot your password?</Link>
          </p>

          <p className="auth-hint">
            New here? Ask your admin to create an account for you.
          </p>
        </div>
      </div>
    </div>
  );
}
