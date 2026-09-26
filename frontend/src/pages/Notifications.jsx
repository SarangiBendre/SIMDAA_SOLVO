import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaBell, FaCheckDouble } from "react-icons/fa";
import Layout from "../components/Layout";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import api from "../api/client";
import { formatDateTime } from "../utils/date";

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/notifications/").then(({ data }) => setNotifications(data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const markRead = async (id) => {
    await api.put(`/notifications/${id}/read`);
    load();
  };

  const markAllRead = async () => {
    await api.put("/notifications/read-all");
    load();
  };

  return (
    <Layout title="Notifications">
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 14 }}>
        <button className="btn btn-secondary" onClick={markAllRead}>
          <FaCheckDouble /> Mark all as read
        </button>
      </div>

      {loading ? (
        <Loader label="Loading notifications..." />
      ) : notifications.length === 0 ? (
        <EmptyState icon={<FaBell />} title="You're all caught up" description="New activity on your questions and answers will show up here." />
      ) : (
        <div className="questions-list">
          {notifications.map((n) => (
            <div
              key={n.NotificationID}
              className="card"
              style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", opacity: n.IsRead ? 0.6 : 1 }}
            >
              <div>
                {n.Link ? <Link to={n.Link} onClick={() => markRead(n.NotificationID)}>{n.Message}</Link> : n.Message}
                <div className="text-faint" style={{ fontSize: 12, marginTop: 4 }}>
                  {formatDateTime(n.CreatedAt)}
                </div>
              </div>
              {!n.IsRead && (
                <button className="btn btn-secondary" style={{ padding: "6px 12px" }} onClick={() => markRead(n.NotificationID)}>
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
