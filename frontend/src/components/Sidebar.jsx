import { NavLink } from "react-router-dom";
import {
  FaHome, FaQuestionCircle, FaPlusCircle, FaTrophy, FaBell,
  FaUsersCog, FaSignOutAlt, FaChartBar, FaTags, FaBookOpen, FaRobot, FaTimes,
} from "react-icons/fa";
import Logo from "./Logo";
import { useAuth } from "../context/AuthContext";
import "./Sidebar.css";

export default function Sidebar({ unreadCount = 0, reviewQueueCount = 0, mobileOpen = false, onClose = () => {} }) {
  const { user, isAdmin, isMentor, logout } = useAuth();

  // Tapping any nav link on mobile should close the drawer, not leave it
  // open over the page you just navigated to.
  const handleLinkClick = () => onClose();

  return (
    <>
      {mobileOpen && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <Logo size={34} />
          <div>
            <strong>SIMDAA SOLVO</strong>
            <span>Ask. Solve. Share.</span>
          </div>
          <button className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <FaTimes />
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className="sidebar-link" onClick={handleLinkClick}>
            <FaHome /> Dashboard
          </NavLink>
          <NavLink to="/questions" className="sidebar-link" onClick={handleLinkClick}>
            <FaQuestionCircle /> Questions
          </NavLink>
          <NavLink to="/ask-question" className="sidebar-link" onClick={handleLinkClick}>
            <FaPlusCircle /> Ask a Question
          </NavLink>
          <NavLink to="/knowledge-base" className="sidebar-link" onClick={handleLinkClick}>
            <FaBookOpen /> Knowledge Base
          </NavLink>
          <NavLink to="/ai-assistant" className="sidebar-link" onClick={handleLinkClick}>
            <FaRobot /> AI Assistant
          </NavLink>
          <NavLink to="/leaderboard" className="sidebar-link" onClick={handleLinkClick}>
            <FaTrophy /> Leaderboard
          </NavLink>
          <NavLink to="/notifications" className="sidebar-link" onClick={handleLinkClick}>
            <FaBell /> Notifications
            {unreadCount > 0 && <span className="sidebar-badge">{unreadCount}</span>}
          </NavLink>

          {(isAdmin || isMentor) && (
            <>
              <div className="sidebar-divider">Mentor</div>
              <NavLink to="/ai-review-queue" className="sidebar-link" onClick={handleLinkClick}>
                <FaRobot /> AI Review Queue
                {reviewQueueCount > 0 && <span className="sidebar-badge">{reviewQueueCount}</span>}
              </NavLink>
            </>
          )}

          {isAdmin && (
            <>
              <div className="sidebar-divider">Admin</div>
              <NavLink to="/admin/analytics" className="sidebar-link" onClick={handleLinkClick}>
                <FaChartBar /> Analytics
              </NavLink>
              <NavLink to="/admin/users" className="sidebar-link" onClick={handleLinkClick}>
                <FaUsersCog /> Users
              </NavLink>
              <NavLink to="/admin/categories" className="sidebar-link" onClick={handleLinkClick}>
                <FaTags /> Categories
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <NavLink to="/profile" className="sidebar-user" onClick={handleLinkClick}>
            <div className="sidebar-avatar">{(user?.FullName || user?.Username || "?")[0]}</div>
            <div>
              <strong>{user?.FullName || user?.Username}</strong>
              <span>{user?.Level || "Beginner"} &middot; {user?.Points ?? 0} pts</span>
            </div>
          </NavLink>
          <button className="sidebar-logout" onClick={logout} title="Log out">
            <FaSignOutAlt />
          </button>
        </div>
      </aside>
    </>
  );
}
