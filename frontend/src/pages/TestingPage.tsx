import React, { useState } from 'react';
import { runTestSuite } from '../services/api';
import type { TestSuiteResponse, TestCaseResult } from '../types';
import { FlaskConical, Play, CheckCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react';

const CATEGORY_COLORS: Record<string, string> = {
  'Eligibility': '#199473',
  'Disqualification': '#dc2626',
  'Loan Cap': '#7c3aed',
  'Tenure': '#2563eb',
  'Market Value': '#0891b2',
  'Clarification': '#d97706',
  'Extraction': '#059669',
  'Contradictions': '#b45309',
  'Dialogue Flow': '#334e68',
  'Loan Transfer': '#1d4ed8',
  'Busy Handling': '#92400e',
  'RAG & Safety': '#4f46e5',
  'Corrections': '#6d28d9',
  'Customer Decline': '#9f1239',
  'Persistence': '#065f46',
  'Checklist Item 5': '#9a3412',
};

const TestResultRow: React.FC<{ result: TestCaseResult }> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);
  const catColor = CATEGORY_COLORS[result.category] || '#627d98';

  return (
    <div style={{ borderBottom: '1px solid #f1f5f9' }}>
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        {result.passed ? (
          <CheckCircle size={16} color="#199473" style={{ flexShrink: 0 }} />
        ) : (
          <XCircle size={16} color="#dc2626" style={{ flexShrink: 0 }} />
        )}
        <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#94a3b8', width: 60 }}>{result.test_id}</span>
        <span style={{
          fontSize: 11, padding: '2px 8px', borderRadius: 20, fontWeight: 600, flexShrink: 0,
          background: catColor + '1a', color: catColor
        }}>
          {result.category}
        </span>
        <span style={{ fontSize: 13, color: '#334e68', flex: 1 }}>{result.name}</span>
        {expanded ? <ChevronDown size={14} color="#94a3b8" /> : <ChevronRight size={14} color="#94a3b8" />}
      </div>

      {expanded && (
        <div style={{ padding: '8px 16px 16px 44px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Expected: </span>
              <code style={{ background: '#f8fafc', padding: '2px 6px', borderRadius: 4, color: '#199473' }}>{result.expected_outcome}</code>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Actual: </span>
              <code style={{ background: '#f8fafc', padding: '2px 6px', borderRadius: 4, color: result.passed ? '#199473' : '#dc2626' }}>{result.actual_outcome}</code>
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#486581', background: '#f8fafc', borderRadius: 8, padding: '8px 12px' }}>
            {result.details}
          </div>
        </div>
      )}
    </div>
  );
};

export const TestingPage: React.FC = () => {
  const [results, setResults] = useState<TestSuiteResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');

  const handleRun = async () => {
    setRunning(true);
    setResults(null);
    try {
      const res = await runTestSuite();
      setResults(res);
    } finally { setRunning(false); }
  };

  const filteredResults = results?.results.filter(r =>
    filter === 'all' ? true : filter === 'passed' ? r.passed : !r.passed
  ) ?? [];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#102a43', margin: 0 }}>
          Testing Center
        </h1>
        <p style={{ fontSize: 14, color: '#627d98', margin: '4px 0 0' }}>
          35 predefined deterministic test scenarios with explicit pass/fail assertions
        </p>
      </div>

      {/* Run button */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: '#243b53', marginBottom: 4 }}>Automated Test Suite</div>
            <div style={{ fontSize: 13, color: '#627d98' }}>
              Tests cover eligibility rules, dialogue flow, extraction accuracy, corrections, boundary conditions, and handoff gate validation.
              No external API keys required.
            </div>
          </div>
          <button
            className="btn-primary"
            onClick={handleRun}
            disabled={running}
            style={{ flexShrink: 0, padding: '10px 24px' }}
          >
            {running ? (
              <>
                <FlaskConical size={15} style={{ animation: 'spin 1s linear infinite' }} />
                Running…
              </>
            ) : (
              <>
                <Play size={15} /> Run All Tests
              </>
            )}
          </button>
        </div>

        {/* Summary */}
        {results && (
          <div style={{ marginTop: 16, display: 'flex', gap: 16, padding: '12px 0', borderTop: '1px solid #f1f5f9' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#243b53' }}>{results.total_tests}</div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>Total</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#199473' }}>{results.passed_tests}</div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>Passed</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#dc2626' }}>{results.failed_tests}</div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>Failed</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: results.failed_tests === 0 ? '#199473' : '#d97706' }}>
                {Math.round(results.passed_tests / results.total_tests * 100)}%
              </div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>Pass Rate</div>
            </div>
            {results.failed_tests === 0 && (
              <div style={{ background: '#d1fae5', borderRadius: 8, padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 8, color: '#065f46', fontSize: 13, fontWeight: 600 }}>
                <CheckCircle size={16} /> All tests passed!
              </div>
            )}
          </div>
        )}
      </div>

      {results && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: 8 }}>
            {(['all', 'passed', 'failed'] as const).map(f => (
              <button
                key={f}
                className={filter === f ? 'btn-primary' : 'btn-secondary'}
                onClick={() => setFilter(f)}
                style={{ fontSize: 12, padding: '5px 14px', textTransform: 'capitalize' }}
              >
                {f} {f === 'passed' ? `(${results.passed_tests})` : f === 'failed' ? `(${results.failed_tests})` : `(${results.total_tests})`}
              </button>
            ))}
          </div>

          <div>
            {filteredResults.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', color: '#94a3b8', fontSize: 13 }}>
                No {filter} results
              </div>
            ) : (
              filteredResults.map(r => <TestResultRow key={r.test_id} result={r} />)
            )}
          </div>
        </div>
      )}

      {!results && !running && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <FlaskConical size={48} style={{ color: '#cbd5e1', margin: '0 auto 16px', display: 'block' }} />
          <div style={{ fontWeight: 600, color: '#334e68', marginBottom: 6 }}>Ready to run tests</div>
          <div style={{ fontSize: 13, color: '#94a3b8' }}>
            Click "Run All Tests" to execute 35 deterministic assertion-based test cases
          </div>
        </div>
      )}
    </div>
  );
};
