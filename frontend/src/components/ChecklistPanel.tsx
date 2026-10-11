import React from 'react';
import type { ChecklistItemDetail } from '../types';
import { CHECKLIST_BG_COLORS } from '../utils/helpers';

interface ChecklistPanelProps {
  items: ChecklistItemDetail[];
  compact?: boolean;
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  'Unknown': <span style={{ color: '#94a3b8', fontSize: 16 }}>○</span>,
  'Answered': <span style={{ color: '#199473', fontSize: 16 }}>✓</span>,
  'Invalid': <span style={{ color: '#dc2626', fontSize: 16 }}>✗</span>,
  'Clarification Needed': <span style={{ color: '#d97706', fontSize: 16 }}>!</span>,
};

export const ChecklistPanel: React.FC<ChecklistPanelProps> = ({ items, compact = false }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 6 : 10 }}>
      {items.map((item) => {
        const bgClass = CHECKLIST_BG_COLORS[item.status];
        return (
          <div
            key={item.item_number}
            className={bgClass}
            style={{
              border: '1px solid',
              borderRadius: 10,
              padding: compact ? '8px 12px' : '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ flexShrink: 0 }}>{STATUS_ICON[item.status]}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#334e68', flex: 1 }}>
                {item.item_number}. {item.name}
              </span>
              {item.clarification_needed && (
                <span style={{
                  fontSize: 10, fontWeight: 600, background: '#fef3c7',
                  color: '#92400e', borderRadius: 20, padding: '2px 8px'
                }}>
                  CLARIFY
                </span>
              )}
            </div>
            {item.captured_value && (
              <div style={{ paddingLeft: 26, fontSize: 12, color: '#486581', fontWeight: 500 }}>
                {item.captured_value}
              </div>
            )}
            {!compact && item.interpretation && (
              <div style={{ paddingLeft: 26, fontSize: 11, color: '#627d98' }}>
                {item.interpretation}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
