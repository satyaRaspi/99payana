"""
Delete all Payana / Mysore screening registrations safely.

Usage from C:\99mysore:

    python delete_all_registrations.py

For automatic confirmation:

    python delete_all_registrations.py --yes

For a different DB path:

    python delete_all_registrations.py --db backend\payana.db --yes

What it deletes:
- screening_registrations
- feedback/survey responses linked to those registration phone numbers
- custom survey answers linked to those survey responses

What it preserves:
- admin users
- app settings
- film/screening details
- survey builder questions
- page/menu settings
- uploaded files
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DEFAULT_DB = Path("backend") / "payana.db"


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    if not table_exists(conn, table_name):
        return False
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def count_table(conn: sqlite3.Connection, table_name: str) -> int:
    if not table_exists(conn, table_name):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def backup_database(db_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}_backup_before_delete_registrations_{timestamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def delete_all_registrations(db_path: Path, assume_yes: bool = False) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        registrations_count = count_table(conn, "screening_registrations")
        survey_count = count_table(conn, "survey_responses")
        custom_count = count_table(conn, "survey_custom_answers")

        print("\nPayana Registration Delete Utility")
        print("----------------------------------")
        print(f"Database: {db_path.resolve()}")
        print(f"Registrations found: {registrations_count}")
        print(f"Survey responses found: {survey_count}")
        print(f"Custom survey answers found: {custom_count}")

        if registrations_count == 0:
            print("\nNo registrations found. Nothing to delete.")
            return

        if not assume_yes:
            print("\nThis will delete all registrations and linked feedback/custom answers.")
            print("Admin users, settings, screening details, and survey builder questions will be preserved.")
            confirmation = input('\nType DELETE to continue: ').strip()
            if confirmation != "DELETE":
                print("Cancelled. No records were deleted.")
                return

        backup_path = backup_database(db_path)
        print(f"\nBackup created: {backup_path}")

        # Collect phone numbers before deleting registrations so linked survey rows can be cleaned.
        phone_numbers: list[str] = []
        if column_exists(conn, "screening_registrations", "phone_number"):
            rows = conn.execute(
                "SELECT phone_number FROM screening_registrations WHERE phone_number IS NOT NULL AND phone_number <> ''"
            ).fetchall()
            phone_numbers = [str(r["phone_number"]) for r in rows]

        survey_response_ids: list[int] = []
        if phone_numbers and table_exists(conn, "survey_responses") and column_exists(conn, "survey_responses", "phone_number"):
            placeholders = ",".join("?" for _ in phone_numbers)
            rows = conn.execute(
                f"SELECT id FROM survey_responses WHERE phone_number IN ({placeholders})",
                phone_numbers,
            ).fetchall()
            survey_response_ids = [int(r["id"]) for r in rows]

        # Some app versions may use registration_id in survey_responses.
        if table_exists(conn, "survey_responses") and column_exists(conn, "survey_responses", "registration_id"):
            rows = conn.execute(
                "SELECT id FROM survey_responses WHERE registration_id IN (SELECT id FROM screening_registrations)"
            ).fetchall()
            survey_response_ids.extend(int(r["id"]) for r in rows)

        survey_response_ids = sorted(set(survey_response_ids))

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN")

        deleted_custom_answers = 0
        deleted_survey_responses = 0
        deleted_registrations = 0

        if survey_response_ids and table_exists(conn, "survey_custom_answers"):
            placeholders = ",".join("?" for _ in survey_response_ids)
            cur = conn.execute(
                f"DELETE FROM survey_custom_answers WHERE survey_response_id IN ({placeholders})",
                survey_response_ids,
            )
            deleted_custom_answers = cur.rowcount if cur.rowcount is not None else 0

        if survey_response_ids and table_exists(conn, "survey_responses"):
            placeholders = ",".join("?" for _ in survey_response_ids)
            cur = conn.execute(
                f"DELETE FROM survey_responses WHERE id IN ({placeholders})",
                survey_response_ids,
            )
            deleted_survey_responses = cur.rowcount if cur.rowcount is not None else 0

        if table_exists(conn, "screening_registrations"):
            cur = conn.execute("DELETE FROM screening_registrations")
            deleted_registrations = cur.rowcount if cur.rowcount is not None else 0

            # Reset auto-increment counter for a clean registration sequence.
            if table_exists(conn, "sqlite_sequence"):
                conn.execute("DELETE FROM sqlite_sequence WHERE name='screening_registrations'")

        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")

        print("\nDelete completed successfully.")
        print(f"Registrations deleted: {deleted_registrations}")
        print(f"Survey responses deleted: {deleted_survey_responses}")
        print(f"Custom survey answers deleted: {deleted_custom_answers}")
        print(f"Backup retained at: {backup_path}")

    except Exception:
        conn.rollback()
        print("\nError occurred. Changes were rolled back.")
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete all Payana screening registrations safely.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to payana.db. Default: backend\\payana.db")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt.")
    args = parser.parse_args()

    delete_all_registrations(Path(args.db), assume_yes=args.yes)


if __name__ == "__main__":
    main()
