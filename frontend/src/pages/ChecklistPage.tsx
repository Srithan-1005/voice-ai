import React, { useState } from 'react';
import { startSimulation, sendMessage } from '../services/api';
import type { ChecklistItemDetail } from '../types';
import { PRESET_SCENARIOS } from '../utils/helpers';
import { Zap, ClipboardList } from 'lucide-react';

export const ChecklistPage: React.FC = () => {
  const [checklist, setChecklist] = useState<ChecklistItemDetail[]>([]);
  const [loading, setLoading] = useState(false);

  const runPreset = async (preset: typeof PRESET_SCENARIOS[0]) => {
    setLoading(true);
    try {
      const sess = await startSimulation({ customer_name: 'Test Customer' });
      const currentId = sess.session_id;
      setChecklist(sess.checklist);

      for (const msg of preset.messages) {
        const resp = await sendMessage(currentId, msg);
        setChecklist(resp.checklist);
        if (resp.call_ended) break;
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>
          Eligibility Checklist Detail
        </h1>
        <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
          View all 7 checklist items, captured values, and eligibility interpretations
        </p>
      </div>

      {/* Load preset to populate */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-title">Load a Scenario to Inspect Checklist State</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {PRESET_SCENARIOS.map(p => (
            <button
              key={p.id}
              className="btn-secondary"
              onClick={() => runPreset(p)}
              disabled={loading}
              style={{ fontSize: 12 }}
              title={p.description}
            >
              <Zap size={12} /> {p.label}
            </button>
          ))}
        </div>
      </div>

      {checklist.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <ClipboardList size={48} style={{ color: '#cbd5e1', margin: '0 auto 16px', display: 'block' }} />
          <div style={{ fontWeight: 600, color: '#334e68', marginBottom: 6 }}>No active session</div>
          <div style={{ fontSize: 14, color: '#94a3b8' }}>
            Select a preset scenario above or use the Conversation Simulator to view checklist state
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {checklist.map(item => (
            <div
              key={item.item_number}
              className="card"
              style={{
                borderLeft: `4px solid ${
                  item.status === 'Answered' ? '#27ab83'
                  : item.status === 'Invalid' ? '#ef4444'
                  : item.status === 'Clarification Needed' ? '#f59e0b'
                  : '#e2e8f0'
                }`
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <div style={{
                  width: 26, height: 26, borderRadius: '50%',
                  background: item.status === 'Answered' ? '#d1fae5' : item.status === 'Invalid' ? '#fee2e2' : '#f1f5f9',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                  color: item.status === 'Answered' ? '#065f46' : item.status === 'Invalid' ? '#991b1b' : '#627d98',
                  flexShrink: 0,
                }}>
                  {item.item_number}
                </div>
                <span style={{ fontWeight: 600, fontSize: 14, color: '#243b53' }}>{item.name}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#627d98' }}>Status</span>
                  <span style={{
                    fontWeight: 600,
                    color: item.status === 'Answered' ? '#199473' : item.status === 'Invalid' ? '#dc2626' : item.status === 'Clarification Needed' ? '#d97706' : '#94a3b8'
                  }}>
                    {item.status}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#627d98' }}>Captured Value</span>
                  <span style={{ fontWeight: 500, color: '#334e68' }}>{item.captured_value ?? '—'}</span>
                </div>
                {item.clarification_needed && (
                  <div style={{ background: '#fef3c7', borderRadius: 8, padding: '6px 10px', fontSize: 12, color: '#92400e' }}>
                    ⚠ Clarification required before this item can be marked complete
                  </div>
                )}
                {item.interpretation && (
                  <div style={{ background: '#f8fafc', borderRadius: 8, padding: '6px 10px', fontSize: 12, color: '#486581' }}>
                    {item.interpretation}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
