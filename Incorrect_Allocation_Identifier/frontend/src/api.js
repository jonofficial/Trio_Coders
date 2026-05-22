import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Health ──
export const fetchHealth = () => api.get('/health');

// ── Config ──
export const fetchConfig = () => api.get('/config');

// ── Runs ──
export const fetchRuns = (limit = 1) => api.get('/api/runs', { params: { limit } });

// ── Summary (needs run_id internally, but caller passes it) ──
export const fetchSummary = (runId) => api.get(`/api/summary/${runId}`);

// ── Exceptions ──
export const fetchExceptions = (params = {}) => api.get('/api/exceptions', { params });

// ── Top Violators ──
export const fetchTopViolators = (params = {}) => api.get('/api/violations/top-violators', { params });

// ── Rejected Rows ──
export const fetchRejected = (params = {}) => api.get('/api/rejected', { params });

// ── Trigger Pipeline ──
export const triggerPipeline = (body = {}) => api.post('/api/trigger', body);

// ── Run Status (polling) ──
export const fetchRunStatus = (runId) => api.get(`/api/run-status/${runId}`);

// ── Export CSV ──
export const getExportUrl = (runId) => `${import.meta.env.VITE_API_BASE_URL || ''}/api/export-exceptions?run_id=${runId}`;

export default api;
