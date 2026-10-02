import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaSearch, FaBell, FaBars } from "react-icons/fa";
import { Link } from "react-router-dom";
import "./Topbar.css";

export default function Topbar({ title, unreadCount = 0, onMenuClick = () => {} }) {
  const [keyword, setKeyword] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (keyword.trim()) {
      navigate(`/questions?q=${encodeURIComponent(keyword.trim())}`);
    }
  };

  return (
    <header className="topbar">
      <button className="topbar-menu-btn" onClick={onMenuClick} aria-label="Open menu">
        <FaBars />
      </button>

      <h1 className="topbar-title">{title}</h1>

      <form className="topbar-search" onSubmit={handleSearch}>
        <FaSearch />
        <input
          type="text"
          placeholder="Search the knowledge base..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </form>

      <Link to="/notifications" className="topbar-bell" aria-label="Notifications">
        <FaBell />
        {unreadCount > 0 && <span className="topbar-bell-dot" />}
      </Link>
    </header>
  );
}
