import React, { useState, useEffect } from 'react';
import {
  PhoneCall,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Sparkles,
  ArrowRight
} from 'lucide-react';

import { startRealCall, startSimulation, getConfig } from '../services/api';
import type { AgentConfig, StartCallResponse } from '../types';

interface StartTestCallPageProps {
  onNavigateToSimulator?: (sessionId?: string) => void;
  onNavigateToCalls?: (callId?: string) => void;
}

export const StartTestCallPage: React.FC<StartTestCallPageProps> = ({
  onNavigateToSimulator,
  onNavigateToCalls
}) => {
  // Mode selection: 'simulator' or 'real_call'
  const [mode, setMode] = useState<'simulator' | 'real_call'>('simulator');
  const [config, setConfig] = useState<AgentConfig | null>(null);

  // Form state - 14 required fields
  const [customerName, setCustomerName] = useState('Rajesh Sharma');
  const [customerPhone, setCustomerPhone] = useState('+919876543210');
  const [language, setLanguage] = useState<'English' | 'Hindi'>('English');
  const [agentName, setAgentName] = useState('Ananya');
  const [agentGender, setAgentGender] = useState<'female' | 'male'>('female');

  const [propertyType, setPropertyType] = useState<string>('Residential');
  const [ownershipStatus, setOwnershipStatus] = useState<string>('Sole');
  const [originalDocs, setOriginalDocs] = useState<string>('Yes'); // 'Yes', 'No', 'Unknown'
  const [loanAmount, setLoanAmount] = useState<string>('4500000');
  const [occupation, setOccupation] = useState<string>('Salaried');
  const [incomeMode, setIncomeMode] = useState<string>('Bank');
  const [marketValue, setMarketValue] = useState<string>('12000000');
  const [tenureYears, setTenureYears] = useState<string>('10');
  const [existingLoan, setExistingLoan] = useState<string>('No'); // 'Yes', 'No'
  const [emiReduction, setEmiReduction] = useState<string>('No'); // 'Yes', 'No'

  // Safety confirmation for real call
  const [confirmedDestination, setConfirmedDestination] = useState(false);
  const [callMode, setCallMode] = useState<'phone' | 'web'>('phone');

  // Execution state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<StartCallResponse | null>(null);
  const [simSessionId, setSimSessionId] = useState<string | null>(null);

  useEffect(() => {
    getConfig().then(setConfig).catch(() => {});
  }, []);

  // Presets
  const applyPreset = (presetKey: string) => {
    setError(null);
    setSuccessResult(null);
    setSimSessionId(null);

    switch (presetKey) {
      case 'standard_qualified':
        setCustomerName('Rajesh Sharma');
        setCustomerPhone('+919876543210');
        setPropertyType('Residential');
        setOwnershipStatus('Joint');
        setOriginalDocs('Yes');
        setLoanAmount('4500000');
        setOccupation('Salaried');
        setIncomeMode('Bank');
        setMarketValue('12000000');
        setTenureYears('10');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
      case 'agricultural_disqualified':
        setCustomerName('Kisan Singh');
        setCustomerPhone('+919876543211');
        setPropertyType('Agricultural');
        setOwnershipStatus('Sole');
        setOriginalDocs('Yes');
        setLoanAmount('3000000');
        setOccupation('Self-employed');
        setIncomeMode('Bank');
        setMarketValue('8000000');
        setTenureYears('7');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
      case 'no_originals':
        setCustomerName('Vikram Verma');
        setCustomerPhone('+919876543212');
        setPropertyType('Residential');
        setOwnershipStatus('Sole');
        setOriginalDocs('No');
        setLoanAmount('5000000');
        setOccupation('Salaried');
        setIncomeMode('Bank');
        setMarketValue('10000000');
        setTenureYears('10');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
      case 'cash_income':
        setCustomerName('Manoj Gupta');
        setCustomerPhone('+919876543213');
        setPropertyType('Commercial');
        setOwnershipStatus('Sole');
        setOriginalDocs('Yes');
        setLoanAmount('2500000');
        setOccupation('Self-employed');
        setIncomeMode('Cash');
        setMarketValue('7500000');
        setTenureYears('5');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
      case 'loan_above_cap':
        setCustomerName('Pooja Mehta');
        setCustomerPhone('+919876543214');
        setPropertyType('Residential');
        setOwnershipStatus('Joint');
        setOriginalDocs('Yes');
        setLoanAmount('9000000'); // ₹90L > ₹75L cap
        setOccupation('Salaried');
        setIncomeMode('Bank');
        setMarketValue('25000000');
        setTenureYears('15');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
      case 'existing_loan_transfer':
        setCustomerName('Amitabh Roy');
        setCustomerPhone('+919876543215');
        setPropertyType('Residential');
        setOwnershipStatus('Sole');
        setOriginalDocs('Yes');
        setLoanAmount('4000000');
        setOccupation('Salaried');
        setIncomeMode('Bank');
        setMarketValue('11000000');
        setTenureYears('10');
        setExistingLoan('Yes'); // triggers specialist handoff
        setEmiReduction('No');
        break;
      case 'minimal_unknowns':
        setCustomerName('Sunil Rao');
        setCustomerPhone('+919876543216');
        setPropertyType('');
        setOwnershipStatus('');
        setOriginalDocs('Unknown');
        setLoanAmount('');
        setOccupation('');
        setIncomeMode('');
        setMarketValue('');
        setTenureYears('');
        setExistingLoan('No');
        setEmiReduction('No');
        break;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessResult(null);
    setSimSessionId(null);
    setLoading(true);

    const payload = {
      customer_name: customerName.trim() || undefined,
      customer_phone: customerPhone.trim(),
      language,
      agent_name: agentName.trim() || undefined,
      agent_gender: agentGender,
      property_type: propertyType || undefined,
      ownership_status: ownershipStatus || undefined,
      original_documents_available: originalDocs,
      loan_amount_requested: loanAmount ? parseFloat(loanAmount) : undefined,
      occupation: occupation || undefined,
      income_mode: incomeMode || undefined,
      market_value: marketValue ? parseFloat(marketValue) : undefined,
      tenure_years: tenureYears ? parseInt(tenureYears, 10) : undefined,
      existing_loan: existingLoan,
      emi_reduction_request: emiReduction,
    };

    try {
      if (mode === 'real_call') {
        if (!confirmedDestination) {
          setError('You must confirm destination authorization before placing a real phone call.');
          setLoading(false);
          return;
        }

        const res = await startRealCall({
          ...payload,
          call_mode: callMode,
          confirmed_destination: true,
        });
        setSuccessResult(res);
      } else {
        // Simulator mode
        const res = await startSimulation(payload);
        setSimSessionId(res.session_id);
        if (onNavigateToSimulator) {
          // Open simulator directly
          onNavigateToSimulator(res.session_id);
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Operation failed.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1040, margin: '0 auto', paddingBottom: 40 }}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#102a43', margin: 0 }}>
          Start Test Call
        </h1>
        <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
          Enter customer applicant details, configure call parameters, and test LAP qualification
          via interactive local simulator or authentic Retell AI telephony.
        </p>
      </div>

      {/* Mode Switcher Banner */}
      <div
        className="card"
        style={{
          padding: 16,
          marginBottom: 24,
          background: mode === 'real_call' ? '#fff7ed' : '#f0fdf4',
          border: mode === 'real_call' ? '2px solid #f97316' : '2px solid #10b981',
          display: 'flex',
          flexDirection: 'column',
          gap: 12
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {mode === 'real_call' ? (
              <div style={{ background: '#ea580c', color: 'white', padding: 8, borderRadius: 8, display: 'flex' }}>
                <PhoneCall size={20} />
              </div>
            ) : (
              <div style={{ background: '#10b981', color: 'white', padding: 8, borderRadius: 8, display: 'flex' }}>
                <MessageSquare size={20} />
              </div>
            )}
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: mode === 'real_call' ? '#9a3412' : '#065f46' }}>
                {mode === 'real_call' ? 'REAL RETELL AI VOICE CALL MODE' : 'CONVERSATION SIMULATOR MODE'}
              </div>
              <div style={{ fontSize: 12, color: mode === 'real_call' ? '#c2410c' : '#047857' }}>
                {mode === 'real_call'
                  ? 'Initiates an actual outbound phone call via Retell AI to the verified destination number.'
                  : 'Zero-cost conversational simulation. Type customer utterances and observe NLP extraction and deterministic rules.'}
              </div>
            </div>
          </div>

          {/* Toggle buttons */}
          <div style={{ display: 'flex', background: '#e2e8f0', borderRadius: 8, padding: 3 }}>
            <button
              type="button"
              onClick={() => { setMode('simulator'); setSuccessResult(null); setError(null); }}
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                border: 'none',
                fontWeight: 600,
                fontSize: 13,
                cursor: 'pointer',
                background: mode === 'simulator' ? '#10b981' : 'transparent',
                color: mode === 'simulator' ? 'white' : '#475569',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'all 0.2s'
              }}
            >
              <MessageSquare size={14} /> Simulator Mode
            </button>
            <button
              type="button"
              onClick={() => { setMode('real_call'); setSuccessResult(null); setError(null); }}
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                border: 'none',
                fontWeight: 600,
                fontSize: 13,
                cursor: 'pointer',
                background: mode === 'real_call' ? '#ea580c' : 'transparent',
                color: mode === 'real_call' ? 'white' : '#475569',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'all 0.2s'
              }}
            >
              <PhoneCall size={14} /> Real Call Mode
            </button>
          </div>
        </div>

        {/* Retell Config Status indicator when in real_call mode */}
        {mode === 'real_call' && (
          <div style={{ fontSize: 12, background: 'rgba(255,255,255,0.7)', padding: '8px 12px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span>
              <strong>Retell API Key:</strong>{' '}
              {config?.has_retell_key ? <span style={{ color: '#16a34a' }}>✓ Configured</span> : <span style={{ color: '#dc2626' }}>✗ Missing in .env</span>}
            </span>
            <span>
              <strong>Agent ID:</strong>{' '}
              {config?.retell_agent_id ? <span style={{ color: '#16a34a' }}>✓ {config.retell_agent_id.slice(0, 12)}…</span> : <span style={{ color: '#dc2626' }}>✗ Missing in .env</span>}
            </span>
            <span>
              <strong>From Number:</strong>{' '}
              {config?.retell_from_number ? <span style={{ color: '#16a34a' }}>✓ {config.retell_from_number}</span> : <span style={{ color: '#d97706' }}>⚠ None (Web Call fallback available)</span>}
            </span>
          </div>
        )}
      </div>

      {/* Preset Quick Fill Bar */}
      <div className="card" style={{ padding: 14, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#64748b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          <Sparkles size={14} color="#0284c7" /> Quick Test Presets:
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {[
            { id: 'standard_qualified', label: '✅ Full Qualification', color: '#065f46', bg: '#d1fae5' },
            { id: 'agricultural_disqualified', label: '❌ Agricultural Prop', color: '#991b1b', bg: '#fee2e2' },
            { id: 'no_originals', label: '❌ No Original Docs', color: '#991b1b', bg: '#fee2e2' },
            { id: 'cash_income', label: '❌ Cash-only Income', color: '#991b1b', bg: '#fee2e2' },
            { id: 'loan_above_cap', label: '⚠️ >₹75L High Loan', color: '#92400e', bg: '#fef3c7' },
            { id: 'existing_loan_transfer', label: '🔄 Existing Loan Handoff', color: '#1e40af', bg: '#dbeafe' },
            { id: 'minimal_unknowns', label: '❓ Blank/Unknown Info', color: '#334155', bg: '#f1f5f9' },
          ].map(p => (
            <button
              key={p.id}
              type="button"
              onClick={() => applyPreset(p.id)}
              style={{
                fontSize: 12,
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: 6,
                border: '1px solid rgba(0,0,0,0.08)',
                background: p.bg,
                color: p.color,
                cursor: 'pointer'
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="card" style={{ borderLeft: '4px solid #ef4444', background: '#fef2f2', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#991b1b', fontWeight: 600 }}>
            <AlertTriangle size={18} /> Operation Failed
          </div>
          <div style={{ fontSize: 13, color: '#b91c1c', marginTop: 4 }}>{error}</div>
        </div>
      )}

      {/* Success banner for Real Call */}
      {successResult && (
        <div className="card" style={{ borderLeft: '4px solid #10b981', background: '#f0fdf4', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#065f46', fontWeight: 700, fontSize: 15 }}>
                <CheckCircle size={20} color="#10b981" /> Call Successfully Initiated!
              </div>
              <div style={{ fontSize: 13, color: '#047857', marginTop: 4 }}>
                {successResult.message}
              </div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4, fontFamily: 'monospace' }}>
                Provider Call ID: {successResult.call_id} | Status: {successResult.call_status}
              </div>
            </div>
            {onNavigateToCalls && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigateToCalls(successResult.call_id)}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                View in Call Logs <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Success banner for Simulation */}
      {simSessionId && (
        <div className="card" style={{ borderLeft: '4px solid #0284c7', background: '#f0f9ff', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#075985', fontWeight: 700, fontSize: 15 }}>
                <CheckCircle size={20} color="#0284c7" /> Simulator Session Ready
              </div>
              <div style={{ fontSize: 13, color: '#0369a1', marginTop: 4 }}>
                Pre-filled facts applied to conversation session: <code>{simSessionId}</code>
              </div>
            </div>
            {onNavigateToSimulator && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigateToSimulator(simSessionId)}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                Open Simulator <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Section 1: Contact & Agent Setup */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#102a43', borderBottom: '1px solid #f1f5f9', paddingBottom: 8 }}>
              1. CONTACT & AGENT PREFERENCES
            </div>

            <div>
              <label className="form-label">Customer Name</label>
              <input
                type="text"
                className="input-field"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
                placeholder="e.g. Rajesh Sharma"
                required
              />
            </div>

            <div>
              <label className="form-label">
                Destination Phone / Test Number (E.164)
              </label>
              <input
                type="text"
                className="input-field"
                value={customerPhone}
                onChange={e => setCustomerPhone(e.target.value)}
                placeholder="+919876543210"
                required
              />
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                Indian 10-digit numbers automatically convert to +91.
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label className="form-label">Language</label>
                <select
                  className="input-field"
                  value={language}
                  onChange={e => setLanguage(e.target.value as 'English' | 'Hindi')}
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi</option>
                </select>
              </div>

              <div>
                <label className="form-label">Agent Voice Gender</label>
                <select
                  className="input-field"
                  value={agentGender}
                  onChange={e => setAgentGender(e.target.value as 'female' | 'male')}
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </div>
            </div>

            <div>
              <label className="form-label">Agent Name</label>
              <input
                type="text"
                className="input-field"
                value={agentName}
                onChange={e => setAgentName(e.target.value)}
                placeholder="Ananya"
              />
            </div>
          </div>

          {/* Section 2: Property & Document Details */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#102a43', borderBottom: '1px solid #f1f5f9', paddingBottom: 8 }}>
              2. PROPERTY & TITLE INFORMATION
            </div>

            <div>
              <label className="form-label">Property Type</label>
              <select
                className="input-field"
                value={propertyType}
                onChange={e => setPropertyType(e.target.value)}
              >
                <option value="">(Unknown / Leave for agent to ask)</option>
                <option value="Residential">Residential (Accepted)</option>
                <option value="Commercial">Commercial (Accepted)</option>
                <option value="Industrial">Industrial (Accepted)</option>
                <option value="Agricultural">Agricultural (Disqualifying)</option>
              </select>
            </div>

            <div>
              <label className="form-label">Ownership Status</label>
              <select
                className="input-field"
                value={ownershipStatus}
                onChange={e => setOwnershipStatus(e.target.value)}
              >
                <option value="">(Unknown / Leave for agent to ask)</option>
                <option value="Sole">Sole Ownership</option>
                <option value="Joint">Joint Ownership</option>
              </select>
            </div>

            <div>
              <label className="form-label">Original Property Title Documents Available</label>
              <select
                className="input-field"
                value={originalDocs}
                onChange={e => setOriginalDocs(e.target.value)}
              >
                <option value="Yes">Yes (Physical originals available)</option>
                <option value="No">No (Copies only / Disqualifying)</option>
                <option value="Unknown">Unknown (Agent must clarify)</option>
              </select>
            </div>

            <div>
              <label className="form-label">Property Estimated Market Value (₹)</label>
              <input
                type="number"
                className="input-field"
                value={marketValue}
                onChange={e => setMarketValue(e.target.value)}
                placeholder="e.g. 12000000 (1.2 Crore)"
              />
            </div>
          </div>

          {/* Section 3: Financial & Loan Requirements */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#102a43', borderBottom: '1px solid #f1f5f9', paddingBottom: 8 }}>
              3. LOAN & TENURE REQUEST
            </div>

            <div>
              <label className="form-label">Requested Loan Amount (₹)</label>
              <input
                type="number"
                className="input-field"
                value={loanAmount}
                onChange={e => setLoanAmount(e.target.value)}
                placeholder="e.g. 4500000 (Max ₹75,00,000)"
              />
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                Maximum LAP loan limit is ₹75,00,000. Values above cap require customer agreement.
              </div>
            </div>

            <div>
              <label className="form-label">Requested Loan Tenure (Years)</label>
              <input
                type="number"
                min="1"
                max="30"
                className="input-field"
                value={tenureYears}
                onChange={e => setTenureYears(e.target.value)}
                placeholder="e.g. 10 (Allowed: 3 to 15 years)"
              />
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                Valid range: 3 to 15 years inclusive.
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label className="form-label">Occupation</label>
                <select
                  className="input-field"
                  value={occupation}
                  onChange={e => setOccupation(e.target.value)}
                >
                  <option value="">(Unknown)</option>
                  <option value="Salaried">Salaried</option>
                  <option value="Self-employed">Self-employed</option>
                </select>
              </div>

              <div>
                <label className="form-label">Income Mode</label>
                <select
                  className="input-field"
                  value={incomeMode}
                  onChange={e => setIncomeMode(e.target.value)}
                >
                  <option value="">(Unknown)</option>
                  <option value="Bank">Bank Deposit (Accepted)</option>
                  <option value="Cash">Cash Only (Disqualifying)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 4: Existing Loans & Handoffs */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#102a43', borderBottom: '1px solid #f1f5f9', paddingBottom: 8 }}>
              4. SPECIALIST ROUTING CRITERIA
            </div>

            <div>
              <label className="form-label">Existing Loan on this Property?</label>
              <select
                className="input-field"
                value={existingLoan}
                onChange={e => setExistingLoan(e.target.value)}
              >
                <option value="No">No (New LAP Loan)</option>
                <option value="Yes">Yes (Route to Loan Transfer Specialist)</option>
              </select>
            </div>

            <div>
              <label className="form-label">Customer Requests EMI Reduction?</label>
              <select
                className="input-field"
                value={emiReduction}
                onChange={e => setEmiReduction(e.target.value)}
              >
                <option value="No">No</option>
                <option value="Yes">Yes (Route to Debt Consolidation Specialist)</option>
              </select>
            </div>

            {mode === 'real_call' && (
              <div>
                <label className="form-label">Calling Delivery Method</label>
                <select
                  className="input-field"
                  value={callMode}
                  onChange={e => setCallMode(e.target.value as 'phone' | 'web')}
                >
                  <option value="phone">Outbound Phone Call (via Retell telephony)</option>
                  <option value="web">Web Call (Browser audio stream)</option>
                </select>
              </div>
            )}

            {mode === 'real_call' && (
              <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', padding: 12, borderRadius: 8 }}>
                <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, cursor: 'pointer', fontSize: 12, color: '#9a3412' }}>
                  <input
                    type="checkbox"
                    checked={confirmedDestination}
                    onChange={e => setConfirmedDestination(e.target.checked)}
                    style={{ marginTop: 2 }}
                  />
                  <span>
                    <strong>Confirmation:</strong> I confirm this call is placed to an authorized test destination number ({customerPhone}) for verification.
                  </span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Submit Actions */}
        <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          {mode === 'real_call' ? (
            <button
              type="submit"
              disabled={loading || !confirmedDestination}
              className="btn-primary"
              style={{
                background: confirmedDestination ? '#ea580c' : '#94a3b8',
                borderColor: confirmedDestination ? '#ea580c' : '#94a3b8',
                padding: '12px 28px',
                fontSize: 15,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: confirmedDestination ? 'pointer' : 'not-allowed'
              }}
            >
              <PhoneCall size={18} />
              {loading ? 'Initiating Retell Call…' : 'Start Test Call via Retell'}
            </button>
          ) : (
            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{
                background: '#10b981',
                borderColor: '#10b981',
                padding: '12px 28px',
                fontSize: 15,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
            >
              <MessageSquare size={18} />
              {loading ? 'Starting Simulator…' : 'Start Test in Simulator'}
            </button>
          )}
        </div>
      </form>
    </div>
  );
};
