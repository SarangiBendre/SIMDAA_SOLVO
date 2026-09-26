import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import Logo from "../components/Logo";
import api from "../api/client";
import "../styles/auth.css";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1 = enter email, 2 = enter code + new password
  const [username, setUsername] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const requestCode = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post("/auth/forgot-password", { Username: username });
      setInfo(data.message);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/auth/reset-password", { Username: username, Code: code, NewPassword: newPassword });
      navigate("/login", { state: { justReset: true } });
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired code");
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
        <h1>Forgot your password?</h1>
        <p>
          Enter your username and we'll send a verification code to the
          email already on file for your account. The code expires
          after 15 minutes.
        </p>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-box">
          <div className="auth-mobile-brand">
            <span className="auth-logo-chip auth-logo-chip-light"><Logo size={26} /></span>
            <strong>SIMDAA SOLVO</strong>
          </div>
          {step === 1 ? (
            <>
              <h2>Reset password</h2>
              <p className="auth-sub">Enter your username to get a code sent to your email on file.</p>
              {error && <div className="alert alert-error">{error}</div>}
              <form onSubmit={requestCode}>
                <div className="field">
                  <label htmlFor="username">Username</label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
                  {submitting ? "Sending..." : "Send verification code"}
                </button>
              </form>
            </>
          ) : (
            <>
              <h2>Enter your code</h2>
              <p className="auth-sub">{info}</p>
              {error && <div className="alert alert-error">{error}</div>}
              <form onSubmit={resetPassword}>
                <div className="field">
                  <label htmlFor="code">Verification code</label>
                  <input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="6-digit code"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="newPassword">New password</label>
                  <div className="password-input">
                    <input
                      id="newPassword"
                      type={showPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      minLength={6}
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
                  {submitting ? "Resetting..." : "Reset password"}
                </button>
              </form>
            </>
          )}

          <p className="auth-hint">
            <Link to="/login">Back to login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
