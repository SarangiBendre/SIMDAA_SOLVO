import { useEffect, useState } from "react";
import { FaPlus, FaBan, FaCheck, FaTrash, FaEye, FaEyeSlash, FaEdit } from "react-icons/fa";
import Layout from "../../components/Layout";
import Loader from "../../components/Loader";
import api from "../../api/client";
import "../../styles/admin.css";

const ROLE_NAMES = { 1: "Admin", 2: "Mentor/Senior", 3: "Employee", 4: "Intern", 5: "Trainee" };

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    RoleID: 3, Username: "", Password: "", FullName: "", Email: "", Department: "",
  });

  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({ FullName: "", Email: "", Department: "", RoleID: 3 });
  const [editError, setEditError] = useState("");

  const load = () => {
    api.get("/users/").then(({ data }) => setUsers(data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/users/", { ...form, RoleID: Number(form.RoleID) });
      setShowForm(false);
      setForm({ RoleID: 3, Username: "", Password: "", FullName: "", Email: "", Department: "" });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create user");
    }
  };

  const toggleActive = async (u) => {
    if (u.IsActive) {
      await api.delete(`/users/${u.UserID}`);
    } else {
      await api.put(`/users/${u.UserID}/reactivate`);
    }
    load();
  };

  const deletePermanently = async (u) => {
    const confirmed = window.confirm(
      `Permanently delete ${u.FullName}? This removes their account and all their questions, answers, and comments. This cannot be undone.\n\nIf you just want to disable their login, use Deactivate instead.`
    );
    if (!confirmed) return;
    try {
      await api.delete(`/users/${u.UserID}/permanent`);
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Could not delete user");
    }
  };

  const startEdit = (u) => {
    setEditError("");
    setEditingUser(u);
    setEditForm({ FullName: u.FullName, Email: u.Email, Department: u.Department || "", RoleID: u.RoleID });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setEditError("");
    try {
      await api.put(`/users/${editingUser.UserID}`, { ...editForm, RoleID: Number(editForm.RoleID) });
      setEditingUser(null);
      load();
    } catch (err) {
      setEditError(err.response?.data?.detail || "Could not update user");
    }
  };

  return (
    <Layout title="Users">
      <div className="admin-toolbar">
        <p className="text-muted" style={{ margin: 0 }}>{users.length} accounts</p>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <FaPlus /> New user
        </button>
      </div>

      {loading ? (
        <Loader label="Loading users..." />
      ) : (
        <div className="card">
          <div className="table-scroll">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Username</th>
                <th>Role</th>
                <th>Department</th>
                <th>Points</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.UserID}>
                  <td>{u.FullName}</td>
                  <td>{u.Username}</td>
                  <td><span className="role-tag">{u.RoleName || ROLE_NAMES[u.RoleID]}</span></td>
                  <td>{u.Department || "-"}</td>
                  <td>{u.Points}</td>
                  <td>
                    <span className={`status-dot ${u.IsActive ? "active" : "inactive"}`} />
                    {u.IsActive ? "Active" : "Inactive"}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: "6px 12px" }}
                        onClick={() => startEdit(u)}
                      >
                        <FaEdit /> Edit
                      </button>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: "6px 12px" }}
                        onClick={() => toggleActive(u)}
                      >
                        {u.IsActive ? <><FaBan /> Deactivate</> : <><FaCheck /> Reactivate</>}
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ padding: "6px 12px" }}
                        onClick={() => deletePermanently(u)}
                      >
                        <FaTrash /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {showForm && (
        <div className="modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: 16 }}>Create user</h3>
            {error && <div className="alert alert-error">{error}</div>}
            <form onSubmit={handleCreate}>
              <div className="field">
                <label>Full name</label>
                <input value={form.FullName} onChange={(e) => setForm({ ...form, FullName: e.target.value })} required />
              </div>
              <div className="field">
                <label>Username</label>
                <input value={form.Username} onChange={(e) => setForm({ ...form, Username: e.target.value })} required />
              </div>
              <div className="field">
                <label>Email</label>
                <input type="email" value={form.Email} onChange={(e) => setForm({ ...form, Email: e.target.value })} required />
              </div>
              <div className="field">
                <label>Password</label>
                <div className="password-input">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={form.Password}
                    onChange={(e) => setForm({ ...form, Password: e.target.value })}
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
              <div className="field">
                <label>Department</label>
                <input value={form.Department} onChange={(e) => setForm({ ...form, Department: e.target.value })} required />
              </div>
              <div className="field">
                <label>Role</label>
                <select value={form.RoleID} onChange={(e) => setForm({ ...form, RoleID: e.target.value })}>
                  <option value={5}>Trainee</option>
                  <option value={4}>Intern</option>
                  <option value={3}>Employee</option>
                  <option value={2}>Mentor/Senior</option>
                  <option value={1}>Admin</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button type="submit" className="btn btn-primary btn-block">Create</button>
                <button type="button" className="btn btn-secondary btn-block" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingUser && (
        <div className="modal-backdrop" onClick={() => setEditingUser(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: 16 }}>Edit user</h3>
            {editError && <div className="alert alert-error">{editError}</div>}
            <form onSubmit={handleEditSubmit}>
              <div className="field">
                <label>Full name</label>
                <input value={editForm.FullName} onChange={(e) => setEditForm({ ...editForm, FullName: e.target.value })} required />
              </div>
              <div className="field">
                <label>Email</label>
                <input type="email" value={editForm.Email} onChange={(e) => setEditForm({ ...editForm, Email: e.target.value })} required />
              </div>
              <div className="field">
                <label>Department</label>
                <input value={editForm.Department} onChange={(e) => setEditForm({ ...editForm, Department: e.target.value })} required />
              </div>
              <div className="field">
                <label>Role</label>
                <select value={editForm.RoleID} onChange={(e) => setEditForm({ ...editForm, RoleID: e.target.value })}>
                  <option value={5}>Trainee</option>
                  <option value={4}>Intern</option>
                  <option value={3}>Employee</option>
                  <option value={2}>Mentor/Senior</option>
                  <option value={1}>Admin</option>
                </select>
              </div>
              <p className="text-faint" style={{ fontSize: 12, marginTop: -8, marginBottom: 16 }}>
                Username can't be changed here. To reset a password, the user should use "Forgot password" on the login screen.
              </p>
              <div style={{ display: "flex", gap: 10 }}>
                <button type="submit" className="btn btn-primary btn-block">Save changes</button>
                <button type="button" className="btn btn-secondary btn-block" onClick={() => setEditingUser(null)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
}
