import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { listModels, downloadModel, deleteModel, getVramStatus, unloadAllModels } from '../api/client';

export default function ModelManager() {
  const [models, setModels] = useState([]);
  const [vram, setVram] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    listModels().then(d => setModels(d.models || [])).catch(() => {});
    getVramStatus().then(setVram).catch(() => {});
  }, [refreshKey]);

  // Auto-refresh every 5 seconds during downloads
  useEffect(() => {
    const hasDownloading = models.some(m => m.download_progress?.status === 'downloading');
    if (!hasDownloading) return;
    const interval = setInterval(() => setRefreshKey(k => k + 1), 5000);
    return () => clearInterval(interval);
  }, [models]);

  const handleDownload = async (modelName) => {
    try {
      await downloadModel(modelName);
      toast.success('Download started');
      setRefreshKey(k => k + 1);
    } catch (err) {
      toast.error('Download failed');
    }
  };

  const handleDelete = async (modelName) => {
    if (!confirm(`Delete model ${modelName}? You'll need to re-download it later.`)) return;
    try {
      await deleteModel(modelName);
      toast.success('Model deleted');
      setRefreshKey(k => k + 1);
    } catch (err) {
      toast.error('Delete failed');
    }
  };

  const handleUnloadAll = async () => {
    try {
      await unloadAllModels();
      toast.success('All models unloaded');
      setRefreshKey(k => k + 1);
    } catch (err) {
      toast.error('Failed to unload');
    }
  };

  return (
    <div className="fade-in">
      <div className="flex items-center justify-between mb-lg">
        <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>🧠 Model Manager</h2>
        <div className="flex gap-md">
          <button className="btn btn-danger btn-sm" onClick={handleUnloadAll}>
            Unload All Models
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setRefreshKey(k => k + 1)}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* VRAM Status */}
      {vram && (
        <div className="card mb-lg">
          <div className="flex items-center justify-between mb-md">
            <div>
              <div className="text-sm font-bold">GPU VRAM Usage</div>
              <div className="text-xs text-muted">
                {vram.gpu_info?.devices?.[0]?.name || 'N/A'} — {vram.vram_used_mb} / {vram.gpu_info?.devices?.[0]?.total_vram_mb || '?'} MB
              </div>
            </div>
            <div className="text-sm font-bold" style={{ color: 'var(--accent-primary-light)' }}>
              {vram.vram_free_mb} MB free
            </div>
          </div>
          <div className="progress-bar" style={{ height: '10px' }}>
            <div className="progress-bar-fill" style={{
              width: `${(vram.vram_used_mb / (vram.gpu_info?.devices?.[0]?.total_vram_mb || 4096)) * 100}%`,
            }} />
          </div>
          {vram.loaded_models?.length > 0 && (
            <div className="text-xs text-muted" style={{ marginTop: '8px' }}>
              Loaded: {vram.loaded_models.join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Model List */}
      <div className="card">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <th style={thStyle}>Model</th>
              <th style={thStyle}>Size</th>
              <th style={thStyle}>VRAM</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {models.map(m => (
              <tr key={m.name} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={tdStyle}>
                  <div>
                    <div className="font-bold text-sm">{m.name}</div>
                    <div className="text-xs text-muted">{m.description}</div>
                  </div>
                </td>
                <td style={tdStyle}>{m.size_mb} MB</td>
                <td style={tdStyle}>{m.vram_mb} MB</td>
                <td style={tdStyle}>
                  {m.downloaded ? (
                    <span className={`status-badge ${m.load_state === 'ready' ? 'completed' : 'pending'}`}>
                      {m.load_state === 'ready' ? '🟢 Loaded' : '💾 Downloaded'}
                    </span>
                  ) : m.download_progress?.status === 'downloading' ? (
                    <div style={{ minWidth: '120px' }}>
                      <div className="progress-bar" style={{ height: '4px' }}>
                        <div className="progress-bar-fill" style={{ width: `${m.download_progress.percent}%` }} />
                      </div>
                      <div className="text-xs text-muted" style={{ marginTop: '2px' }}>
                        {m.download_progress.percent}%
                      </div>
                    </div>
                  ) : (
                    <span className="status-badge failed">❌ Not Downloaded</span>
                  )}
                </td>
                <td style={tdStyle}>
                  {!m.downloaded ? (
                    <button className="btn btn-primary btn-sm" onClick={() => handleDownload(m.name)}>
                      ⬇ Download
                    </button>
                  ) : (
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(m.name)}>
                      🗑 Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = {
  textAlign: 'left', padding: '12px 14px', fontSize: '0.75rem',
  fontWeight: 600, color: 'var(--text-tertiary)',
  textTransform: 'uppercase', letterSpacing: '0.05em',
};
const tdStyle = { padding: '12px 14px' };
