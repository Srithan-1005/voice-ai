create table if not exists public.call_records (
    call_id text primary key,
    customer_name text,
    phone_number text,
    "timestamp" text,
    start_time text,
    end_time text,
    duration_seconds integer,
    call_type text,
    call_status text,
    outcome text,
    disqualification_reason text,
    transfer_reason text,
    recording_url text,
    transcript text not null default '[]',
    collected_fields text not null default '{}',
    decision_explanation text,
    error_message text
);

create index if not exists call_records_timestamp_idx
    on public.call_records ("timestamp" desc);

create index if not exists call_records_outcome_idx
    on public.call_records (outcome);

create index if not exists call_records_status_idx
    on public.call_records (call_status);
