#!/usr/bin/env python3
"""
Import Payana / Mysore Studios registration CSV into the app SQLite database.

Usage from project root:
  python import_registrations_csv.py "registrations_2026-07-10 (4).csv"

Optional DB path:
  python import_registrations_csv.py "registrations_2026-07-10 (4).csv" --db backend/payana.db

What it does:
- Creates the screening_registrations table if missing.
- Imports or updates records using Phone Number as the unique key.
- Preserves Created At / Updated At from CSV when available.
- Writes an audit log entry for every imported or updated row.
"""

import argparse
import csv
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

REQUIRED_COLUMNS = [
    "Name",
    "Age Group",
    "Social Background",
    "Primary Language",
    "Phone Number",
    "Remarks",
    "Selection Status",
    "Admin Remarks",
    "Created At",
    "Updated At",
]

def find_default_db() -> Path:
    candidates = [
        Path("backend/payana.db"),
        Path("backend/app.db"),
        Path("backend/screening.db"),
        Path("payana.db"),
        Path("app.db"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return Path("backend/payana.db")

def clean(value):
    if value is None:
        return ""
    return str(value).strip()

def clean_phone(value):
    s = clean(value)
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s

def now_ist_string():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")

def ensure_tables(conn: sqlite3.Connection):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS screening_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age_group TEXT NOT NULL,
        social_background TEXT NOT NULL,
        primary_language TEXT NOT NULL,
        phone_number TEXT NOT NULL UNIQUE,
        remarks TEXT,
        selection_status TEXT NOT NULL DEFAULT 'Registered',
        admin_remarks TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        updated_by TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        module_name TEXT NOT NULL,
        record_id INTEGER,
        old_value TEXT,
        new_value TEXT,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()

def import_csv(csv_file: Path, db_file: Path):
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    db_file.parent.mkdir(parents=True, exist_ok=True)

    inserted = 0
    updated = 0
    skipped = 0

    with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(missing)}")

        conn = sqlite3.connect(db_file)
        try:
            ensure_tables(conn)
            cur = conn.cursor()

            for row_number, row in enumerate(reader, start=2):
                record = {
                    "name": clean(row.get("Name")),
                    "age_group": clean(row.get("Age Group")),
                    "social_background": clean(row.get("Social Background")),
                    "primary_language": clean(row.get("Primary Language")),
                    "phone_number": clean_phone(row.get("Phone Number")),
                    "remarks": clean(row.get("Remarks")),
                    "selection_status": clean(row.get("Selection Status")) or "Registered",
                    "admin_remarks": clean(row.get("Admin Remarks")),
                    "created_at": clean(row.get("Created At")) or now_ist_string(),
                    "updated_at": clean(row.get("Updated At")) or now_ist_string(),
                    "updated_by": "csv_import",
                }

                if not record["name"] or not record["phone_number"]:
                    print(f"Skipping row {row_number}: Name or Phone Number missing")
                    skipped += 1
                    continue

                cur.execute(
                    "SELECT id FROM screening_registrations WHERE phone_number = ?",
                    (record["phone_number"],),
                )
                existing = cur.fetchone()

                if existing:
                    record_id = existing[0]
                    cur.execute("""
                    UPDATE screening_registrations
                    SET name = :name,
                        age_group = :age_group,
                        social_background = :social_background,
                        primary_language = :primary_language,
                        remarks = :remarks,
                        selection_status = :selection_status,
                        admin_remarks = :admin_remarks,
                        updated_at = :updated_at,
                        updated_by = :updated_by
                    WHERE phone_number = :phone_number
                    """, record)
                    action = "CSV_UPDATE_REGISTRATION"
                    updated += 1
                else:
                    cur.execute("""
                    INSERT INTO screening_registrations
                    (name, age_group, social_background, primary_language, phone_number,
                     remarks, selection_status, admin_remarks, created_at, updated_at, updated_by)
                    VALUES
                    (:name, :age_group, :social_background, :primary_language, :phone_number,
                     :remarks, :selection_status, :admin_remarks, :created_at, :updated_at, :updated_by)
                    """, record)
                    record_id = cur.lastrowid
                    action = "CSV_IMPORT_REGISTRATION"
                    inserted += 1

                cur.execute("""
                INSERT INTO audit_logs
                (user_id, action, module_name, record_id, old_value, new_value, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    None,
                    action,
                    "screening_registrations",
                    record_id,
                    "",
                    json.dumps(record, ensure_ascii=False),
                    now_ist_string(),
                ))

            conn.commit()
        finally:
            conn.close()

    print("CSV import completed.")
    print(f"Database: {db_file}")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="Path to registrations CSV file")
    parser.add_argument("--db", default=None, help="Path to SQLite DB. Default: auto-detect or backend/payana.db")
    args = parser.parse_args()

    csv_file = Path(args.csv_file)
    db_file = Path(args.db) if args.db else find_default_db()

    import_csv(csv_file, db_file)

if __name__ == "__main__":
    main()
