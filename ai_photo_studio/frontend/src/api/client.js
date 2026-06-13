import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 min for long operations
});

// Upload API
export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const uploadBatch = async (files) => {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  const { data } = await api.post('/upload/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

// Jobs API
export const submitJob = async (plugin, fileIds, params = {}) => {
  const { data } = await api.post('/jobs', {
    plugin,
    file_ids: fileIds,
    params,
    is_batch: fileIds.length > 1,
  });
  return data;
};

export const getJob = async (jobId) => {
  const { data } = await api.get(`/jobs/${jobId}`);
  return data;
};

export const listJobs = async (limit = 50, offset = 0) => {
  const { data } = await api.get('/jobs', { params: { limit, offset } });
  return data;
};

export const cancelJob = async (jobId) => {
  const { data } = await api.delete(`/jobs/${jobId}`);
  return data;
};

// Presets API
export const listPresets = async (plugin = null) => {
  const params = plugin ? { plugin } : {};
  const { data } = await api.get('/presets', { params });
  return data;
};

export const createPreset = async (preset) => {
  const { data } = await api.post('/presets', preset);
  return data;
};

export const deletePreset = async (presetId) => {
  const { data } = await api.delete(`/presets/${presetId}`);
  return data;
};

// Models API
export const listModels = async () => {
  const { data } = await api.get('/models');
  return data;
};

export const downloadModel = async (modelName) => {
  const { data } = await api.post(`/models/${modelName}/download`);
  return data;
};

export const deleteModel = async (modelName) => {
  const { data } = await api.delete(`/models/${modelName}`);
  return data;
};

export const getVramStatus = async () => {
  const { data } = await api.get('/models/vram');
  return data;
};

export const unloadAllModels = async () => {
  const { data } = await api.post('/models/unload-all');
  return data;
};

// Settings API
export const getSettings = async () => {
  const { data } = await api.get('/settings');
  return data;
};

export const getSystemInfo = async () => {
  const { data } = await api.get('/settings/system');
  return data;
};

// Plugins API
export const getPluginInfo = async () => {
  const { data } = await api.get('/info');
  return data;
};

export default api;
