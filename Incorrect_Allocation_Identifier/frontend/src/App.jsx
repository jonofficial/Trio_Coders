import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { fetchHealth } from './api';

import Dashboard from './pages/Dashboard';
import Exceptions from './pages/Exceptions';
import TriggerRun from './pages/TriggerRun';
import RejectedRows from './pages/RejectedRows';
import Configuration from './pages/Configuration';

export default function App() {
  const location = useLocation();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const check = () => {
      fetchHealth()
        .then(r => setHealth(r.data))
        .catch(() => setHealth(null));
    };
    check();
    const iv = setInterval(check, 15000);
    return () => clearInterval(iv);
  }, []);

  const isOnline = health?.status === 'ok' && health?.database_connected;

  const links = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/exceptions', label: 'Exceptions', icon: '⚠️' },
    { path: '/trigger', label: 'Trigger Run', icon: '▶️' },
    { path: '/rejected', label: 'Rejected Rows', icon: '🚫' },
    { path: '/config', label: 'Configuration', icon: '⚙️' },
  ];

  const pageTitle = {
    '/': 'Dashboard',
    '/exceptions': 'Exception Records',
    '/trigger': 'Trigger Pipeline Run',
    '/rejected': 'Rejected Rows',
    '/config': 'System Configuration',
  };

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">IAI</div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">IAI Agent</span>
            <span className="sidebar-brand-sub">Allocation Monitor</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Navigation</div>
          {links.map(link => (
            <NavLink
              key={link.path}
              to={link.path}
              end={link.path === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <span className="sidebar-link-icon">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`sidebar-status-dot ${isOnline ? 'online' : 'offline'}`} />
            <span>{isOnline ? 'Backend Connected' : 'Backend Offline'}</span>
          </div>
          {health && (
            <div className="sidebar-status" style={{ marginTop: 4 }}>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>v{health.version}</span>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main-content">
        <header className="page-header">
          <div>
            <div className="page-title">{pageTitle[location.pathname] || 'IAI'}</div>
            <div className="page-subtitle">Incorrect Allocation Identifier</div>
          </div>
        </header>

        <div className="page-body">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/exceptions" element={<Exceptions />} />
            <Route path="/trigger" element={<TriggerRun />} />
            <Route path="/rejected" element={<RejectedRows />} />
            <Route path="/config" element={<Configuration />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
