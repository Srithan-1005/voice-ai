import React, { useEffect, useState } from 'react';
import { getCalls, getCallById } from '../services/api';
import type { CallRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatTimestamp, formatDuration } from '../utils/helpers';
import { Phone, Filter, X, FileText, RefreshCw, Volume2 } from 'lucide-react';

const OUTCOMES = ['ALL', 'QUALIFIED', 'NOT_ELIGIBLE', 'LOAN_TRANSFER', 'CALLBACK_REQUESTED', 'CUSTOMER_DECLINED', 'IN_PROGRESS'];

interface CallLogsPageProps {
  initialSelectedCallId?: string | null;
}

export const CallLogsPage: React.FC<CallLogsPageProps> = ({ initialSelectedCallId }) => {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [selected, setSelected] = useState<CallRecord | null>(null);
  const [syncing, setSyncing] = useState(false);

  const maskPhone = (phone?: string | null) => {
    if (!phone) return '—';
    if (phone.length < 8) return phone;
    return `${phone.slice(0, 4)} *** **${phone.slice(-3)}`;
  };

  const fetchCalls = async () => {
    setLoading(true);
    try {
      const result = await getCalls(filter !== 'ALL' ? filter : undefined);
      setCalls(result.calls);
      if (initialSelectedCallId) {
        const found = result.calls.find(c => c.call_id === initialSelectedCallId);
        if (found) {
          handleViewDetail(found.call_id);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [filter, initialSelectedCallId]);

  const handleViewDetail = async (callId: string) => {
    try {
      const detail = await getCallById(callId);
      setSelected(detail);
    } catch (e) {
      console.error('Failed to fetch call detail', e);
    }
  };

  const handleSyncCall = async () => {
    if (!selected) return;
    setSyncing(true);
    try {
      const updated = await getCallById(selected.call_id);
      setSelected(updated);
      // update in table
      setCalls(prev => prev.map(c => c.call_id === updated.call_id ? updated : c));
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>Call Logs</h1>
          <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
            Authentic call records, verified transcripts, and actual audio recordings from Retell AI and simulator
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            className="btn-secondary"
            onClick={fetchCalls}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}
          >
            <RefreshCw size={12} /> Refresh
          </button>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Filter size={14} color="#627d98" />
            <select
              className="input-field"
              value={filter}
              onChange={e => setFilter(e.target.value)}
              style={{ width: 'auto' }}
            >
              {OUTCOMES.map(o => (
                <option key={o} value={o}>
                  {o === 'ALL' ? 'All Outcomes' : o.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>Loading call records…</div>
      ) : calls.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <Phone size={48} style={{ color: '#cbd5e1', margin: '0 auto 16px', display: 'block' }} />
          <div style={{ fontWeight: 600, color: '#334e68', marginBottom: 6 }}>No call records found</div>
          <div style={{ fontSize: 13, color: '#94a3b8' }}>
            {filter !== 'ALL' ? `No calls with outcome "${filter}"` : 'Start a test call or run a simulation to generate records.'}
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  {['Call ID', 'Customer', 'Phone Number', 'Type', 'Status', 'Timestamp', 'Duration', 'Outcome', 'Actions'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#627d98', fontSize: 11, textTransform: 'uppercase' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {calls.map((call) => (
                  <tr
                    key={call.call_id}
                    style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
                    onClick={() => handleViewDetail(call.call_id)}
                  >
                    <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#475569' }}>
                      {call.call_id.length > 20 ? `${call.call_id.slice(0, 18)}…` : call.call_id}
                    </td>
                    <td style={{ padding: '10px 16px', fontWeight: 500, color: '#243b53' }}>{call.customer_name}</td>
                    <td style={{ padding: '10px 16px', color: '#627d98', fontFamily: 'monospace', fontSize: 12 }}>
                      {maskPhone(call.phone_number)}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        fontSize: 11, padding: '2px 8px', borderRadius: 20, fontWeight: 600,
                        background: call.call_type === 'simulation' ? '#f1f5f9' : '#ffedd5',
                        color: call.call_type === 'simulation' ? '#334e68' : '#c2410c'
                      }}>
                        {call.call_type === 'simulation' ? '🎭 SIM' : '📞 RETELL'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        fontSize: 11, padding: '2px 8px', borderRadius: 12, fontWeight: 600,
                        background: call.call_status === 'ended' || call.call_status === 'completed' ? '#dcfce7' : call.call_status === 'failed' ? '#fee2e2' : '#e0f2fe',
                        color: call.call_status === 'ended' || call.call_status === 'completed' ? '#15803d' : call.call_status === 'failed' ? '#b91c1c' : '#0369a1'
                      }}>
                        {(call.call_status || 'completed').toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#627d98' }}>{formatTimestamp(call.timestamp)}</td>
                    <td style={{ padding: '10px 16px', color: '#627d98' }}>{formatDuration(call.duration_seconds)}</td>
                    <td style={{ padding: '10px 16px' }}><StatusBadge status={call.outcome} /></td>
                    <td style={{ padding: '10px 16px' }}>
                      <button
                        className="btn-secondary"
                        onClick={e => { e.stopPropagation(); handleViewDetail(call.call_id); }}
                        style={{ fontSize: 11, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                      >
                        <FileText size={12} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Call Detail Modal */}
      {selected && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(16,42,67,0.45)',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
          zIndex: 1000, padding: '40px 20px', overflowY: 'auto'
        }}>
          <div style={{
            background: 'white', borderRadius: 16, width: '100%', maxWidth: 760,
            boxShadow: '0 20px 60px rgba(0,0,0,0.22)', position: 'relative'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 17, color: '#102a43' }}>
                  {selected.customer_name}
                  <span style={{ fontSize: 13, fontWeight: 500, color: '#627d98', marginLeft: 8 }}>
                    ({maskPhone(selected.phone_number)})
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#627d98', marginTop: 2, fontFamily: 'monospace' }}>
                  Provider Call ID: {selected.call_id}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <button
                  className="btn-secondary"
                  onClick={handleSyncCall}
                  disabled={syncing}
                  style={{ fontSize: 12, padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  <RefreshCw size={12} className={syncing ? 'animate-spin' : ''} /> {syncing ? 'Syncing…' : 'Sync Retell'}
                </button>
                <StatusBadge status={selected.outcome} />
                <button
                  onClick={() => setSelected(null)}
                  style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: 4 }}
                >
                  <X size={20} color="#627d98" />
                </button>
              </div>
            </div>

            <div style={{ padding: '20px 24px', maxHeight: '74vh', overflowY: 'auto' }}>
              {/* Telephony status ribbon */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
                <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>CALL TYPE</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginTop: 2 }}>
                    {selected.call_type === 'simulation' ? 'Simulator' : 'Retell Outbound'}
                  </div>
                </div>
                <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>CALL STATUS</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginTop: 2 }}>
                    {(selected.call_status || 'completed').toUpperCase()}
                  </div>
                </div>
                <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>DURATION</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginTop: 2 }}>
                    {formatDuration(selected.duration_seconds)}
                  </div>
                </div>
                <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>STARTED AT</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginTop: 2 }}>
                    {selected.start_time ? formatTimestamp(selected.start_time) : formatTimestamp(selected.timestamp)}
                  </div>
                </div>
              </div>

              {/* Decision explanation */}
              {selected.decision_explanation && (
                <div style={{ marginBottom: 18, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#166534' }}>
                  <strong>Qualification Decision:</strong> {selected.decision_explanation}
                </div>
              )}

              {/* Disqualification / Transfer reason banners */}
              {selected.disqualification_reason && (
                <div style={{ marginBottom: 18, background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#991b1b' }}>
                  <strong>Disqualification Reason:</strong> {selected.disqualification_reason}
                </div>
              )}

              {selected.transfer_reason && (
                <div style={{ marginBottom: 18, background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#1e40af' }}>
                  <strong>Handoff / Routing:</strong> {selected.transfer_reason}
                </div>
              )}

              {/* Authentic Audio Player */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Volume2 size={14} /> AUDIO RECORDING
                </div>
                {selected.recording_url ? (
                  <div style={{ background: '#f8fafc', padding: 14, borderRadius: 10, border: '1px solid #e2e8f0' }}>
                    <audio controls src={selected.recording_url} style={{ width: '100%', marginBottom: 6 }}>
                      Your browser does not support audio playback.
                    </audio>
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      Authentic recording link:{' '}
                      <a href={selected.recording_url} target="_blank" rel="noreferrer" style={{ color: '#0284c7' }}>
                        Open audio URL
                      </a>
                    </div>
                  </div>
                ) : (
                  <div style={{ background: '#f8fafc', padding: 14, borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>
                    Recording not available yet (provider has not produced recording or call was locally simulated).
                  </div>
                )}
              </div>

              {/* Collected applicant fields */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', marginBottom: 8 }}>
                  EXTRACTED APPLICANT FACTS
                </div>
                {Object.keys(selected.collected_fields || {}).length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                    {Object.entries(selected.collected_fields).map(([k, v]) => v != null && (
                      <div key={k} style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px' }}>
                        <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          {k.replace(/_/g, ' ')}
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: '#334e68', marginTop: 2 }}>
                          {String(v)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>
                    No applicant facts extracted yet.
                  </div>
                )}
              </div>

              {/* Full verified transcript */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.06em', marginBottom: 8 }}>
                  CONVERSATION TRANSCRIPT ({selected.transcript ? selected.transcript.length : 0} TURNS)
                </div>
                {selected.transcript && selected.transcript.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 280, overflowY: 'auto' }}>
                    {selected.transcript.map((msg, i) => (
                      <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                        <span style={{
                          fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 12, flexShrink: 0,
                          background: msg.role === 'agent' ? '#effcf6' : '#f0f4f8',
                          color: msg.role === 'agent' ? '#065f46' : '#334e68'
                        }}>
                          {msg.role.toUpperCase()}
                        </span>
                        <span style={{ fontSize: 13, color: '#334e68', lineHeight: 1.5 }}>
                          {msg.content}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ background: '#f8fafc', padding: 14, borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>
                    Transcript not available yet. Call may still be in progress or pending provider transcription.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
