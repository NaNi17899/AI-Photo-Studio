import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSystemInfo, getVramStatus, listJobs } from '../api/client';

export default function Dashboard({ features }) {
  const navigate = useNavigate();
  const [sysInfo, setSysInfo] = useState(null);
  const [vram, setVram] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);

  useEffect(() => {
    getSystemInfo().then(setSysInfo).catch(() => {});
    getVramStatus().then(setVram).catch(() => {});
    listJobs(5).then(d => setRecentJobs(d.jobs || [])).catch(() => {});
  }, []);

  return (
    <div className="fade-in">
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h2 style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 800 }}>
            Welcome to <span style={{ background: 'var(--gradient-accent)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>AI Photo Studio</span>
          </h2>
          <p className="text-muted" style={{ marginTop: '4px' }}>
            Professional AI photo editing — powered by GFPGAN, Real-ESRGAN, Stable Diffusion & more
          </p>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid-3 mb-lg">
        <div className="card-gradient">
          <div className="text-xs text-muted" style={{ marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>GPU</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
            {vram?.gpu_info?.devices?.[0]?.name || 'N/A'}
          </div>
          <div className="text-sm text-muted" style={{ marginTop: '4px' }}>
            {vram ? `${vram.vram_used_mb} / ${vram.gpu_info?.devices?.[0]?.total_vram_mb || '?'} MB used` : 'Loading...'}
          </div>
          {vram && (
            <div className="progress-bar" style={{ marginTop: '10px', height: '4px' }}>
              <div className="progress-bar-fill" style={{
                width: `${(vram.vram_used_mb / (vram.gpu_info?.devices?.[0]?.total_vram_mb || 4096)) * 100}%`,
                background: 'var(--gradient-primary)',
              }} />
            </div>
          )}
        </div>

        <div className="card-gradient">
          <div className="text-xs text-muted" style={{ marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Memory</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
            {sysInfo ? `${sysInfo.memory.available_gb} GB free` : 'Loading...'}
          </div>
          <div className="text-sm text-muted" style={{ marginTop: '4px' }}>
            {sysInfo ? `${sysInfo.memory.total_gb} GB total • ${sysInfo.memory.used_percent}% used` : ''}
          </div>
        </div>

        <div className="card-gradient">
          <div className="text-xs text-muted" style={{ marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Models Loaded</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
            {vram?.loaded_models?.length || 0}
          </div>
          <div className="text-sm text-muted" style={{ marginTop: '4px' }}>
            {vram?.loaded_models?.length > 0 ? vram.loaded_models.join(', ') : 'No models loaded'}
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <h3 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
        AI Tools
      </h3>
      <div className="dashboard-grid mb-lg">
        {features.map((f, idx) => (
          <div
            key={f.path}
            className="feature-card fade-in"
            style={{ animationDelay: `${idx * 50}ms` }}
            onClick={() => navigate(`/${f.path}`)}
            id={`feature-${f.path}`}
          >
            <div className="feature-card-icon">{f.icon}</div>
            <div className="feature-card-title">{f.title}</div>
            <div className="feature-card-desc">
              {getFeatureDescription(f.plugin)}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Jobs */}
      {recentJobs.length > 0 && (
        <>
          <h3 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
            Recent Jobs
          </h3>
          <div className="card">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={thStyle}>ID</th>
                  <th style={thStyle}>Plugin</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Progress</th>
                </tr>
              </thead>
              <tbody>
                {recentJobs.map(job => (
                  <tr key={job.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={tdStyle}><code>{job.id}</code></td>
                    <td style={tdStyle}>{job.plugin}</td>
                    <td style={tdStyle}>
                      <span className={`status-badge ${job.status}`}>{job.status}</span>
                    </td>
                    <td style={tdStyle}>{Math.round(job.progress)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

const thStyle = {
  textAlign: 'left', padding: '10px 14px',
  fontSize: '0.75rem', fontWeight: 600,
  color: 'var(--text-tertiary)', textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

const tdStyle = { padding: '10px 14px', fontSize: '0.875rem' };

function getFeatureDescription(plugin) {
  const descriptions = {
    background_removal: 'Remove backgrounds with hair-aware matting and custom replacement.',
    face_enhancement: 'Enhance faces with GFPGAN — sharpen eyes, smooth skin, fix blur.',
    upscaling: 'Upscale images 2x-8x with Real-ESRGAN and face-aware enhancement.',
    object_removal: 'Remove unwanted objects using AI inpainting with brush tools.',
    watermark_removal: 'Auto-detect and remove watermarks and text overlays.',
    color_grading: 'Professional color grading with cinematic, wedding, and custom presets.',
    style_transfer: 'Transform photo styles with Stable Diffusion and LoRA support.',
    cartoon_anime: 'Convert photos to cartoon or anime style.',
    headshot_generator: 'Generate professional headshots for corporate and LinkedIn.',
    wedding_studio: 'Batch process wedding albums with consistent styling.',
  };
  return descriptions[plugin] || '';
}
