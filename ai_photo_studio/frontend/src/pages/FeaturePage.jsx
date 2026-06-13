import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { uploadFile, submitJob, getJob, getPluginInfo } from '../api/client';
import ImageUploader from '../components/ImageUploader';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ProgressBar from '../components/ProgressBar';

/**
 * Generic feature page — used for all 10 AI tools.
 * Dynamically renders parameter controls based on the plugin's JSON Schema.
 */
export default function FeaturePage({ feature, ws }) {
  const [pluginSchema, setPluginSchema] = useState(null);
  const [params, setParams] = useState({});
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch plugin schema
  useEffect(() => {
    getPluginInfo().then(data => {
      const plugin = data.plugins?.find(p => p.name === feature.plugin);
      if (plugin) {
        setPluginSchema(plugin.params_schema);
        // Set defaults
        const defaults = {};
        Object.entries(plugin.params_schema?.properties || {}).forEach(([key, spec]) => {
          if (spec.default !== undefined) defaults[key] = spec.default;
        });
        setParams(defaults);
      }
    }).catch(() => {});
  }, [feature.plugin]);

  // Watch job progress via WebSocket
  useEffect(() => {
    if (jobId && ws?.jobs?.[jobId]) {
      const job = ws.jobs[jobId];
      setJobData(job);
      if (job.status === 'completed' && job.output_files?.length > 0) {
        const outputFile = job.output_files[0];
        const filename = outputFile.split(/[/\\]/).pop();
        setResultUrl(`/outputs/${filename}`);
        setLoading(false);
        toast.success('Processing complete!');
      } else if (job.status === 'failed') {
        setLoading(false);
        toast.error(job.error || 'Processing failed');
      }
    }
  }, [jobId, ws?.jobs]);

  const handleUpload = useCallback(async (file) => {
    try {
      setLoading(true);
      setResultUrl(null);
      setJobData(null);
      const result = await uploadFile(file);
      setUploadedFile(result);
      setPreviewUrl(`/api/upload/file/${result.file_id}`);
      setLoading(false);
      toast.success(`Uploaded: ${file.name}`);
    } catch (err) {
      setLoading(false);
      toast.error('Upload failed');
    }
  }, []);

  const handleProcess = useCallback(async () => {
    if (!uploadedFile) {
      toast.error('Please upload an image first');
      return;
    }
    try {
      setLoading(true);
      setResultUrl(null);
      const result = await submitJob(feature.plugin, [uploadedFile.file_id], params);
      setJobId(result.job_id);
      toast('Processing started...', { icon: '⏳' });

      // Fallback polling in case WebSocket misses updates
      const poll = setInterval(async () => {
        try {
          const job = await getJob(result.job_id);
          setJobData(job);
          if (job.status === 'completed') {
            clearInterval(poll);
            if (job.output_files?.length > 0) {
              const filename = job.output_files[0].split(/[/\\]/).pop();
              setResultUrl(`/outputs/${filename}`);
            }
            setLoading(false);
            toast.success('Processing complete!');
          } else if (job.status === 'failed') {
            clearInterval(poll);
            setLoading(false);
            toast.error(job.error || 'Processing failed');
          }
        } catch {}
      }, 2000);

      // Cleanup after 5 minutes max
      setTimeout(() => clearInterval(poll), 300000);
    } catch (err) {
      setLoading(false);
      toast.error('Failed to submit job');
    }
  }, [uploadedFile, feature.plugin, params]);

  const handleReset = () => {
    setUploadedFile(null);
    setPreviewUrl(null);
    setJobId(null);
    setJobData(null);
    setResultUrl(null);
    setLoading(false);
  };

  return (
    <div className="fade-in">
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>
            {feature.icon} {feature.title}
          </h2>
        </div>
        <button className="btn btn-ghost" onClick={handleReset}>🔄 Reset</button>
      </div>

      <div className="processing-layout">
        {/* Main Area */}
        <div className="processing-main">
          {!uploadedFile ? (
            <ImageUploader onUpload={handleUpload} />
          ) : (
            <>
              {/* Preview / Result */}
              {resultUrl && previewUrl ? (
                <BeforeAfterSlider beforeSrc={previewUrl} afterSrc={resultUrl} />
              ) : (
                <div className="image-preview">
                  <img src={previewUrl} alt="Uploaded" />
                  <div style={{
                    position: 'absolute', top: '10px', left: '10px',
                    padding: '4px 10px', background: 'rgba(0,0,0,0.6)',
                    borderRadius: '6px', fontSize: '12px', fontWeight: 600
                  }}>
                    {uploadedFile.width}×{uploadedFile.height} • {(uploadedFile.size_bytes / 1024).toFixed(0)} KB
                  </div>
                </div>
              )}

              {/* Progress */}
              {loading && jobData && (
                <ProgressBar
                  progress={jobData.progress || 0}
                  message={jobData.message || 'Processing...'}
                  status={jobData.status || 'running'}
                />
              )}

              {/* Result Actions */}
              {resultUrl && (
                <div className="flex gap-md">
                  <a href={resultUrl} download className="btn btn-primary btn-lg">
                    ⬇ Download Result
                  </a>
                  <button className="btn btn-secondary" onClick={() => {
                    setUploadedFile(null);
                    setPreviewUrl(null);
                    setResultUrl(null);
                  }}>
                    📁 Upload New Image
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Parameters Sidebar */}
        <div className="processing-sidebar">
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-lg)' }}>
              Parameters
            </h3>

            {pluginSchema?.properties && (
              <div className="flex flex-col gap-md">
                {Object.entries(pluginSchema.properties).map(([key, spec]) => (
                  <ParamControl
                    key={key}
                    name={key}
                    spec={spec}
                    value={params[key]}
                    onChange={(val) => setParams(prev => ({ ...prev, [key]: val }))}
                  />
                ))}
              </div>
            )}

            <button
              className="btn btn-primary w-full btn-lg"
              style={{ marginTop: 'var(--space-xl)' }}
              onClick={handleProcess}
              disabled={!uploadedFile || loading}
              id="process-button"
            >
              {loading ? '⏳ Processing...' : `▶ Process`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Dynamic parameter control renderer based on JSON Schema.
 */
function ParamControl({ name, spec, value, onChange }) {
  const label = spec.title || name;
  const description = spec.description || '';

  // Select / Enum
  if (spec.enum) {
    return (
      <div className="input-group">
        <label className="input-label" title={description}>{label}</label>
        <select
          className="select-field"
          value={value ?? spec.default}
          onChange={e => onChange(spec.type === 'integer' ? parseInt(e.target.value) : e.target.value)}
        >
          {spec.enum.map(opt => (
            <option key={opt} value={opt}>{String(opt)}</option>
          ))}
        </select>
      </div>
    );
  }

  // Slider for numbers with min/max
  if ((spec.type === 'number' || spec.type === 'integer') && spec.minimum !== undefined) {
    return (
      <div className="slider-container">
        <div className="slider-header">
          <label className="input-label" title={description}>{label}</label>
          <span className="text-xs text-muted">{value ?? spec.default}</span>
        </div>
        <input
          type="range"
          min={spec.minimum}
          max={spec.maximum}
          step={spec.type === 'integer' ? 1 : 0.05}
          value={value ?? spec.default}
          onChange={e => onChange(spec.type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value))}
        />
      </div>
    );
  }

  // Boolean toggle
  if (spec.type === 'boolean') {
    return (
      <div className="flex items-center justify-between" style={{ padding: '4px 0' }}>
        <label className="input-label" title={description}>{label}</label>
        <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px' }}>
          <input
            type="checkbox"
            checked={value ?? spec.default}
            onChange={e => onChange(e.target.checked)}
            style={{ opacity: 0, width: 0, height: 0 }}
          />
          <span style={{
            position: 'absolute', cursor: 'pointer', inset: 0,
            background: (value ?? spec.default) ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            borderRadius: '12px', transition: 'var(--transition-fast)',
          }}>
            <span style={{
              position: 'absolute', height: '18px', width: '18px',
              left: (value ?? spec.default) ? '23px' : '3px',
              bottom: '3px', background: 'white', borderRadius: '50%',
              transition: 'var(--transition-fast)',
            }} />
          </span>
        </label>
      </div>
    );
  }

  // Text input
  if (spec.type === 'string' && !spec.enum) {
    // Skip internal fields
    if (name === 'mask_data' || name === 'mask_path' || name === 'bg_image_path' || name === 'lora_path' || name === 'custom_bg_path') return null;
    return (
      <div className="input-group">
        <label className="input-label" title={description}>{label}</label>
        <input
          type="text"
          className="input-field"
          value={value ?? spec.default ?? ''}
          onChange={e => onChange(e.target.value)}
          placeholder={description}
        />
      </div>
    );
  }

  return null;
}
