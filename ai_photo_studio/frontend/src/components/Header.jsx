export default function Header({ connected }) {
  return (
    <header className="header">
      <h1 className="header-title">AI Photo Studio</h1>
      <div className="header-actions">
        <div className={`header-badge ${connected ? '' : 'disconnected'}`}
             style={connected ? {} : { background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}>
          <span className="dot-pulse" style={connected ? {} : { background: '#ef4444' }}></span>
          {connected ? ' Connected' : ' Disconnected'}
        </div>
        <span className="text-xs text-muted">v2.0.0</span>
      </div>
    </header>
  );
}
