import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import "./Sidebar.css";

export default function Layout({ title, children }) {
  const { isAdmin, isMentor, refreshMe } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [reviewQueueCount, setReviewQueueCount] = useState(0);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    // Keeps the sidebar's Level/points current - these reset every
    // month, so without this, whatever was cached at login would just
    // sit there stale (refreshMe existed but was never actually being
    // called anywhere). Layout re-mounts on every page's own <Layout>
    // wrapper, so in practice this keeps it in sync continuously
    // during normal use, not just right after logging in.
    refreshMe().catch(() => {});
  }, [refreshMe]);

  useEffect(() => {
    let cancelled = false;

    const loadCount = () => {
      api.get("/notifications/unread-count")
        .then(({ data }) => {
          if (!cancelled) setUnreadCount(data.UnreadCount);
        })
        .catch(() => {});
    };

    loadCount();
    const interval = setInterval(loadCount, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!isAdmin && !isMentor) return;
    let cancelled = false;

    const loadReviewCount = () => {
      api.get("/ai/pending-review")
        .then(({ data }) => {
          if (!cancelled) setReviewQueueCount(data.length);
        })
        .catch(() => {});
    };

    loadReviewCount();
    const interval = setInterval(loadReviewCount, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [isAdmin, isMentor]);

  return (
    <div className="app-shell">
      <Sidebar
        unreadCount={unreadCount}
        reviewQueueCount={reviewQueueCount}
        mobileOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      />
      <div className="app-content">
        <Topbar title={title} unreadCount={unreadCount} onMenuClick={() => setMobileNavOpen(true)} />
        <main className="container">{children}</main>
      </div>
    </div>
  );
}
