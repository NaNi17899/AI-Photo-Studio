import { NavLink, useLocation } from 'react-router-dom';

export default function Sidebar({ features }) {
  const location = useLocation();

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">📸</div>
        <span className="sidebar-logo-text">AI Photo Studio</span>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">Dashboard</div>
        <NavLink to="/" className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`} end>
          <span className="sidebar-item-icon">🏠</span>
          <span>Overview</span>
        </NavLink>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">AI Tools</div>
        {features.map(f => (
          <NavLink
            key={f.path}
            to={`/${f.path}`}
            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
          >
            <span className="sidebar-item-icon">{f.icon}</span>
            <span>{f.title}</span>
          </NavLink>
        ))}
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">Workspace</div>
        <NavLink to="/batch" className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}>
          <span className="sidebar-item-icon">📦</span>
          <span>Batch Processing</span>
        </NavLink>
        <NavLink to="/models" className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}>
          <span className="sidebar-item-icon">🧠</span>
          <span>Model Manager</span>
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}>
          <span className="sidebar-item-icon">⚙️</span>
          <span>Settings</span>
        </NavLink>
      </div>
    </nav>
  );
}
