import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from app.core.config import settings

class CallRepository:
    """
    SQLite persistence layer for storing and retrieving call logs, transcripts,
    and qualification outcomes. Cleanly isolated behind a repository interface
    for easy migration to PostgreSQL.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS call_records (
                    call_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    phone_number TEXT,
                    timestamp TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds INTEGER,
                    call_type TEXT,
                    call_status TEXT,
                    outcome TEXT,
                    disqualification_reason TEXT,
                    transfer_reason TEXT,
                    recording_url TEXT,
                    transcript TEXT,
                    collected_fields TEXT,
                    decision_explanation TEXT,
                    error_message TEXT
                )
            """)
            # Migration check for existing tables missing new columns
            existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(call_records)").fetchall()]
            for col_name, col_type in [
                ("phone_number", "TEXT"),
                ("call_status", "TEXT"),
                ("start_time", "TEXT"),
                ("end_time", "TEXT")
            ]:
                if col_name not in existing_cols:
                    try:
                        conn.execute(f"ALTER TABLE call_records ADD COLUMN {col_name} {col_type}")
                    except sqlite3.OperationalError:
                        pass
        conn.close()

    def save_call_record(self, record: Dict[str, Any]) -> None:
        conn = self._get_connection()
        transcript = record.get("transcript")
        transcript_json = json.dumps(transcript) if isinstance(transcript, (list, dict)) else (transcript or "[]")
        collected_fields = record.get("collected_fields")
        fields_json = json.dumps(collected_fields) if isinstance(collected_fields, dict) else (collected_fields or "{}")

        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO call_records (
                    call_id, customer_name, phone_number, timestamp, start_time, end_time,
                    duration_seconds, call_type, call_status, outcome, disqualification_reason,
                    transfer_reason, recording_url, transcript, collected_fields,
                    decision_explanation, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("call_id"),
                record.get("customer_name"),
                record.get("phone_number"),
                record.get("timestamp"),
                record.get("start_time"),
                record.get("end_time"),
                record.get("duration_seconds"),
                record.get("call_type", "simulation"),
                record.get("call_status", "completed" if record.get("call_type") == "simulation" else "registered"),
                record.get("outcome"),
                record.get("disqualification_reason"),
                record.get("transfer_reason"),
                record.get("recording_url"),
                transcript_json,
                fields_json,
                record.get("decision_explanation"),
                record.get("error_message")
            ))
        conn.close()

    def update_call_status(self, call_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record = self.get_call_by_id(call_id)
        if not record:
            return None
        # Merge updates
        for k, v in updates.items():
            if v is not None or k in ("error_message", "recording_url"):
                record[k] = v
        self.save_call_record(record)
        return self.get_call_by_id(call_id)

    def get_all_calls(self, outcome_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if outcome_filter and outcome_filter.upper() != "ALL":
            cursor.execute("SELECT * FROM call_records WHERE outcome = ? ORDER BY timestamp DESC", (outcome_filter.upper(),))
        else:
            cursor.execute("SELECT * FROM call_records ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(self._row_to_dict(row))
        conn.close()
        return results

    def get_call_by_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM call_records WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_dict(row)
        return None

    def get_analytics_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT outcome, count(*) as count FROM call_records GROUP BY outcome")
        outcome_counts = {row["outcome"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT count(*) as total FROM call_records")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT count(*) as completed FROM call_records WHERE call_status IN ('ended', 'completed') OR (call_type = 'simulation' AND outcome != 'IN_PROGRESS')")
        completed = cursor.fetchone()["completed"]

        cursor.execute("SELECT count(*) as failed FROM call_records WHERE call_status = 'failed' OR outcome = 'FAILED' OR (error_message IS NOT NULL AND error_message != '')")
        failed = cursor.fetchone()["failed"]

        qualified = outcome_counts.get("QUALIFIED", 0)
        not_eligible = outcome_counts.get("NOT_ELIGIBLE", 0)
        transfers = outcome_counts.get("LOAN_TRANSFER", 0)
        callbacks = outcome_counts.get("CALLBACK_REQUESTED", 0)
        declined = outcome_counts.get("CUSTOMER_DECLINED", 0)

        rate = (qualified / total * 100) if total > 0 else 0.0

        conn.close()
        return {
            "total_calls": total,
            "completed_calls": completed,
            "failed_calls": failed,
            "qualified_count": qualified,
            "disqualified_count": not_eligible,
            "loan_transfer_count": transfers,
            "callback_count": callbacks,
            "declined_count": declined,
            "qualification_rate": round(rate, 1),
            "outcome_distribution": [
                {"name": "Qualified", "value": qualified, "color": "#0d9488"},
                {"name": "Not Eligible", "value": not_eligible, "color": "#ef4444"},
                {"name": "Loan Transfer", "value": transfers, "color": "#3b82f6"},
                {"name": "Callback", "value": callbacks, "color": "#f59e0b"},
                {"name": "Declined", "value": declined, "color": "#6b7280"}
            ]
        }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        keys = row.keys()
        return {
            "call_id": row["call_id"],
            "customer_name": row["customer_name"],
            "phone_number": row["phone_number"] if "phone_number" in keys else None,
            "timestamp": row["timestamp"],
            "start_time": row["start_time"] if "start_time" in keys else None,
            "end_time": row["end_time"] if "end_time" in keys else None,
            "duration_seconds": row["duration_seconds"],
            "call_type": row["call_type"],
            "call_status": row["call_status"] if "call_status" in keys else "completed",
            "outcome": row["outcome"],
            "disqualification_reason": row["disqualification_reason"],
            "transfer_reason": row["transfer_reason"],
            "recording_url": row["recording_url"],
            "transcript": json.loads(row["transcript"]) if row["transcript"] else [],
            "collected_fields": json.loads(row["collected_fields"]) if row["collected_fields"] else {},
            "decision_explanation": row["decision_explanation"],
            "error_message": row["error_message"]
        }

call_repository = CallRepository()
