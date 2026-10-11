import React, { useEffect, useState } from 'react';
import { getConfig, updateConfig, getPrompt, updatePrompt, getVoiceStatus, syncAgent } from '../services/api';
import type { AgentConfig } from '../types';
import { Save, Copy, RefreshCw, Check, AlertTriangle, Mic2 } from 'lucide-react';

const DYNAMIC_VARS = [
  '{{company_name}}', '{{customer_name}}', '{{agent_name}}', '{{agent_gender}}',
  '{{current_date}}', '{{current_day}}', '{{current_time}}',
  '{{additional_context_from_rag}}', '{{language_to_speak}}',
  '{{conversation_history}}', '{{customer_utterance}}'
];

export const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [promptText, setPromptText] = useState('');
  const [saving, setSaving] = useState(false);
  const [promptSaving, setPromptSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<Record<string, unknown>>({});
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    Promise.all([getConfig(), getPrompt(), getVoiceStatus()]).then(([cfg, pmt, vs]) => {
      setConfig(cfg);
      setPromptText(pmt.raw_prompt);
      setVoiceStatus(vs as Record<string, unknown>);
    }).catch(() => {});
  }, []);

  const handleSaveConfig = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const result = await updateConfig(config);
      setConfig(result.config);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally { setSaving(false); }
  };

  const handleSavePrompt = async () => {
    setPromptSaving(true);
    try {
      await updatePrompt(promptText);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally { setPromptSaving(false); }
  };

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(promptText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleSyncAgent = async () => {
    setSyncResult(null);
    const result = await syncAgent({
      agent_name: config?.agent_name,
      voice_id: config?.voice_id,
      language: config?.default_language
    });
    setSyncResult(result.success ? `✓ Agent synced! ID: ${result.agent_id || 'see Retell Dashboard'}` : `✗ ${result.error}`);
  };

  if (!config) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#627d98' }}>
        Loading configuration…
      </div>
    );
  }

  const field = (label: string, key: keyof AgentConfig, type: 'text' | 'select' = 'text', options?: string[]) => (
    <div style={{ marginBottom: 16 }}>
      <label className="label">{label}</label>
      {type === 'select' ? (
        <select
          className="input-field"
          value={String(config[key])}
          onChange={e => setConfig({ ...config, [key]: e.target.value })}
        >
          {options?.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input
          className="input-field"
          value={String(config[key])}
          onChange={e => setConfig({ ...config, [key]: e.target.value })}
        />
      )}
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>
          Agent Configuration
        </h1>
        <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
          Configure dynamic prompt variables, voice settings, and platform integration
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Left column: Agent Settings */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">Agent Identity</div>
            {field('Company Name', 'company_name')}
            {field('Agent Name', 'agent_name')}
            {field('Agent Gender', 'agent_gender', 'select', ['female', 'male'])}
            {field('Default Customer Name', 'default_customer_name')}
            {field('Default Language', 'default_language', 'select', ['English', 'Hindi'])}
            {field('Voice Platform', 'voice_platform', 'select', ['retell', 'bolna'])}
            {field('Voice ID', 'voice_id')}
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">Retell AI Telephony Settings</div>
            {field('Retell Agent ID', 'retell_agent_id')}
            {field('Retell From Number (Outbound)', 'retell_from_number')}
            <div style={{ marginBottom: 16 }}>
              <label className="label">Authorized Test Numbers (comma-separated)</label>
              <input
                className="input-field"
                value={config.authorized_test_numbers ? config.authorized_test_numbers.join(', ') : ''}
                onChange={e => setConfig({
                  ...config,
                  authorized_test_numbers: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                placeholder="+919876543210, +1234567890"
              />
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                Leave empty to accept any valid E.164 number in development mode.
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">Additional RAG Context</div>
            <div style={{ fontSize: 12, color: '#627d98', marginBottom: 8 }}>
              This text is injected as product knowledge. Do not include confidential data.
            </div>
            <textarea
              className="input-field"
              rows={5}
              value={config.additional_context_from_rag}
              onChange={e => setConfig({ ...config, additional_context_from_rag: e.target.value })}
              style={{ resize: 'vertical' }}
            />
          </div>

          <button
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleSaveConfig}
            disabled={saving}
          >
            {saving ? <RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={15} />}
            {saved ? 'Saved!' : 'Save Configuration'}
          </button>
        </div>

        {/* Right column: System Prompt & Voice Status */}
        <div>
          {/* Voice Platform Status */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="section-title" style={{ margin: 0 }}>Voice Platform Status</div>
              <Mic2 size={18} color="#199473" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: '#627d98' }}>Primary Provider</span>
                <span style={{ fontWeight: 600, color: '#334e68', textTransform: 'uppercase' }}>
                  {String(voiceStatus.primary_provider || 'Retell AI')}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: '#627d98' }}>API Configured</span>
                <span style={{
                  fontWeight: 600,
                  color: voiceStatus.retell_configured ? '#199473' : '#dc2626'
                }}>
                  {voiceStatus.retell_configured ? '✓ Yes' : '✗ Missing key'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: '#627d98' }}>Agent ID</span>
                <span style={{ fontWeight: 500, color: '#334e68', fontSize: 11 }}>
                  {String(voiceStatus.retell_agent_id || '— Not synced')}
                </span>
              </div>
              {!voiceStatus.retell_configured && (
                <div style={{ background: '#fef3c7', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#92400e', display: 'flex', gap: 6 }}>
                  <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
                  Add RETELL_API_KEY to backend/.env to enable real voice calls
                </div>
              )}
              <button className="btn-secondary" onClick={handleSyncAgent} style={{ marginTop: 4, justifyContent: 'center' }}>
                <RefreshCw size={13} /> Sync Agent to Retell
              </button>
              {syncResult && (
                <div style={{ fontSize: 12, padding: '6px 10px', borderRadius: 8, background: syncResult.startsWith('✓') ? '#d1fae5' : '#fee2e2', color: syncResult.startsWith('✓') ? '#065f46' : '#991b1b' }}>
                  {syncResult}
                </div>
              )}
            </div>
          </div>

          {/* Dynamic Variables Reference */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">Dynamic Variables</div>
            <div style={{ fontSize: 12, color: '#627d98', marginBottom: 10 }}>
              These variables are substituted safely in the rendered system prompt.
              Missing values use fallback neutrals — raw <code>{'{{tags}}'}</code> are never exposed.
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {DYNAMIC_VARS.map(v => (
                <code key={v} style={{
                  fontSize: 11, background: '#f8fafc', border: '1px solid #e2e8f0',
                  borderRadius: 6, padding: '3px 8px', color: '#486581', fontFamily: 'monospace'
                }}>
                  {v}
                </code>
              ))}
            </div>
          </div>

          {/* System Prompt Editor */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div className="section-title" style={{ margin: 0 }}>Production System Prompt</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn-secondary" onClick={handleCopyPrompt} style={{ fontSize: 12, padding: '6px 12px' }}>
                  {copied ? <Check size={13} /> : <Copy size={13} />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button className="btn-primary" onClick={handleSavePrompt} disabled={promptSaving} style={{ fontSize: 12, padding: '6px 12px' }}>
                  <Save size={13} /> Save
                </button>
              </div>
            </div>
            <textarea
              className="input-field"
              rows={18}
              value={promptText}
              onChange={e => setPromptText(e.target.value)}
              style={{
                fontFamily: 'monospace', fontSize: 11.5, lineHeight: 1.6,
                resize: 'vertical', maxHeight: 500,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
