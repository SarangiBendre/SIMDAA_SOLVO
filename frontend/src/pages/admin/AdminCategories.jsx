import { useEffect, useState } from "react";
import { FaPlus, FaTrash } from "react-icons/fa";
import Layout from "../../components/Layout";
import Loader from "../../components/Loader";
import api from "../../api/client";
import "../../styles/admin.css";

export default function AdminCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    api.get("/categories/").then(({ data }) => setCategories(data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/categories/", { CategoryName: name, Description: description });
      setName("");
      setDescription("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create category");
    }
  };

  const remove = async (id) => {
    await api.delete(`/categories/${id}`);
    load();
  };

  return (
    <Layout title="Categories">
      <div className="admin-toolbar">
        <p className="text-muted" style={{ margin: 0 }}>{categories.length} categories</p>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <FaPlus /> New category
        </button>
      </div>

      {loading ? (
        <Loader label="Loading categories..." />
      ) : (
        <div className="card">
          <div className="table-scroll">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Questions</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {categories.map((c) => (
                <tr key={c.CategoryID}>
                  <td>{c.CategoryName}</td>
                  <td className="text-muted">{c.Description}</td>
                  <td>{c.QuestionCount}</td>
                  <td>
                    <button className="btn btn-danger" style={{ padding: "6px 12px" }} onClick={() => remove(c.CategoryID)}>
                      <FaTrash /> Remove
                    </button>
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
            <h3 style={{ marginBottom: 16 }}>Create category</h3>
            {error && <div className="alert alert-error">{error}</div>}
            <form onSubmit={handleCreate}>
              <div className="field">
                <label>Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="field">
                <label>Description</label>
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button type="submit" className="btn btn-primary btn-block">Create</button>
                <button type="button" className="btn btn-secondary btn-block" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
}
