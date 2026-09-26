import { useEffect, useState } from "react";
import { FaMedal, FaEnvelope, FaBuilding, FaEye, FaEyeSlash, FaLock } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    if (user?.UserID) {
      api.get(`/users/profile/${user.UserID}`).then(({ data }) => setProfile(data));
    }
  }, [user]);

  const submitPasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    setChangingPassword(true);
    try {
      await api.put("/auth/change-password", {
        CurrentPassword: currentPassword,
        NewPassword: newPassword,
      });
      setPasswordSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setPasswordError(err.response?.data?.detail || "Could not update password");
    } finally {
      setChangingPassword(false);
    }
  };

  if (!profile) {
    return (
      <Layout title="Profile">
        <Loader label="Loading profile..." />
      </Layout>
    );
  }

  return (
    <Layout title="Profile">
      <div className="dashboard-columns">
        <div className="card section-card">
          <h3>{profile.FullName}</h3>
          <p className="text-muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <FaEnvelope /> {profile.Email}
          </p>
          {profile.Department && (
            <p className="text-muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <FaBuilding /> {profile.Department}
            </p>
          )}

          <div className="stats-grid profile-stats-grid" style={{ marginTop: 20 }}>
            <div className="card stat-card" style={{ padding: 14 }}>
              <div>
                <div className="stat-value">{profile.QuestionsAsked}</div>
                <div className="stat-label">Questions asked</div>
              </div>
            </div>
            <div className="card stat-card" style={{ padding: 14 }}>
              <div>
                <div className="stat-value">{profile.AnswersPosted}</div>
                <div className="stat-label">Answers posted</div>
              </div>
            </div>
            <div className="card stat-card" style={{ padding: 14 }}>
              <div>
                <div className="stat-value">{profile.AcceptedAnswers}</div>
                <div className="stat-label">Accepted answers</div>
              </div>
            </div>
          </div>
        </div>

        <div className="card section-card">
          <h3><FaMedal style={{ color: "var(--color-accent)", marginRight: 8 }} />Badges earned</h3>
          {profile.Badges.length === 0 ? (
            <p className="text-muted" style={{ fontSize: 13.5 }}>No badges yet.</p>
          ) : (
            <div className="badge-strip">
              {profile.Badges.map((b) => (
                <div key={b.BadgeID} className="badge-chip"><FaMedal /> {b.Name}</div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 18 }}>
            <span className="pill pill-level">{profile.Level}</span>
            <span className="text-muted" style={{ marginLeft: 10, fontSize: 13.5 }}>{profile.Points} points</span>
          </div>
        </div>

        <div className="card section-card">
          <h3><FaLock style={{ marginRight: 8 }} />Change password</h3>
          {passwordError && <div className="alert alert-error">{passwordError}</div>}
          {passwordSuccess && <div className="alert alert-success">{passwordSuccess}</div>}
          <form onSubmit={submitPasswordChange}>
            <div className="field">
              <label>Current password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label>New password</label>
              <div className="password-input">
                <input
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
            <button type="submit" className="btn btn-primary" disabled={changingPassword}>
              {changingPassword ? "Updating..." : "Update password"}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
}
