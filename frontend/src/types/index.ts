// API types matching backend schemas

export type QualificationStatus =
  | 'IN_PROGRESS'
  | 'NEEDS_CLARIFICATION'
  | 'QUALIFIED'
  | 'NOT_ELIGIBLE'
  | 'LOAN_TRANSFER'
  | 'CALLBACK_REQUESTED'
  | 'CUSTOMER_DECLINED';

export type ChecklistItemStatus = 'Unknown' | 'Answered' | 'Invalid' | 'Clarification Needed';

export interface ChecklistItemDetail {
  item_number: number;
  name: string;
  status: ChecklistItemStatus;
  captured_value: string | null;
  interpretation: string | null;
  clarification_needed: boolean;
}

export interface ConversationMessage {
  role: 'agent' | 'customer' | 'system';
  content: string;
  timestamp?: string;
}

export interface QualificationState {
  call_id: string | null;
  customer_name: string | null;
  customer_verified: boolean;
  customer_busy: boolean;
  callback_time: string | null;
  call_intent: string;
  property_type: string | null;
  ownership_status: string | null;
  original_documents_available: boolean | null;
  original_documents_uncertain: boolean;
  loan_amount_requested: number | null;
  loan_amount_confirmed: number | null;
  excess_loan_offer_pending: boolean;
  occupation: string | null;
  income_mode: string | null;
  income_mode_both_pending: boolean;
  market_value: number | null;
  tenure_years: number | null;
  disqualified: boolean;
  disqualification_reason: string | null;
  transfer_required: boolean;
  transfer_reason: string | null;
  qualification_status: QualificationStatus;
  answered_items: string[];
  pending_clarifications: string[];
  conversation_history: ConversationMessage[];
  call_ended: boolean;
  decision_explanation: string | null;
}

export interface SimulationSession {
  session_id: string;
  initial_message: string;
  state: QualificationState;
  checklist: ChecklistItemDetail[];
  missing_items: string[];
  outcome: QualificationStatus;
  call_ended: boolean;
  decision_explanation: string;
}

export interface SimulationMessageResponse {
  agent_response: string;
  state: QualificationState;
  checklist: ChecklistItemDetail[];
  outcome: QualificationStatus;
  missing_items: string[];
  call_ended: boolean;
  decision_explanation: string;
}

export interface CallRecord {
  call_id: string;
  customer_name: string;
  phone_number?: string | null;
  timestamp: string;
  start_time?: string | null;
  end_time?: string | null;
  duration_seconds: number | null;
  call_type: 'simulation' | 'provider_call' | 'web_call';
  call_status?: string;
  outcome: QualificationStatus;
  disqualification_reason: string | null;
  transfer_reason: string | null;
  recording_url: string | null;
  transcript: Array<{ role: string; content: string }>;
  collected_fields: Record<string, unknown>;
  decision_explanation: string;
  error_message: string | null;
}

export interface Analytics {
  total_calls: number;
  completed_calls?: number;
  failed_calls?: number;
  qualified_count: number;
  disqualified_count: number;
  loan_transfer_count: number;
  callback_count: number;
  declined_count: number;
  qualification_rate: number;
  outcome_distribution: Array<{ name: string; value: number; color: string }>;
}

export interface AgentConfig {
  app_name: string;
  environment: string;
  debug: boolean;
  company_name: string;
  agent_name: string;
  agent_gender: string;
  default_customer_name: string;
  default_language: string;
  voice_platform: string;
  voice_id: string;
  has_retell_key: boolean;
  retell_agent_id: string | null;
  retell_from_number?: string | null;
  authorized_test_numbers?: string[];
  has_webhook_secret?: boolean;
  has_bolna_key: boolean;
  additional_context_from_rag: string;
}

export interface StartCallRequest {
  customer_name?: string;
  customer_phone: string;
  language?: string;
  agent_name?: string;
  agent_gender?: string;
  property_type?: string;
  ownership_status?: string;
  original_documents_available?: string;
  loan_amount_requested?: number;
  occupation?: string;
  income_mode?: string;
  market_value?: number;
  tenure_years?: number;
  existing_loan?: string;
  emi_reduction_request?: string;
  call_mode?: 'phone' | 'web';
  confirmed_destination: boolean;
}

export interface StartCallResponse {
  call_id: string;
  call_status: string;
  customer_name: string;
  phone_number: string;
  call_type: string;
  message: string;
  access_token?: string;
  raw?: Record<string, unknown>;
}

export interface TranscriptResponse {
  call_id: string;
  available: boolean;
  transcript: Array<{ role: string; content: string }>;
  message: string;
}

export interface RecordingResponse {
  call_id: string;
  available: boolean;
  recording_url: string | null;
  message: string;
}


export interface TestCaseResult {
  test_id: string;
  name: string;
  category: string;
  passed: boolean;
  expected_outcome: string;
  actual_outcome: string;
  expected_state: Record<string, unknown>;
  actual_state: Record<string, unknown>;
  details: string;
}

export interface TestSuiteResponse {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  results: TestCaseResult[];
}
