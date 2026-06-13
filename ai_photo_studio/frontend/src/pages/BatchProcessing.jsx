import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { uploadBatch, submitJob, getJob } from '../api/client';
import ImageUploader from '../components/ImageUploader';
import ProgressBar from '../components/ProgressBar';

export default function BatchProcessing({ features, ws }) {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedPlugin, setSelectedPlugin] = useState('background_removal');
  const [processing, setProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [results, setResults] = useState([]);

  const handleFilesSelected = useCallback(async (selectedFiles) => {
    const fileList = Array.isArray(selectedFiles) ? selectedFiles : [selectedFiles];
    setFiles(fileList);

    try {
      toast('Uploading files...');
      const result = await uploadBatch(fileList);
      const uploaded = result.results.filter(r => !r.error);
      setUploadedFiles(uploaded);
      toast.success(`Uploaded ${uploaded.length}/${fileList.length} files`);
    } catch (err) {
      toast.error('Batch upload failed');
    }
  }, []);

  const handleProcessBatch = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload files first');
      return;
    }

    setProcessing(true);
    setBatchProgress(0);
    setResults([]);

    try {
      const fileIds = uploadedFiles.map(f => f.file_id);
      const result = await submitJob(selectedPlugin, fileIds, {});

      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const job = await getJob(result.job_id);
          setBatchProgress(job.progress || 0);

          if (job.status === 'completed') {
            clearInterval(poll);
            setProcessing(false);
            setResults(job.output_files || []);
            toast.success(`Batch complete! ${job.output_files?.length || 0} files processed`);
          } else if (job.status === 'failed') {
            clearInterval(poll);
            setProcessing(false);
            toast.error(job.error || 'Batch processing failed');
          }
        } catch {}
      }, 2000);

      setTimeout(() => clearInterval(poll), 600000); // 10 min timeout
    } catch (err) {
      setProcessing(false);
      toast.error('Failed to start batch processing');
    }
  };

  return (
    <div className="fade-in">
      <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
        📦 Batch Processing
      </h2>
      <p className="text-muted mb-lg">
        Upload multiple images and apply the same AI processing to all of them at once.
      </p>

      <div className="grid-2">
        <div className="flex flex-col gap-lg">
          <ImageUploader onUpload={handleFilesSelected} multiple={true} label="Upload Multiple Images" />

          {uploadedFiles.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-md)', fontWeight: 600 }}>
                Uploaded Files ({uploadedFiles.length})
              </h3>
              <div className="flex flex-col gap-sm" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {uploadedFiles.map(f => (
                  <div key={f.file_id} className="flex items-center gap-md" style={{
                    padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)',
                  }}>
                    <span>📄</span>
                    <span className="text-sm">{f.original_name}</span>
                    <span className="text-xs text-muted" style={{ marginLeft: 'auto' }}>
                      {f.width}×{f.height}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-lg">
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-md)', fontWeight: 600 }}>Operation</h3>

            <div className="input-group mb-md">
              <label className="input-label">Select AI Tool</label>
              <select
                className="select-field w-full"
                value={selectedPlugin}
                onChange={e => setSelectedPlugin(e.target.value)}
              >
                {features.map(f => (
                  <option key={f.plugin} value={f.plugin}>
                    {f.icon} {f.title}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="btn btn-primary w-full btn-lg"
              onClick={handleProcessBatch}
              disabled={uploadedFiles.length === 0 || processing}
            >
              {processing ? '⏳ Processing...' : `▶ Process ${uploadedFiles.length} Images`}
            </button>
          </div>

          {processing && (
            <ProgressBar progress={batchProgress} message={`Batch processing...`} status="running" />
          )}

          {results.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-md)', fontWeight: 600 }}>
                ✅ Results ({results.length} files)
              </h3>
              <div className="flex flex-col gap-sm" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {results.map((path, idx) => {
                  const filename = path.split(/[/\\]/).pop();
                  return (
                    <div key={idx} className="flex items-center justify-between" style={{
                      padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)',
                    }}>
                      <span className="text-sm">{filename}</span>
                      <a href={`/outputs/${filename}`} download className="btn btn-sm btn-secondary">
                        ⬇ Download
                      </a>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
