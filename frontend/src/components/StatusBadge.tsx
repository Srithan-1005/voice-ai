import React from 'react';
import { STATUS_LABELS, STATUS_BADGE } from '../utils/helpers';
import type { QualificationStatus } from '../types';

interface StatusBadgeProps {
  status: QualificationStatus;
}

const STATUS_ICONS: Record<QualificationStatus, string> = {
  QUALIFIED: '✓',
  NOT_ELIGIBLE: '✗',
  LOAN_TRANSFER: '↔',
  CALLBACK_REQUESTED: '⏰',
  IN_PROGRESS: '…',
  NEEDS_CLARIFICATION: '?',
  CUSTOMER_DECLINED: '✗',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => (
  <span className={STATUS_BADGE[status]}>
    <span>{STATUS_ICONS[status]}</span>
    {STATUS_LABELS[status]}
  </span>
);
