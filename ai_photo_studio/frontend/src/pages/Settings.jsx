import { useState, useEffect } from 'react';
import { getSettings, getSystemInfo } from '../api/client';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [sysInfo, setSysInfo] = useState(null);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
    getSystemInfo().then(setSysInfo).catch(() => {});
  }, []);

  return (
    <div className="fade-in">
      <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
        ⚙️ Settings
      </h2>

      <div className="grid-2">
        {/* System Information */}
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-lg)', fontWeight: 600 }}>System Information</h3>
          {sysInfo && (
            <div className="flex flex-col gap-md">
              <InfoRow label="Platform" value={sysInfo.platform} />
              <InfoRow label="Python" value={sysInfo.python_version} />
              <InfoRow label="CPU" value={`${sysInfo.cpu.processor || 'Unknown'} (${sysInfo.cpu.cores_physical}C/${sysInfo.cpu.cores_logical}T)`} />
              <InfoRow label="CPU Usage" value={`${sysInfo.cpu.usage_percent}%`} />
              <InfoRow label="RAM" value={`${sysInfo.memory.available_gb} / ${sysInfo.memory.total_gb} GB (${sysInfo.memory.used_percent}% used)`} />
              <InfoRow label="Disk" value={`${sysInfo.disk.free_gb} GB free of ${sysInfo.disk.total_gb} GB`} />
              {sysInfo.gpu?.devices?.length > 0 && (
                <>
                  <InfoRow label="GPU" value={sysInfo.gpu.devices[0].name} />
                  <InfoRow label="VRAM" value={`${sysInfo.gpu.devices[0].total_vram_mb} MB total`} />
                  <InfoRow label="Compute" value={`Capability ${sysInfo.gpu.devices[0].compute_capability}`} />
                </>
              )}
            </div>
          )}
        </div>

        {/* App Settings */}
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-lg)', fontWeight: 600 }}>Application Settings</h3>
          {settings && (
            <div className="flex flex-col gap-md">
              <InfoRow label="App Version" value={settings.version} />
              <InfoRow label="GPU Device" value={settings.gpu.device} />
              <InfoRow label="Max VRAM" value={`${settings.gpu.max_vram_usage_mb} MB`} />
              <InfoRow label="Mixed Precision" value={settings.gpu.mixed_precision ? 'Enabled' : 'Disabled'} />
              <InfoRow label="Tile Size" value={`${settings.gpu.tile_size}px`} />
              <InfoRow label="Idle Unload" value={`${settings.gpu.idle_unload_seconds}s`} />
              <InfoRow label="Max Upload" value={`${settings.storage.max_upload_size_mb} MB`} />

              <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '8px 0' }} />

              <h4 style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>Storage</h4>
              {settings.storage.disk_usage && (
                <>
                  <InfoRow label="Uploads" value={`${settings.storage.disk_usage.uploads_mb} MB`} />
                  <InfoRow label="Outputs" value={`${settings.storage.disk_usage.outputs_mb} MB`} />
                  <InfoRow label="Models" value={`${settings.storage.disk_usage.models_mb} MB`} />
                  <InfoRow label="Total" value={`${settings.storage.disk_usage.total_mb} MB`} />
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Paths */}
      {settings && (
        <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
          <h3 style={{ marginBottom: 'var(--space-lg)', fontWeight: 600 }}>Storage Paths</h3>
          <div className="flex flex-col gap-sm">
            <PathRow label="Uploads" path={settings.storage.uploads_dir} />
            <PathRow label="Outputs" path={settings.storage.outputs_dir} />
            <PathRow label="Models" path={settings.storage.models_dir} />
          </div>
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between" style={{ padding: '4px 0' }}>
      <span className="text-sm text-muted">{label}</span>
      <span className="text-sm font-bold">{value}</span>
    </div>
  );
}

function PathRow({ label, path }) {
  return (
    <div className="flex items-center justify-between" style={{
      padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)',
    }}>
      <span className="text-sm font-bold">{label}</span>
      <code className="text-xs text-muted" style={{ fontFamily: 'monospace' }}>{path}</code>
    </div>
  );
}
