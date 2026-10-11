import React, { useEffect, useState } from 'react';
import { getAnalytics, getCalls } from '../services/api';
import type { Analytics, CallRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatTimestamp, formatDuration } from '../utils/helpers';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { CheckCircle, XCircle, RefreshCw, Phone, PhoneCall } from 'lucide-react';

interface OverviewPageProps {
  onNavigate?: (page: any) => void;
}


export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [recentCalls, setRecentCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [an, calls] = await Promise.all([getAnalytics(), getCalls()]);
      setAnalytics(an);
      setRecentCalls(calls.calls.slice(0, 6));
    } catch (e) {
      setError('Cannot reach the backend. Check that the backend service is available and try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const statCards = analytics ? [
    { label: 'Total Calls', value: analytics.total_calls, icon: <Phone size={20} />, color: '#199473', bg: '#effcf6' },
    { label: 'Completed Calls', value: analytics.completed_calls ?? 0, icon: <CheckCircle size={20} />, color: '#0284c7', bg: '#e0f2fe' },
    { label: 'Failed Calls', value: analytics.failed_calls ?? 0, icon: <XCircle size={20} />, color: '#dc2626', bg: '#fee2e2' },
    { label: 'Qualified Customers', value: analytics.qualified_count, icon: <CheckCircle size={20} />, color: '#199473', bg: '#d1fae5' },
    { label: 'Disqualified Customers', value: analytics.disqualified_count, icon: <XCircle size={20} />, color: '#dc2626', bg: '#fee2e2' },
    { label: 'Transfers Requested', value: analytics.loan_transfer_count, icon: <RefreshCw size={20} />, color: '#2563eb', bg: '#dbeafe' },
  ] : [];


  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
        <div style={{ textAlign: 'center', color: '#627d98' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>⏳</div>
          Loading analytics…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ borderLeft: '4px solid #ef4444', background: '#fff5f5', marginBottom: 16 }}>
        <div style={{ fontWeight: 600, color: '#991b1b', marginBottom: 4 }}>Backend Connection Error</div>
        <div style={{ fontSize: 14, color: '#7f1d1d' }}>{error}</div>
        <button className="btn-primary" style={{ marginTop: 12 }} onClick={fetchData}>Retry</button>
      </div>
    );
  }

  const isDemo = analytics?.total_calls === 0;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>
            Overview Dashboard
          </h1>
          <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
            Home Credit | LAP Voice Qualification
            {isDemo && (
              <span style={{ marginLeft: 10, background: '#fef3c7', color: '#92400e', borderRadius: 20, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                DEMO MODE — No calls yet
              </span>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {onNavigate && (
            <button className="btn-primary" onClick={() => onNavigate('start-call')} style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
              <PhoneCall size={14} /> Start Test Call
            </button>
          )}
          <button className="btn-secondary" onClick={fetchData} style={{ fontSize: 13 }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
        {statCards.map((s) => (
          <div key={s.label} className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#627d98' }}>{s.label}</span>
              <div style={{ background: s.bg, color: s.color, padding: 8, borderRadius: 8 }}>
                {s.icon}
              </div>
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#102a43' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, marginBottom: 24 }}>
        {/* Bar chart */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: 8 }}>Call Outcome Distribution</div>
          {analytics && analytics.outcome_distribution.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={analytics.outcome_distribution} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#627d98' }} />
                <YAxis tick={{ fontSize: 11, fill: '#627d98' }} allowDecimals={false} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {analytics.outcome_distribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 14 }}>
              No call data yet — run a simulation to see results
            </div>
          )}
        </div>

        {/* Pie chart */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: 8 }}>Outcome Breakdown</div>
          {analytics && analytics.outcome_distribution.some(d => d.value > 0) ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={analytics.outcome_distribution.filter(d => d.value > 0)}
                    cx="50%" cy="50%"
                    innerRadius={40} outerRadius={72}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {analytics.outcome_distribution.filter(d => d.value > 0).map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                {analytics.outcome_distribution.filter(d => d.value > 0).map(entry => (
                  <div key={entry.name} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: entry.color }} />
                    <span style={{ color: '#627d98' }}>{entry.name}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 14 }}>
              No data yet
            </div>
          )}
        </div>
      </div>

      {/* Recent calls */}
      <div className="card">
        <div className="section-title">Recent Call Activity</div>
        {recentCalls.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8' }}>
            <Phone size={36} style={{ opacity: 0.3, margin: '0 auto 12px', display: 'block' }} />
            <div style={{ fontWeight: 500 }}>No calls recorded yet</div>
            <div style={{ fontSize: 13, marginTop: 4 }}>Use the Conversation Simulator to start testing</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                  {['Customer', 'Type', 'Time', 'Duration', 'Outcome'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: '#627d98', fontSize: 11, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentCalls.map((call) => (
                  <tr key={call.call_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 500, color: '#243b53' }}>{call.customer_name}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: call.call_type === 'simulation' ? '#f1f5f9' : '#dbeafe', color: call.call_type === 'simulation' ? '#334e68' : '#1e40af', fontWeight: 600 }}>
                        {call.call_type === 'simulation' ? '🎭 SIM' : '📞 REAL'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#627d98' }}>{formatTimestamp(call.timestamp)}</td>
                    <td style={{ padding: '10px 12px', color: '#627d98' }}>{formatDuration(call.duration_seconds)}</td>
                    <td style={{ padding: '10px 12px' }}><StatusBadge status={call.outcome} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
