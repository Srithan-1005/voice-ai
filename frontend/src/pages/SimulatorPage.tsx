import React, { useState, useRef, useEffect } from 'react';
import { startSimulation, sendMessage, resetSimulation } from '../services/api';
import type { SimulationSession, SimulationMessageResponse, ChecklistItemDetail, QualificationState } from '../types';
import { ChecklistPanel } from '../components/ChecklistPanel';
import { StatusBadge } from '../components/StatusBadge';
import { PRESET_SCENARIOS, formatCurrency } from '../utils/helpers';
import { Send, RotateCcw, Zap, Info, MessageSquare, ChevronDown, ChevronRight, AlertTriangle, ArrowRight, Clock } from 'lucide-react';

// ─── helpers ────────────────────────────────────────────────────────────────

function FieldRow({ label, value, highlight }: { label: string; value: React.ReactNode; highlight?: 'green' | 'amber' | 'red' }) {
  const colors: Record<string, string> = {
    green: '#10b981',
    amber: '#f59e0b',
    red:   '#ef4444',
  };
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: 12, padding: '3px 0', borderBottom: '1px solid #f1f5f9' }}>
      <span style={{ color: '#64748b', flexShrink: 0 }}>{label}</span>
      <span style={{ fontWeight: 500, color: highlight ? colors[highlight] : '#1e293b', textAlign: 'right', maxWidth: 180 }}>{value ?? '—'}</span>
    </div>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 14, marginBottom: 6 }}>
      {title}
    </div>
  );
}

function Tag({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span style={{ display: 'inline-block', background: color + '18', color, border: `1px solid ${color}40`, borderRadius: 4, padding: '1px 6px', fontSize: 11, fontWeight: 600, marginRight: 4, marginBottom: 4 }}>
      {children}
    </span>
  );
}

function PendingFields({ items }: { items: string[] }) {
  if (!items.length) return <Tag color="#10b981">All captured ✓</Tag>;
  const labels: Record<string, string> = {
    property_type:              'Property Type',
    ownership_status:           'Ownership',
    original_documents:         'Original Docs',
    loan_amount:                'Loan Amount',
    occupation_and_income_mode: 'Occupation & Income',
    market_value:               'Market Value',
    tenure_years:               'Tenure',
  };
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap' }}>
      {items.map(k => <Tag key={k} color="#f59e0b">{labels[k] ?? k}</Tag>)}
    </div>
  );
}

// ─── captured values panel ───────────────────────────────────────────────────

function CapturedValues({ state }: { state: QualificationState }) {
  return (
    <>
      <SectionHeader title="Captured Values" />
      <FieldRow label="Property Type"  value={state.property_type} highlight={state.property_type ? 'green' : undefined} />
      <FieldRow label="Ownership"      value={state.ownership_status} highlight={state.ownership_status ? 'green' : undefined} />
      <FieldRow label="Original Docs"  value={
        state.original_documents_available === true  ? '✓ Available' :
        state.original_documents_available === false ? '✗ Not available' :
        state.original_documents_uncertain           ? '? Uncertain' : null
      } highlight={
        state.original_documents_available === true  ? 'green' :
        state.original_documents_available === false ? 'red'   :
        state.original_documents_uncertain           ? 'amber' : undefined
      } />
      <FieldRow label="Market Value"   value={formatCurrency(state.market_value)} highlight={state.market_value ? 'green' : undefined} />
      <FieldRow label="Loan Requested" value={formatCurrency(state.loan_amount_requested)} highlight={state.loan_amount_requested ? 'green' : undefined} />
      <FieldRow label="Loan Confirmed" value={formatCurrency(state.loan_amount_confirmed)} highlight={state.loan_amount_confirmed ? 'green' : undefined} />
      <FieldRow label="Occupation"     value={state.occupation} highlight={state.occupation ? 'green' : undefined} />
      <FieldRow label="Income Mode"    value={state.income_mode} highlight={
        state.income_mode?.toLowerCase() === 'cash' ? 'red' :
        state.income_mode ? 'green' : undefined
      } />
      <FieldRow label="Tenure"         value={state.tenure_years ? `${state.tenure_years} years` : null} highlight={state.tenure_years ? 'green' : undefined} />
    </>
  );
}

// ─── session state panel ─────────────────────────────────────────────────────

function SessionStatePanel({
  state,
  checklist,
  outcome,
  explanation,
  missingItems,
}: {
  state: QualificationState;
  checklist: ChecklistItemDetail[];
  outcome: string;
  explanation: string;
  missingItems: string[];
}) {
  const [showChecklist, setShowChecklist] = useState(true);
  const [showState, setShowState] = useState(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* Status */}
      <div className="card" style={{ padding: '14px 16px' }}>
        <SectionHeader title="Qualification Status" />
        <div style={{ marginBottom: 8 }}>
          <StatusBadge status={outcome as never} />
        </div>

        {state.disqualified && state.disqualification_reason && (
          <div style={{ display: 'flex', gap: 8, background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '8px 10px', marginTop: 8 }}>
            <AlertTriangle size={14} color="#ef4444" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ fontSize: 11, color: '#991b1b', lineHeight: 1.5 }}>{state.disqualification_reason}</span>
          </div>
        )}

        {state.transfer_required && (
          <div style={{ display: 'flex', gap: 8, background: '#eff6ff', border: '1px solid #93c5fd', borderRadius: 8, padding: '8px 10px', marginTop: 8 }}>
            <ArrowRight size={14} color="#3b82f6" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ fontSize: 11, color: '#1e40af', lineHeight: 1.5 }}>
              <strong>Transfer Required:</strong> {state.transfer_reason || 'Existing loan / EMI reduction'}
            </span>
          </div>
        )}

        {state.customer_busy && state.callback_time && (
          <div style={{ display: 'flex', gap: 8, background: '#fefce8', border: '1px solid #fde047', borderRadius: 8, padding: '8px 10px', marginTop: 8 }}>
            <Clock size={14} color="#ca8a04" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ fontSize: 11, color: '#854d0e', lineHeight: 1.5 }}>
              Callback: {state.callback_time}
            </span>
          </div>
        )}
      </div>

      {/* Captured values + pending fields */}
      <div className="card" style={{ padding: '14px 16px' }}>
        <CapturedValues state={state} />

        <SectionHeader title="Pending Fields" />
        <PendingFields items={missingItems} />

        {state.pending_clarifications?.length > 0 && (
          <>
            <SectionHeader title="Needs Clarification" />
            <div style={{ display: 'flex', flexWrap: 'wrap' }}>
              {state.pending_clarifications.map((c, i) => (
                <Tag key={i} color="#f59e0b">{c}</Tag>
              ))}
            </div>
          </>
        )}

        <SectionHeader title="Progress" />
        <FieldRow label="Answered"   value={`${state.answered_items.length} / 7`} highlight={state.answered_items.length === 7 ? 'green' : 'amber'} />
        <FieldRow label="Verified"   value={state.customer_verified ? '✓ Yes' : '✗ No'} highlight={state.customer_verified ? 'green' : 'amber'} />
        <FieldRow label="Call Ended" value={state.call_ended ? 'Yes' : 'No'} />
        {state.excess_loan_offer_pending && (
          <FieldRow label="Excess Loan Offer" value="Pending acceptance" highlight="amber" />
        )}
      </div>

      {/* Decision explanation */}
      {explanation && (
        <div className="card" style={{ borderLeft: '3px solid #27ab83', padding: '12px 14px' }}>
          <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
            <Info size={13} color="#27ab83" style={{ flexShrink: 0, marginTop: 2 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#334e68' }}>Decision Explanation</span>
          </div>
          <div style={{ fontSize: 11, color: '#486581', lineHeight: 1.6 }}>{explanation}</div>
        </div>
      )}

      {/* Checklist */}
      <div className="card" style={{ padding: '12px 14px' }}>
        <button
          onClick={() => setShowChecklist(s => !s)}
          style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: 11, fontWeight: 700, color: '#334e68', letterSpacing: '0.05em', textTransform: 'uppercase' }}
        >
          {showChecklist ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          Eligibility Checklist
        </button>
        {showChecklist && <div style={{ marginTop: 10 }}><ChecklistPanel items={checklist} compact /></div>}
      </div>

      {/* Raw JSON state */}
      <div className="card" style={{ padding: '12px 14px' }}>
        <button
          onClick={() => setShowState(s => !s)}
          style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: 11, fontWeight: 700, color: '#334e68', letterSpacing: '0.05em', textTransform: 'uppercase' }}
        >
          {showState ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          Raw State (JSON)
        </button>
        {showState && (
          <pre style={{
            marginTop: 10, fontSize: 10, color: '#475569', background: '#f8fafc',
            borderRadius: 6, padding: 10, overflowX: 'auto', maxHeight: 300,
            lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
          }}>
            {JSON.stringify({
              property_type: state.property_type,
              ownership_status: state.ownership_status,
              original_documents_available: state.original_documents_available,
              market_value: state.market_value,
              loan_amount_requested: state.loan_amount_requested,
              loan_amount_confirmed: state.loan_amount_confirmed,
              occupation: state.occupation,
              income_mode: state.income_mode,
              tenure_years: state.tenure_years,
              answered_items: state.answered_items,
              pending_clarifications: state.pending_clarifications,
              qualification_status: state.qualification_status,
              disqualified: state.disqualified,
              disqualification_reason: state.disqualification_reason,
              transfer_required: state.transfer_required,
              transfer_reason: state.transfer_reason,
              call_ended: state.call_ended,
              excess_loan_offer_pending: state.excess_loan_offer_pending,
            }, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

// ─── main page ───────────────────────────────────────────────────────────────

export const SimulatorPage: React.FC = () => {
  const [session, setSession] = useState<SimulationSession | null>(null);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [checklist, setChecklist] = useState<ChecklistItemDetail[]>([]);
  const [missingItems, setMissingItems] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [customerName, setCustomerName] = useState('Rajesh Kumar');
  const [language, setLanguage] = useState('English');
  const [explanation, setExplanation] = useState('');
  const [outcome, setOutcome] = useState<string>('');
  const [callEnded, setCallEnded] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [liveState, setLiveState] = useState<QualificationState | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const initSession = async () => {
    setInitializing(true);
    setMessages([]);
    setChecklist([]);
    setMissingItems([]);
    setCallEnded(false);
    setExplanation('');
    setOutcome('');
    setLiveState(null);
    try {
      const sess = await startSimulation({ customer_name: customerName, language });
      setSession(sess);
      setChecklist(sess.checklist);
      setMissingItems(sess.missing_items);
      setOutcome(sess.outcome);
      setExplanation(sess.decision_explanation);
      setLiveState(sess.state);
      setMessages([{ role: 'agent', content: sess.initial_message }]);
    } finally {
      setInitializing(false);
    }
  };

  const handleSend = async (text?: string) => {
    const msgText = text ?? input.trim();
    if (!msgText || !session || loading || callEnded) return;

    setInput('');
    setMessages(m => [...m, { role: 'customer', content: msgText }]);
    setLoading(true);
    setIsTyping(true);

    try {
      const resp: SimulationMessageResponse = await sendMessage(session.session_id, msgText);
      setIsTyping(false);
      setMessages(m => [...m, { role: 'agent', content: resp.agent_response }]);
      setChecklist(resp.checklist);
      setMissingItems(resp.missing_items);
      setOutcome(resp.outcome);
      setExplanation(resp.decision_explanation);
      setCallEnded(resp.call_ended);
      setLiveState(resp.state);
      setSession(s => s ? { ...s, state: resp.state } : s);
    } catch {
      setIsTyping(false);
      setMessages(m => [...m, { role: 'agent', content: '⚠ Error reaching backend. Is the server running?' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!session) { initSession(); return; }
    const sess = await resetSimulation(session.session_id);
    setSession(sess);
    setMessages([{ role: 'agent', content: sess.initial_message }]);
    setChecklist(sess.checklist);
    setMissingItems(sess.missing_items);
    setOutcome(sess.outcome);
    setExplanation(sess.decision_explanation);
    setCallEnded(false);
    setLiveState(sess.state);
  };

  const runPreset = async (preset: typeof PRESET_SCENARIOS[0]) => {
    setInitializing(true);
    setMessages([]);
    setChecklist([]);
    setMissingItems([]);
    setCallEnded(false);
    setLiveState(null);
    try {
      const sess = await startSimulation({ customer_name: 'Test Customer', language });
      setSession(sess);
      setLiveState(sess.state);
      setMessages([{ role: 'agent', content: sess.initial_message }]);

      const currentSession = sess.session_id;
      for (const msg of preset.messages) {
        await new Promise(r => setTimeout(r, 200));
        const resp = await sendMessage(currentSession, msg);
        setMessages(m => [...m, { role: 'customer', content: msg }, { role: 'agent', content: resp.agent_response }]);
        setChecklist(resp.checklist);
        setMissingItems(resp.missing_items);
        setOutcome(resp.outcome);
        setExplanation(resp.decision_explanation);
        setCallEnded(resp.call_ended);
        setLiveState(resp.state);
        if (resp.call_ended) break;
      }
    } finally {
      setInitializing(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>
          Conversation Simulator
        </h1>
        <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ background: '#fef3c7', color: '#92400e', padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>
            🎭 SIMULATION MODE
          </span>
          Text-based test of the qualification conversation engine (not a real phone call)
        </p>
      </div>

      {/* Setup bar */}
      {!session && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: 12, alignItems: 'flex-end' }}>
            <div>
              <label className="label">Customer Name</label>
              <input
                className="input-field"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
                placeholder="Rajesh Kumar"
              />
            </div>
            <div>
              <label className="label">Language</label>
              <select className="input-field" value={language} onChange={e => setLanguage(e.target.value)}>
                <option>English</option>
                <option>Hindi</option>
              </select>
            </div>
            <button className="btn-primary" onClick={initSession} disabled={initializing}>
              {initializing ? '…' : <><MessageSquare size={15} /> Start</>}
            </button>
          </div>

          {/* Preset scenarios */}
          <div style={{ marginTop: 16 }}>
            <div className="label">Quick Preset Scenarios</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {PRESET_SCENARIOS.map(p => (
                <button
                  key={p.id}
                  className="btn-secondary"
                  onClick={() => runPreset(p)}
                  disabled={initializing}
                  style={{ fontSize: 12 }}
                  title={p.description}
                >
                  <Zap size={12} /> {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {session && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
          {/* Chat area */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 700, padding: 0 }}>
            {/* Chat header */}
            <div style={{
              padding: '14px 20px', borderBottom: '1px solid #e2e8f0',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: callEnded ? '#ef4444' : '#10b981' }} />
                <span style={{ fontWeight: 600, fontSize: 13, color: '#243b53' }}>
                  {session.state.customer_name} — LAP Qualification
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {outcome && <StatusBadge status={outcome as never} />}
                <button className="btn-secondary" onClick={handleReset} style={{ fontSize: 12, padding: '5px 10px' }}>
                  <RotateCcw size={12} /> Reset
                </button>
              </div>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {messages.map((msg, i) => (
                <div key={i} className="animate-fade-in" style={{ display: 'flex', justifyContent: msg.role === 'customer' ? 'flex-end' : 'flex-start' }}>
                  {msg.role === 'agent' && (
                    <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#effcf6', border: '1px solid #8eedc7', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8, flexShrink: 0, fontSize: 12 }}>
                      🤖
                    </div>
                  )}
                  <div className={msg.role === 'agent' ? 'chat-bubble-agent' : 'chat-bubble-customer'}>
                    {msg.content}
                  </div>
                  {msg.role === 'customer' && (
                    <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#f0f4f8', border: '1px solid #bcccdc', display: 'flex', alignItems: 'center', justifyContent: 'center', marginLeft: 8, flexShrink: 0, fontSize: 12 }}>
                      👤
                    </div>
                  )}
                </div>
              ))}
              {isTyping && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#effcf6', border: '1px solid #8eedc7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12 }}>🤖</div>
                  <div className="chat-bubble-agent" style={{ padding: '10px 14px' }}>
                    <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                  </div>
                </div>
              )}
              {callEnded && (
                <div style={{ textAlign: 'center', padding: '12px 16px', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13, color: '#627d98', margin: '8px 0' }}>
                  📞 Call ended — <button className="btn-secondary" onClick={handleReset} style={{ fontSize: 12, display: 'inline-flex', padding: '4px 10px', marginLeft: 8 }}>Start New Simulation</button>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            {!callEnded && (
              <div style={{ padding: '12px 16px', borderTop: '1px solid #e2e8f0', display: 'flex', gap: 8 }}>
                <input
                  className="input-field"
                  style={{ flex: 1 }}
                  placeholder="Type your response as the customer…"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !loading && handleSend()}
                  disabled={loading || callEnded}
                />
                <button
                  className="btn-primary"
                  onClick={() => handleSend()}
                  disabled={loading || !input.trim() || callEnded}
                  style={{ padding: '0 16px' }}
                >
                  <Send size={15} />
                </button>
              </div>
            )}
          </div>

          {/* Right panel: full structured state */}
          {liveState && (
            <div style={{ overflowY: 'auto', maxHeight: 700 }}>
              <SessionStatePanel
                state={liveState}
                checklist={checklist}
                outcome={outcome}
                explanation={explanation}
                missingItems={missingItems}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
