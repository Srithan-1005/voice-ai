import type { QualificationStatus, ChecklistItemStatus } from '../types';

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return '—';
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`;
  if (value >= 100000) return `₹${(value / 100000).toFixed(0)} L`;
  return `₹${value.toLocaleString('en-IN')}`;
}

export function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return ts;
  }
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export const STATUS_LABELS: Record<QualificationStatus, string> = {
  IN_PROGRESS: 'In Progress',
  NEEDS_CLARIFICATION: 'Needs Clarification',
  QUALIFIED: 'Qualified',
  NOT_ELIGIBLE: 'Not Eligible',
  LOAN_TRANSFER: 'Loan Transfer',
  CALLBACK_REQUESTED: 'Callback Requested',
  CUSTOMER_DECLINED: 'Declined',
};

export const STATUS_BADGE: Record<QualificationStatus, string> = {
  IN_PROGRESS: 'badge-progress',
  NEEDS_CLARIFICATION: 'badge-clarification',
  QUALIFIED: 'badge-qualified',
  NOT_ELIGIBLE: 'badge-disqualified',
  LOAN_TRANSFER: 'badge-transfer',
  CALLBACK_REQUESTED: 'badge-callback',
  CUSTOMER_DECLINED: 'badge-progress',
};

export const CHECKLIST_ITEM_COLORS: Record<ChecklistItemStatus, string> = {
  'Unknown': 'text-slate-400',
  'Answered': 'text-teal-600',
  'Invalid': 'text-red-600',
  'Clarification Needed': 'text-amber-600',
};

export const CHECKLIST_BG_COLORS: Record<ChecklistItemStatus, string> = {
  'Unknown': 'bg-slate-50 border-slate-200',
  'Answered': 'bg-teal-50 border-teal-200',
  'Invalid': 'bg-red-50 border-red-200',
  'Clarification Needed': 'bg-amber-50 border-amber-200',
};

export const PRESET_SCENARIOS = [
  {
    id: 'happy_path',
    label: 'Happy Path – Full Qualification',
    description: 'Residential property, sole owner, salaried with bank income, ₹50L loan, 10 years',
    messages: [
      'Yes, speaking',
      "It's my own residential house",
      'I am the sole owner',
      'Yes, the original papers are at home',
      'I need around 50 lakh',
      'I am a salaried software engineer, salary credited to bank',
      'Worth roughly 1 crore',
      '10 years',
    ],
  },
  {
    id: 'agricultural',
    label: 'Disqualification – Agricultural Property',
    description: 'Farmland property triggers immediate disqualification',
    messages: ['Yes speaking', 'It is an agricultural farmland'],
  },
  {
    id: 'cash_income',
    label: 'Disqualification – Cash Income',
    description: 'Cash-only income triggers immediate disqualification',
    messages: [
      'Yes speaking',
      'Residential house',
      'Sole owner',
      'Yes originals available',
      '40 lakh',
      'I run a small shop and all income is cash',
    ],
  },
  {
    id: 'loan_transfer',
    label: 'Loan Transfer – Existing Loan',
    description: 'Customer already has a mortgage on the property',
    messages: ['Yes speaking', 'Actually I already have a loan on this property with HDFC'],
  },
  {
    id: 'excess_loan',
    label: 'Excess Loan – ₹1 Crore Request',
    description: 'Customer requests ₹1 Cr, offered ₹75L cap, accepts',
    messages: [
      'Yes speaking',
      'Residential house',
      'Sole owner',
      'Yes originals available',
      'I need 1 crore',
      'Yes, 75 lakh is fine',
      'Salaried, bank income',
      '80 lakh market value',
      '10 years',
    ],
  },
  {
    id: 'callback',
    label: 'Busy Customer – Callback',
    description: 'Customer is busy, requests callback tomorrow',
    messages: ['I am driving, please call me back tomorrow at 3 pm'],
  },
  {
    id: 'multi_fact',
    label: 'Multi-Fact Utterance',
    description: 'Customer provides multiple facts in one sentence',
    messages: [
      'Yes speaking',
      'I own a commercial property worth 2 crore, need 70 lakh for 12 years, I run a business with bank income, and I have the original documents',
      'Joint ownership with my brother',
    ],
  },
];
