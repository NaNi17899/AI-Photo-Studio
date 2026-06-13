export default function ProgressBar({ progress = 0, message = '', status = 'running' }) {
  const statusColors = {
    running: 'var(--gradient-primary)',
    completed: 'linear-gradient(135deg, #10b981, #06b6d4)',
    failed: 'linear-gradient(135deg, #ef4444, #f59e0b)',
    pending: 'linear-gradient(135deg, #f59e0b, #eab308)',
  };

  return (
    <div className="card" style={{ padding: 'var(--space-md)' }}>
      <div className="progress-bar">
        <div
          className="progress-bar-fill"
          style={{
            width: `${Math.min(progress, 100)}%`,
            background: statusColors[status] || statusColors.running,
          }}
        />
      </div>
      <div className="progress-info">
        <span>{message || `Processing...`}</span>
        <span style={{ fontWeight: 600 }}>{Math.round(progress)}%</span>
      </div>
    </div>
  );
}
