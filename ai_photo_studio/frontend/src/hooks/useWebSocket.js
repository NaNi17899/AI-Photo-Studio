import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * WebSocket hook for real-time job progress updates.
 */
export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [jobs, setJobs] = useState({});
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // Start ping interval
      reconnectRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'job_progress') {
          setJobs(prev => ({
            ...prev,
            [data.job.id]: data.job,
          }));
        } else if (data.type === 'initial_state') {
          const initial = {};
          data.active_jobs.forEach(j => { initial[j.id] = j; });
          setJobs(prev => ({ ...prev, ...initial }));
        }
      } catch (e) {
        // Ignore parse errors (pong, etc.)
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (reconnectRef.current) clearInterval(reconnectRef.current);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearInterval(reconnectRef.current);
    };
  }, [connect]);

  const getJobProgress = useCallback((jobId) => {
    return jobs[jobId] || null;
  }, [jobs]);

  return { connected, jobs, getJobProgress };
}

/**
 * Hook for managing a single processing job.
 */
export function useJob() {
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const reset = useCallback(() => {
    setUploading(false);
    setProcessing(false);
    setUploadedFile(null);
    setJobId(null);
    setResult(null);
    setError(null);
  }, []);

  return {
    uploading, setUploading,
    processing, setProcessing,
    uploadedFile, setUploadedFile,
    jobId, setJobId,
    result, setResult,
    error, setError,
    reset,
  };
}
