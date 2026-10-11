import axios from 'axios';
import type {
  AgentConfig,
  SimulationSession,
  SimulationMessageResponse,
  CallRecord,
  Analytics,
  TestSuiteResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Config
export const getConfig = () => api.get<AgentConfig>('/api/config').then(r => r.data);
export const updateConfig = (data: Partial<AgentConfig>) => api.put<{ success: boolean; config: AgentConfig }>('/api/config', data).then(r => r.data);

// Prompt
export const getPrompt = () => api.get<{ raw_prompt: string; rendered_preview: string }>('/api/prompt').then(r => r.data);
export const updatePrompt = (prompt: string) => api.put('/api/prompt', { prompt }).then(r => r.data);

export const startSimulation = (params: Record<string, unknown>) =>
  api.post<SimulationSession>('/api/simulations', params).then(r => r.data);

export const sendMessage = (sessionId: string, message: string) =>
  api.post<SimulationMessageResponse>(`/api/simulations/${sessionId}/messages`, { message }).then(r => r.data);

export const resetSimulation = (sessionId: string) =>
  api.post<SimulationSession>(`/api/simulations/${sessionId}/reset`).then(r => r.data);

export const getSimulation = (sessionId: string) =>
  api.get<SimulationSession>(`/api/simulations/${sessionId}`).then(r => r.data);

// Calls
export const getCalls = (outcome?: string) =>
  api.get<{ total: number; calls: CallRecord[] }>('/api/calls', { params: outcome && outcome !== 'ALL' ? { outcome } : {} }).then(r => r.data);

export const getCallById = (callId: string) =>
  api.get<CallRecord>(`/api/calls/${callId}`).then(r => r.data);

export const startRealCall = (data: import('../types').StartCallRequest) =>
  api.post<import('../types').StartCallResponse>('/api/calls/start', data).then(r => r.data);

export const getCallTranscript = (callId: string) =>
  api.get<import('../types').TranscriptResponse>(`/api/calls/${callId}/transcript`).then(r => r.data);

export const getCallRecording = (callId: string) =>
  api.get<import('../types').RecordingResponse>(`/api/calls/${callId}/recording`).then(r => r.data);

export const getAnalytics = () =>
  api.get<Analytics>('/api/calls/analytics').then(r => r.data);

// Tests
export const runTestSuite = () =>
  api.post<TestSuiteResponse>('/api/tests/run').then(r => r.data);

// Voice
export const getVoiceStatus = () =>
  api.get('/api/voice/status').then(r => r.data);

export const syncAgent = (params?: { agent_name?: string; voice_id?: string; language?: string }) =>
  api.post('/api/voice/sync-agent', params || {}).then(r => r.data);

export const startWebCall = (customerName?: string) =>
  api.post('/api/voice/web-call', { customer_name: customerName }).then(r => r.data);

export const healthCheck = () =>
  api.get('/health').then(r => r.data);

