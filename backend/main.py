from __future__ import annotations

import csv
import hashlib
import os
import hmac
import io
import json
import secrets
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

APP_NAME = "Payana Screening Registration"
APP_VERSION = "1.2.40"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "payana.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
IST = ZoneInfo("Asia/Kolkata")
SESSION_HOURS = 12
SHORTLIST_LIMIT = 40

AGE_GROUPS = ["Below 18", "18-25", "26-35", "36-45", "46-60", "Above 60"]
SOCIAL_BACKGROUNDS = [
    "Student",
    "Working Professional",
    "Business / Self-employed",
    "Homemaker",
    "Retired",
    "Film / Media Background",
    "Artist / Creative Background",
    "General Audience",
    "Other",
]
PRIMARY_LANGUAGES = ["Kannada", "English", "Hindi", "Tamil", "Telugu", "Malayalam", "Marathi", "Other"]
STATUSES = ["Registered", "Approved", "Shortlisted", "Waitlisted", "Rejected", "Attended", "No Show"]
ROLES = ["Super Admin", "Admin", "Viewer"]
FILM_LANGUAGES = ["Kannada", "English", "Hindi", "Tamil", "Telugu", "Malayalam", "Marathi", "Other"]
FILM_GENRES = [
    "Drama", "Family", "Romance", "Thriller", "Comedy", "Social / Realistic", "Art / Festival",
    "Commercial", "Documentary", "Other"
]
RATINGS = [1, 2, 3, 4, 5]
YES_NO_MAYBE = ["Yes", "Maybe", "No"]
UNDERSTOOD_OPTIONS = ["Yes", "Mostly", "Somewhat", "No"]

DEFAULT_PAGES = [
    ("landing", "Home", "public", 1, 1),
    ("register", "Register", "public", 1, 2),
    ("survey", "Audience Survey", "public", 1, 3),
    ("admin", "Admin", "public", 1, 4),
    ("registrations", "Registrations", "admin", 1, 1),
    ("screeningDetails", "Film & Audience Details", "admin", 1, 2),
    ("surveyReport", "Survey Report", "admin", 1, 3),
    ("surveyBuilder", "Survey Builder", "admin", 1, 4),
    ("analytics", "Analytics", "admin", 1, 5),
    ("surveyAnalytics", "Feedback Analytics", "admin", 0, 6),
    ("pageSettings", "Landing Button Settings", "admin", 1, 7),
    ("users", "User Management", "admin", 1, 7),
    ("audit", "Audit Logs", "admin", 1, 8),
]

app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


def now_iso() -> str:
    return datetime.now(IST).replace(microsecond=0).isoformat()


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



def migrate_survey_responses_remove_fk(conn: sqlite3.Connection) -> None:
    """Remove old FK constraint from survey_responses if present.

    Some local databases created from earlier builds have a strict FK on
    survey_responses.registration_id. Feedback should be allowed even when the
    phone/reference is not pre-registered, so this rebuilds the table without
    that FK while preserving existing rows.
    """
    fk_rows = conn.execute("PRAGMA foreign_key_list(survey_responses)").fetchall()
    if not fk_rows:
        return

    cols = [r["name"] for r in conn.execute("PRAGMA table_info(survey_responses)").fetchall()]
    required = {"id", "registration_id", "name", "phone_number", "overall_rating", "story_rating", "acting_rating", "music_rating", "pace_rating", "emotional_impact_rating", "understood_story", "would_recommend", "contact_permission", "created_at", "updated_at"}
    if not required.issubset(set(cols)):
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("ALTER TABLE survey_responses RENAME TO survey_responses_old_fk")

    conn.execute("""
        CREATE TABLE survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id INTEGER NOT NULL DEFAULT 0,
            name TEXT NOT NULL,
            phone_number TEXT NOT NULL UNIQUE,
            overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
            story_rating INTEGER NOT NULL CHECK(story_rating BETWEEN 1 AND 5),
            acting_rating INTEGER NOT NULL CHECK(acting_rating BETWEEN 1 AND 5),
            music_rating INTEGER NOT NULL CHECK(music_rating BETWEEN 1 AND 5),
            pace_rating INTEGER NOT NULL CHECK(pace_rating BETWEEN 1 AND 5),
            emotional_impact_rating INTEGER NOT NULL CHECK(emotional_impact_rating BETWEEN 1 AND 5),
            visual_quality_rating INTEGER NOT NULL DEFAULT 5 CHECK(visual_quality_rating BETWEEN 1 AND 5),
            dialogue_rating INTEGER NOT NULL DEFAULT 5 CHECK(dialogue_rating BETWEEN 1 AND 5),
            length_rating INTEGER NOT NULL DEFAULT 5 CHECK(length_rating BETWEEN 1 AND 5),
            understood_story TEXT NOT NULL,
            connected_with_characters TEXT DEFAULT '',
            preferred_audience TEXT DEFAULT '',
            theatre_or_ott TEXT DEFAULT '',
            one_word_reaction TEXT DEFAULT '',
            audience_type TEXT DEFAULT '',
            consent_quote TEXT DEFAULT 'No',
            liked_most TEXT,
            improvements TEXT,
            memorable_scene TEXT,
            would_recommend TEXT NOT NULL,
            contact_permission TEXT NOT NULL,
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    copy_cols = [c for c in cols if c in {
        "id", "registration_id", "name", "phone_number", "overall_rating", "story_rating", "acting_rating",
        "music_rating", "pace_rating", "emotional_impact_rating", "visual_quality_rating", "dialogue_rating",
        "length_rating", "understood_story", "connected_with_characters", "preferred_audience", "theatre_or_ott",
        "one_word_reaction", "audience_type", "consent_quote", "liked_most", "improvements", "memorable_scene",
        "would_recommend", "contact_permission", "remarks", "created_at", "updated_at"
    }]
    col_sql = ", ".join(copy_cols)
    conn.execute(f"INSERT OR IGNORE INTO survey_responses ({col_sql}) SELECT {col_sql} FROM survey_responses_old_fk")
    conn.execute("DROP TABLE survey_responses_old_fk")
    conn.execute("PRAGMA foreign_keys = ON")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def poster_url(poster_path: str | None) -> str:
    if not poster_path:
        default = UPLOAD_DIR / "default_poster.png"
        return "/uploads/default_poster.png" if default.exists() else ""
    return f"/uploads/{Path(poster_path).name}"


def add_poster_urls(row: dict[str, Any]) -> dict[str, Any]:
    row["poster_url"] = poster_url(row.get("poster_path"))
    return row


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                phone_number TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Super Admin', 'Admin', 'Viewer')),
                is_active INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES admin_users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screening_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age_group TEXT NOT NULL,
                social_background TEXT NOT NULL,
                primary_language TEXT NOT NULL,
                phone_number TEXT NOT NULL UNIQUE,
                occupation TEXT DEFAULT '',
                remarks TEXT,
                selection_status TEXT NOT NULL DEFAULT 'Registered' CHECK(selection_status IN ('Registered', 'Approved', 'Shortlisted', 'Waitlisted', 'Rejected', 'Attended', 'No Show')),
                admin_remarks TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY(updated_by) REFERENCES admin_users(id)
            );

            CREATE TABLE IF NOT EXISTS screening_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                film_title TEXT NOT NULL,
                film_language TEXT NOT NULL,
                genre TEXT NOT NULL,
                duration_minutes INTEGER,
                director TEXT,
                producer TEXT,
                synopsis TEXT,
                screening_date TEXT,
                screening_time TEXT,
                venue_name TEXT,
                venue_city TEXT,
                expected_audience_count INTEGER DEFAULT 40,
                actual_audience_count INTEGER DEFAULT 0,
                audience_age_mix TEXT,
                audience_language_mix TEXT,
                audience_social_mix TEXT,
                audience_occupation_mix TEXT,
                remarks TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY(updated_by) REFERENCES admin_users(id)
            );

            CREATE TABLE IF NOT EXISTS survey_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone_number TEXT NOT NULL UNIQUE,
                overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
                story_rating INTEGER NOT NULL CHECK(story_rating BETWEEN 1 AND 5),
                acting_rating INTEGER NOT NULL CHECK(acting_rating BETWEEN 1 AND 5),
                music_rating INTEGER NOT NULL CHECK(music_rating BETWEEN 1 AND 5),
                pace_rating INTEGER NOT NULL CHECK(pace_rating BETWEEN 1 AND 5),
                emotional_impact_rating INTEGER NOT NULL CHECK(emotional_impact_rating BETWEEN 1 AND 5),
                visual_quality_rating INTEGER NOT NULL DEFAULT 5 CHECK(visual_quality_rating BETWEEN 1 AND 5),
                dialogue_rating INTEGER NOT NULL DEFAULT 5 CHECK(dialogue_rating BETWEEN 1 AND 5),
                length_rating INTEGER NOT NULL DEFAULT 5 CHECK(length_rating BETWEEN 1 AND 5),
                understood_story TEXT NOT NULL,
                connected_with_characters TEXT DEFAULT '',
                preferred_audience TEXT DEFAULT '',
                theatre_or_ott TEXT DEFAULT '',
                one_word_reaction TEXT DEFAULT '',
                audience_type TEXT DEFAULT '',
                consent_quote TEXT DEFAULT 'No',
                liked_most TEXT,
                improvements TEXT,
                memorable_scene TEXT,
                would_recommend TEXT NOT NULL,
                contact_permission TEXT NOT NULL,
                remarks TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(registration_id) REFERENCES screening_registrations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS survey_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                display_order INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY(updated_by) REFERENCES admin_users(id)
            );

            CREATE TABLE IF NOT EXISTS survey_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL CHECK(question_type IN ('multiple_choice', 'short_text')),
                options_json TEXT NOT NULL DEFAULT '[]',
                is_required INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY(section_id) REFERENCES survey_sections(id) ON DELETE CASCADE,
                FOREIGN KEY(updated_by) REFERENCES admin_users(id)
            );

            CREATE TABLE IF NOT EXISTS survey_custom_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(survey_response_id) REFERENCES survey_responses(id) ON DELETE CASCADE,
                FOREIGN KEY(question_id) REFERENCES survey_questions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS page_settings (
                page_key TEXT PRIMARY KEY,
                page_label TEXT NOT NULL,
                page_type TEXT NOT NULL CHECK(page_type IN ('public', 'admin')),
                is_visible INTEGER NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                module_name TEXT NOT NULL,
                record_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES admin_users(id)
            );
            """
        )
        reg_schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='screening_registrations'").fetchone()["sql"]
        if "Approved" not in reg_schema:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("ALTER TABLE screening_registrations RENAME TO screening_registrations_old")
            conn.execute(
                """
                CREATE TABLE screening_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age_group TEXT NOT NULL,
                    social_background TEXT NOT NULL,
                    primary_language TEXT NOT NULL,
                    phone_number TEXT NOT NULL UNIQUE,
                    occupation TEXT DEFAULT '',
                    remarks TEXT,
                    selection_status TEXT NOT NULL DEFAULT 'Registered' CHECK(selection_status IN ('Registered', 'Approved', 'Shortlisted', 'Waitlisted', 'Rejected', 'Attended', 'No Show')),
                    admin_remarks TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by INTEGER,
                    FOREIGN KEY(updated_by) REFERENCES admin_users(id)
                )
                """
            )
            conn.execute(
                """
                INSERT INTO screening_registrations(id, name, age_group, social_background, primary_language, phone_number, occupation, remarks, selection_status, admin_remarks, created_at, updated_at, updated_by)
                SELECT id, name, age_group, social_background, primary_language, phone_number, COALESCE(occupation, ''), remarks, selection_status, admin_remarks, created_at, updated_at, updated_by
                FROM screening_registrations_old
                """
            )
            conn.execute("DROP TABLE screening_registrations_old")
            conn.execute("PRAGMA foreign_keys = ON")

        ensure_column(conn, "screening_details", "poster_path", "TEXT")
        ensure_column(conn, "survey_responses", "visual_quality_rating", "INTEGER NOT NULL DEFAULT 5")
        ensure_column(conn, "survey_responses", "dialogue_rating", "INTEGER NOT NULL DEFAULT 5")
        ensure_column(conn, "survey_responses", "length_rating", "INTEGER NOT NULL DEFAULT 5")
        ensure_column(conn, "survey_responses", "connected_with_characters", "TEXT DEFAULT ''")
        ensure_column(conn, "survey_responses", "preferred_audience", "TEXT DEFAULT ''")
        ensure_column(conn, "survey_responses", "theatre_or_ott", "TEXT DEFAULT ''")
        ensure_column(conn, "survey_responses", "one_word_reaction", "TEXT DEFAULT ''")
        ensure_column(conn, "survey_responses", "audience_type", "TEXT DEFAULT ''")
        ensure_column(conn, "survey_responses", "consent_quote", "TEXT DEFAULT 'No'")
        ts = now_iso()
        count = conn.execute("SELECT COUNT(*) AS count FROM admin_users").fetchone()["count"]
        if count == 0:
            conn.execute(
                """
                INSERT INTO admin_users(full_name, username, phone_number, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                ("Default Super Admin", "admin", "", hash_password("admin123"), "Super Admin", ts, ts),
            )
            audit(conn, None, "CREATE_DEFAULT_ADMIN", "User Management", 1, None, "username=admin")

        for key, label, ptype, visible, order in DEFAULT_PAGES:
            conn.execute(
                """
                INSERT OR IGNORE INTO page_settings(page_key, page_label, page_type, is_visible, display_order, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, label, ptype, visible, order, ts),
            )

        # v1.2.12 configurable survey builder seed questions for honest criticism.
        section_count = conn.execute("SELECT COUNT(*) AS count FROM survey_sections").fetchone()["count"]
        if section_count == 0:
            sections = [
                ("before_poster", "Before Screening: Poster & Expectations", "Quick reaction before watching the film.", 1),
                ("after_core", "After Screening: Honest Film Feedback", "Be direct. This helps the makers improve positioning and edits.", 2),
                ("after_pace", "Pace, Length & Removal Suggestions", "Tell us what felt slow, unnecessary, or confusing.", 3),
                ("after_final", "Final Recommendation", "Recommendation, audience fit, and permission to contact.", 4),
            ]
            section_ids = {}
            for key, title, desc, order in sections:
                cur = conn.execute("INSERT INTO survey_sections(section_key, title, description, display_order, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)", (key, title, desc, order, ts, ts))
                section_ids[key] = cur.lastrowid
            questions = [
                ("before_poster", "What is your honest first impression of the poster?", "short_text", [], 0, 1),
                ("before_poster", "Based on the poster, what kind of film do you expect?", "multiple_choice", ["Family drama", "Travel story", "Emotional drama", "Children/grandparent bonding", "Art/festival film", "Commercial film", "Not sure"], 0, 2),
                ("before_poster", "Does the poster make you want to watch the film?", "multiple_choice", ["Yes", "Maybe", "No"], 0, 3),
                ("after_core", "What are the strongest/highest points of the film?", "short_text", [], 1, 10),
                ("after_core", "What are the weakest/lowest points of the film?", "short_text", [], 1, 11),
                ("after_core", "What did you not like or find unconvincing?", "short_text", [], 0, 12),
                ("after_core", "How strong is the grandfather-grandson emotional bonding?", "multiple_choice", ["Very strong", "Strong", "Average", "Weak", "Did not work"], 1, 13),
                ("after_core", "How engaging is the antique camera journey from Mysore to Jaipur?", "multiple_choice", ["Very engaging", "Engaging", "Average", "Slow", "Not engaging"], 1, 14),
                ("after_pace", "Which portions felt slow? Mention scenes or broad parts.", "short_text", [], 1, 20),
                ("after_pace", "What would you remove, shorten, or rewrite?", "short_text", [], 1, 21),
                ("after_pace", "Was any part confusing or unclear?", "short_text", [], 0, 22),
                ("after_pace", "How did the film length feel?", "multiple_choice", ["Perfect", "Slightly long", "Too long", "Slightly short", "Too short"], 1, 23),
                ("after_final", "Would you recommend this film to others?", "multiple_choice", ["Yes", "Maybe", "No"], 1, 30),
                ("after_final", "Who is the right audience for this film?", "short_text", [], 0, 31),
                ("after_final", "One honest line to the director/editor.", "short_text", [], 0, 32),
            ]
            for skey, text, qtype, opts, req, order in questions:
                conn.execute("INSERT INTO survey_questions(section_id, question_text, question_type, options_json, is_required, display_order, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)", (section_ids[skey], text, qtype, json.dumps(opts), 1 if req else 0, order, ts, ts))

        config_defaults = {
            "registration_success_message": "Thank you for registering. Seats are limited. Shortlisted participants will be contacted separately.",
            "registration_waitlist_message": "Thank you for your interest. We have received enough registrations for the screening. Your registration has been kept on the waitlist and will be prioritised if seats open up.",
            "waitlist_threshold": "40",
            "landing_show_registration_button": "1",
            "landing_show_survey_button": "1",
            "landing_show_feedback_qr_button": "1",
        }
        for key, value in config_defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                (key, value, ts),
            )

        # v1.2.9 one-time migration: default landing-page CTA buttons to visible.
        # This fixes existing deployments where Registration/Survey buttons may have been hidden
        # from older configuration data. After this migration runs once, Super Admin changes persist.
        flag = conn.execute("SELECT config_value FROM app_config WHERE config_key = 'landing_buttons_defaulted_v129'").fetchone()
        if not flag:
            conn.execute(
                "UPDATE page_settings SET is_visible = 1, updated_at = ? WHERE page_type = 'public' AND page_key IN ('register', 'survey')",
                (ts,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_buttons_defaulted_v129', '1', ts),
            )

        # v1.2.11: landing CTA button visibility is independent of the public/admin menu.
        # Keep public navigation available and default both landing buttons ON for fresh/Railway deploys.
        flag = conn.execute("SELECT config_value FROM app_config WHERE config_key = 'landing_buttons_migrated_v1211'").fetchone()
        if not flag:
            conn.execute(
                "UPDATE page_settings SET is_visible = 1, updated_at = ? WHERE page_type = 'public' AND page_key IN ('landing', 'register', 'survey', 'admin')",
                (ts,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_show_registration_button', '1', ts),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_show_survey_button', '1', ts),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_buttons_migrated_v1211', '1', ts),
            )

        # v1.2.32: Feedback QR link has an independent landing-page checkbox.
        flag = conn.execute("SELECT config_value FROM app_config WHERE config_key = 'landing_qr_config_migrated_v1223'").fetchone()
        if not flag:
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_show_feedback_qr_button', '1', ts),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?)",
                ('landing_qr_config_migrated_v1223', '1', ts),
            )

        # Seed a default screening row for the landing page if none exists yet.
        s_count = conn.execute("SELECT COUNT(*) AS count FROM screening_details").fetchone()["count"]
        if s_count == 0:
            conn.execute(
                """
                INSERT INTO screening_details(
                    film_title, film_language, genre, duration_minutes, director, producer, synopsis,
                    screening_date, screening_time, venue_name, venue_city, expected_audience_count,
                    actual_audience_count, audience_age_mix, audience_language_mix, audience_social_mix,
                    audience_occupation_mix, remarks, poster_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Mysore Studio", "Kannada", "Drama", None, "Praveen M Prabhu", "PK Picture and High5Studio",
                    "A warm, nostalgic story about memories, cinema, and relationships.",
                    "2026-07-12", "16:00", "Club Luxuria, The Icon Apartments, Thanisandra Road", "Bangalore", 40, 0,
                    "To be updated after registrations", "To be updated after registrations",
                    "To be updated after registrations", "To be updated after registrations",
                    "Private screening and audience feedback session. 12 July 2026, 4:00 PM onwards.",
                    "default_poster.png", ts, ts,
                ),
            )
        conn.commit()


def audit(conn: sqlite3.Connection, user_id: int | None, action: str, module_name: str, record_id: int | None, old: Any, new: Any) -> None:
    conn.execute(
        """
        INSERT INTO audit_logs(user_id, action, module_name, record_id, old_value, new_value, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            action,
            module_name,
            record_id,
            None if old is None else json.dumps(old, ensure_ascii=False, default=str) if not isinstance(old, str) else old,
            None if new is None else json.dumps(new, ensure_ascii=False, default=str) if not isinstance(new, str) else new,
            now_iso(),
        ),
    )


@app.on_event("startup")
def startup() -> None:
    init_db()


class RegistrationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    age_group: str
    social_background: str
    primary_language: str
    phone_number: str | None = Field(default="", max_length=40)
    remarks: str | None = Field(default="", max_length=500)

    @field_validator("name", "phone_number", mode="before")
    @classmethod
    def strip_required(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("age_group")
    @classmethod
    def valid_age_group(cls, value: str) -> str:
        if value not in AGE_GROUPS:
            raise ValueError("Invalid age group")
        return value

    @field_validator("social_background")
    @classmethod
    def valid_social_background(cls, value: str) -> str:
        if value not in SOCIAL_BACKGROUNDS:
            raise ValueError("Invalid social background")
        return value

    @field_validator("primary_language")
    @classmethod
    def valid_language(cls, value: str) -> str:
        if value not in PRIMARY_LANGUAGES:
            raise ValueError("Invalid primary language")
        return value

    @field_validator("phone_number")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch.isdigit())
        if len(cleaned) != 10:
            raise ValueError("Phone number must be 10 digits")
        return cleaned

    @field_validator("remarks", mode="before")
    @classmethod
    def strip_remarks(cls, value: Any) -> str:
        return str(value or "").strip()


class RegistrationUpdate(RegistrationCreate):
    selection_status: str = "Registered"
    admin_remarks: str | None = Field(default="", max_length=500)

    @field_validator("selection_status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in STATUSES:
            raise ValueError("Invalid selection status")
        return value


class StatusUpdate(BaseModel):
    selection_status: str
    admin_remarks: str | None = Field(default="", max_length=500)

    @field_validator("selection_status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in STATUSES:
            raise ValueError("Invalid selection status")
        return value


class BulkStatusUpdate(BaseModel):
    ids: list[int]
    selection_status: str = "Approved"
    admin_remarks: str | None = Field(default="", max_length=500)

    @field_validator("selection_status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in STATUSES:
            raise ValueError("Invalid selection status")
        return value


class AiApprovalApply(BaseModel):
    ids: list[int]


class AppConfigUpdate(BaseModel):
    registration_success_message: str = Field(max_length=1000)
    registration_waitlist_message: str = Field(max_length=1000)
    waitlist_threshold: int = Field(default=40, ge=0, le=100000)


class SurveyCreate(BaseModel):
    name: str | None = Field(default="", max_length=120)
    phone_number: str | None = Field(default="", max_length=40)
    overall_rating: int = Field(ge=1, le=5)
    story_rating: int = Field(ge=1, le=5)
    acting_rating: int = Field(ge=1, le=5)
    music_rating: int = Field(ge=1, le=5)
    pace_rating: int = Field(ge=1, le=5)
    emotional_impact_rating: int = Field(ge=1, le=5)
    visual_quality_rating: int = Field(default=5, ge=1, le=5)
    dialogue_rating: int = Field(default=5, ge=1, le=5)
    length_rating: int = Field(default=5, ge=1, le=5)
    understood_story: str = "Mostly"
    connected_with_characters: str | None = Field(default="", max_length=40)
    preferred_audience: str | None = Field(default="", max_length=120)
    theatre_or_ott: str | None = Field(default="", max_length=40)
    one_word_reaction: str | None = Field(default="", max_length=120)
    audience_type: str | None = Field(default="", max_length=120)
    consent_quote: str | None = Field(default="No", max_length=10)
    liked_most: str | None = Field(default="", max_length=1000)
    improvements: str | None = Field(default="", max_length=1000)
    memorable_scene: str | None = Field(default="", max_length=1000)
    would_recommend: str = "Maybe"
    contact_permission: str = "Yes"
    remarks: str | None = Field(default="", max_length=1000)
    consent_contact: str | None = Field(default="Yes", max_length=10)
    custom_answers: dict[str, Any] = Field(default_factory=dict)
    @field_validator("name", "phone_number", "liked_most", "improvements", "memorable_scene", "remarks", "connected_with_characters", "preferred_audience", "theatre_or_ott", "one_word_reaction", "audience_type", "consent_quote", "consent_contact", "understood_story", "would_recommend", "contact_permission", mode="before")
    @classmethod
    def strip_optional_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_feedback_phone(cls, value: Any) -> str:
        return str(value or "").strip()[:40]


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminUserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=60)
    phone_number: str | None = Field(default="", max_length=15)
    password: str = Field(min_length=6, max_length=100)
    role: str = "Admin"

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        if value not in ROLES:
            raise ValueError("Invalid role")
        return value

    @field_validator("username", "full_name", "phone_number", mode="before")
    @classmethod
    def strip_values(cls, value: Any) -> str:
        return str(value or "").strip()


class AdminUserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone_number: str | None = Field(default="", max_length=15)
    role: str

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        if value not in ROLES:
            raise ValueError("Invalid role")
        return value


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=100)


class ActiveUpdate(BaseModel):
    is_active: bool


class PageSettingPayload(BaseModel):
    page_label: str = Field(min_length=1, max_length=80)
    is_visible: bool
    display_order: int = Field(ge=1, le=999)


class PageSettingsUpdate(BaseModel):
    items: list[dict[str, Any]]


class LandingButtonSettingsUpdate(BaseModel):
    show_registration_button: bool = True
    show_survey_button: bool = True
    show_feedback_qr_button: bool = True


class SurveySectionPayload(BaseModel):
    section_key: str | None = Field(default="", max_length=80)
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default="", max_length=500)
    display_order: int = Field(default=1, ge=1, le=999)
    is_active: bool = True


class SurveyQuestionPayload(BaseModel):
    section_id: int
    question_text: str = Field(min_length=3, max_length=500)
    question_type: str
    options: list[str] = Field(default_factory=list)
    is_required: bool = False
    display_order: int = Field(default=1, ge=1, le=999)
    is_active: bool = True

    @field_validator("question_type")
    @classmethod
    def valid_question_type(cls, value: str) -> str:
        if value not in {"multiple_choice", "short_text"}:
            raise ValueError("Question type must be multiple_choice or short_text")
        return value


class ScreeningDetailsPayload(BaseModel):
    film_title: str = Field(min_length=2, max_length=160)
    film_language: str
    genre: str
    duration_minutes: int | None = Field(default=None, ge=1, le=400)
    director: str | None = Field(default="", max_length=120)
    producer: str | None = Field(default="", max_length=120)
    synopsis: str | None = Field(default="", max_length=1000)
    screening_date: str | None = Field(default="", max_length=20)
    screening_time: str | None = Field(default="", max_length=30)
    venue_name: str | None = Field(default="", max_length=160)
    venue_city: str | None = Field(default="", max_length=120)
    expected_audience_count: int | None = Field(default=40, ge=0, le=10000)
    actual_audience_count: int | None = Field(default=0, ge=0, le=10000)
    audience_age_mix: str | None = Field(default="", max_length=1000)
    audience_language_mix: str | None = Field(default="", max_length=1000)
    audience_social_mix: str | None = Field(default="", max_length=1000)
    audience_occupation_mix: str | None = Field(default="", max_length=1000)
    remarks: str | None = Field(default="", max_length=1000)

    @field_validator("film_title", "film_language", "genre", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator(
        "director", "producer", "synopsis", "screening_date", "screening_time", "venue_name", "venue_city",
        "audience_age_mix", "audience_language_mix", "audience_social_mix", "audience_occupation_mix", "remarks",
        mode="before"
    )
    @classmethod
    def strip_optional_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("film_language")
    @classmethod
    def valid_film_language(cls, value: str) -> str:
        if value not in FILM_LANGUAGES:
            raise ValueError("Invalid film language")
        return value

    @field_validator("genre")
    @classmethod
    def valid_genre(cls, value: str) -> str:
        if value not in FILM_GENRES:
            raise ValueError("Invalid genre")
        return value


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    token = authorization.split(" ", 1)[1].strip()
    with connect() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        if parse_dt(session["expires_at"]) < datetime.now(IST):
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        user = conn.execute("SELECT * FROM admin_users WHERE id = ?", (session["user_id"],)).fetchone()
        if not user or not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        return dict(user) | {"token": token}


def require_roles(*roles: str):
    def _inner(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this action")
        return user
    return _inner



@app.get("/api/admin/survey-responses/export")
def export_survey_responses(user: dict[str, Any] = Depends(get_current_user)):
    """Download feedback responses as CSV.

    Uses the app's native connect() helper and dynamically reads the current
    database schema so older local databases do not break export.
    """
    with connect() as conn:
        survey_cols = [r["name"] for r in conn.execute("PRAGMA table_info(survey_responses)").fetchall()]
        reg_cols = [r["name"] for r in conn.execute("PRAGMA table_info(screening_registrations)").fetchall()]

        output = io.StringIO()
        writer = csv.writer(output)

        if not survey_cols:
            writer.writerow(["Message"])
            writer.writerow(["No feedback response table found"])
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=feedback_responses.csv"}
            )

        sr_select = [f"sr.{col} AS sr_{col}" for col in survey_cols]
        reg_join_cols = [col for col in ["name", "age_group", "social_background", "primary_language", "selection_status"] if col in reg_cols]
        reg_select = [f"r.{col} AS reg_{col}" for col in reg_join_cols]

        join_sql = ""
        if "phone_number" in survey_cols and "phone_number" in reg_cols:
            join_sql = "LEFT JOIN screening_registrations r ON r.phone_number = sr.phone_number"
        else:
            reg_select = []
            reg_join_cols = []

        order_col = "created_at" if "created_at" in survey_cols else survey_cols[0]
        sql = f"""
            SELECT {', '.join(sr_select + reg_select)}
            FROM survey_responses sr
            {join_sql}
            ORDER BY sr.{order_col} DESC
        """
        rows = conn.execute(sql).fetchall()

        headers = [f"Feedback {col.replace('_', ' ').title()}" for col in survey_cols]
        headers.extend([f"Registration {col.replace('_', ' ').title()}" for col in reg_join_cols])
        writer.writerow(headers)

        for row in rows:
            line = [row[f"sr_{col}"] for col in survey_cols]
            line.extend([row[f"reg_{col}"] for col in reg_join_cols])
            writer.writerow(line)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=feedback_responses.csv"}
        )


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "app": APP_NAME, "version": APP_VERSION}


@app.get("/api/options")
def options() -> dict[str, Any]:
    return {
        "age_groups": AGE_GROUPS,
        "social_backgrounds": SOCIAL_BACKGROUNDS,
        "primary_languages": PRIMARY_LANGUAGES,
        "statuses": STATUSES,
        "roles": ROLES,
        "film_languages": FILM_LANGUAGES,
        "film_genres": FILM_GENRES,
        "ratings": RATINGS,
        "yes_no_maybe": YES_NO_MAYBE,
        "understood_options": UNDERSTOOD_OPTIONS,
        "character_connection_options": ["Yes", "Somewhat", "No"],
        "theatre_or_ott_options": ["Theatre", "OTT", "Both", "Not sure"],
        "quote_consent_options": ["Yes", "No"],
    }



def survey_builder_payload(conn: sqlite3.Connection, active_only: bool = True) -> dict[str, Any]:
    """Return survey builder payload safely.

    Some recent builds referenced this helper but did not include the function,
    which caused the Survey Builder page to show Failed to fetch.
    """
    try:
        section_filter = "WHERE is_active = 1" if active_only else ""
        sections = [dict(r) for r in conn.execute(
            f"SELECT * FROM survey_sections {section_filter} ORDER BY display_order, id"
        ).fetchall()]

        payload_sections = []
        for section in sections:
            question_filter = "AND is_active = 1" if active_only else ""
            questions = [dict(r) for r in conn.execute(
                f"""
                SELECT * FROM survey_questions
                WHERE section_id = ? {question_filter}
                ORDER BY display_order, id
                """,
                (section["id"],),
            ).fetchall()]

            clean_questions = []
            for q in questions:
                try:
                    options = json.loads(q.get("options_json") or "[]")
                    if not isinstance(options, list):
                        options = []
                except Exception:
                    options = []
                item = dict(q)
                item["options"] = options
                clean_questions.append(item)

            sec = dict(section)
            sec["questions"] = clean_questions
            payload_sections.append(sec)

        return {"sections": payload_sections}
    except sqlite3.Error:
        return {"sections": []}


@app.get("/api/survey-builder")
def get_public_survey_builder() -> dict[str, Any]:
    with connect() as conn:
        return survey_builder_payload(conn, active_only=True)


@app.get("/api/menu-pages")
def public_menu_pages() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM page_settings WHERE page_type = 'public' ORDER BY display_order, page_key"
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@app.get("/api/landing")
def landing() -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM screening_details ORDER BY datetime(updated_at) DESC, id DESC LIMIT 1").fetchone()
        if row:
            data = add_poster_urls(dict(row))
            config = get_config(conn)
            data["app_config"] = config
            data["landing_buttons"] = landing_button_settings_from_config(config)
            return data
    return {
        "film_title": "Mysore Studio",
        "film_language": "Kannada",
        "genre": "Drama",
        "director": "Praveen M Prabhu",
        "screening_date": "2026-07-12",
        "screening_time": "16:00",
        "expected_audience_count": 40,
        "synopsis": "Private screening and feedback session.",
        "poster_url": poster_url("default_poster.png"),
        "app_config": {},
        "landing_buttons": {"show_registration_button": True, "show_survey_button": True, "show_feedback_qr_button": True},
    }


@app.post("/api/register", status_code=201)
def register(payload: RegistrationCreate) -> dict[str, Any]:
    ts = now_iso()
    try:
        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO screening_registrations
                (name, age_group, social_background, primary_language, phone_number, occupation, remarks, selection_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, '', ?, 'Registered', ?, ?)
                """,
                (
                    payload.name, payload.age_group, payload.social_background, payload.primary_language,
                    payload.phone_number, payload.remarks or "", ts, ts,
                ),
            )
            audit(conn, None, "PUBLIC_REGISTER", "Registration", cur.lastrowid, None, f"phone={payload.phone_number}")
            config = get_config(conn)
            threshold = int(config.get("waitlist_threshold", "40") or 40)
            total = conn.execute("SELECT COUNT(*) AS count FROM screening_registrations").fetchone()["count"]
            if threshold and total > threshold:
                message = config.get("registration_waitlist_message", "Thank you. You have been kept on the waitlist.")
            else:
                message = config.get("registration_success_message", "Registration completed")
            conn.commit()
            return {"message": message, "id": cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="This phone number has already been registered for the screening.")



def save_custom_survey_answers(conn: sqlite3.Connection, survey_response_id: int, custom_answers: dict[str, Any]) -> None:
    """Persist custom survey answers safely.

    Older builds referenced this helper without defining it. This version accepts
    string/int question ids and silently skips empty or invalid entries.
    """
    if not custom_answers:
        return
    ts = now_iso()
    for question_id, answer in (custom_answers or {}).items():
        try:
            qid = int(question_id)
        except (TypeError, ValueError):
            continue
        answer_text = str(answer or "").strip()
        if not answer_text:
            continue
        # Only save answers for questions that exist, to avoid FK errors in older DBs.
        exists = conn.execute("SELECT id FROM survey_questions WHERE id = ?", (qid,)).fetchone()
        if not exists:
            continue
        conn.execute(
            "INSERT INTO survey_custom_answers(survey_response_id, question_id, answer_text, created_at) VALUES (?, ?, ?, ?)",
            (survey_response_id, qid, answer_text[:2000], ts),
        )


@app.post("/api/survey", status_code=201)
def submit_survey(payload: SurveyCreate) -> dict[str, Any]:
    ts = now_iso()
    raw_phone = str(payload.phone_number or "").strip()
    phone = raw_phone[:40] if raw_phone else f"FB{int(datetime.now(IST).timestamp())}{secrets.token_hex(4)}"[:40]
    display_name = (payload.name or "Feedback Audience").strip() or "Feedback Audience"

    def ensure_registration(conn: sqlite3.Connection) -> sqlite3.Row | None:
        registration = conn.execute(
            "SELECT id, name, phone_number FROM screening_registrations WHERE phone_number = ?",
            (phone,),
        ).fetchone()
        if registration:
            return registration
        try:
            cur_reg = conn.execute(
                """
                INSERT INTO screening_registrations(
                    name, age_group, social_background, primary_language, phone_number,
                    occupation, remarks, selection_status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, '', ?, 'Attended', ?, ?)
                """,
                (
                    display_name,
                    AGE_GROUPS[0],
                    SOCIAL_BACKGROUNDS[-2] if len(SOCIAL_BACKGROUNDS) >= 2 else SOCIAL_BACKGROUNDS[0],
                    PRIMARY_LANGUAGES[0],
                    phone,
                    "Auto-created from feedback form. Phone/reference is not validated against registration.",
                    ts,
                    ts,
                ),
            )
            conn.commit()
            return conn.execute(
                "SELECT id, name, phone_number FROM screening_registrations WHERE id = ?",
                (cur_reg.lastrowid,),
            ).fetchone()
        except sqlite3.IntegrityError:
            conn.rollback()
            return conn.execute(
                "SELECT id, name, phone_number FROM screening_registrations WHERE phone_number = ?",
                (phone,),
            ).fetchone()

    def save_feedback(conn: sqlite3.Connection, registration_id: int) -> tuple[int, bool]:
        understood = payload.understood_story or "Mostly"
        would_recommend = payload.would_recommend or "Maybe"
        contact_permission = payload.contact_permission or "Yes"
        existing = conn.execute("SELECT id FROM survey_responses WHERE phone_number = ?", (phone,)).fetchone()
        if existing:
            response_id = existing["id"]
            conn.execute(
                """
                UPDATE survey_responses
                SET registration_id=?, name=?, overall_rating=?, story_rating=?, acting_rating=?,
                    music_rating=?, pace_rating=?, emotional_impact_rating=?, visual_quality_rating=?,
                    dialogue_rating=?, length_rating=?, understood_story=?, connected_with_characters=?,
                    preferred_audience=?, theatre_or_ott=?, one_word_reaction=?, audience_type=?, consent_quote=?,
                    liked_most=?, improvements=?, memorable_scene=?, would_recommend=?, contact_permission=?, remarks=?,
                    updated_at=?
                WHERE id=?
                """,
                (
                    registration_id, display_name, payload.overall_rating, payload.story_rating, payload.acting_rating,
                    payload.music_rating, payload.pace_rating, payload.emotional_impact_rating,
                    payload.visual_quality_rating, payload.dialogue_rating, payload.length_rating,
                    understood, payload.connected_with_characters or "", payload.preferred_audience or "",
                    payload.theatre_or_ott or "", payload.one_word_reaction or "", payload.audience_type or "",
                    payload.consent_quote or "No", payload.liked_most or "", payload.improvements or "",
                    payload.memorable_scene or "", would_recommend, contact_permission,
                    payload.remarks or "", ts, response_id,
                ),
            )
            return response_id, True

        cur = conn.execute(
            """
            INSERT INTO survey_responses(
                registration_id, name, phone_number, overall_rating, story_rating, acting_rating,
                music_rating, pace_rating, emotional_impact_rating, visual_quality_rating, dialogue_rating, length_rating,
                understood_story, connected_with_characters, preferred_audience, theatre_or_ott, one_word_reaction, audience_type, consent_quote,
                liked_most, improvements, memorable_scene, would_recommend, contact_permission, remarks,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registration_id, display_name, phone, payload.overall_rating,
                payload.story_rating, payload.acting_rating, payload.music_rating, payload.pace_rating,
                payload.emotional_impact_rating, payload.visual_quality_rating, payload.dialogue_rating, payload.length_rating,
                understood, payload.connected_with_characters or "", payload.preferred_audience or "",
                payload.theatre_or_ott or "", payload.one_word_reaction or "", payload.audience_type or "",
                payload.consent_quote or "No", payload.liked_most or "", payload.improvements or "",
                payload.memorable_scene or "", would_recommend, contact_permission,
                payload.remarks or "", ts, ts,
            ),
        )
        return cur.lastrowid, False

    with connect() as conn:
        registration = ensure_registration(conn)
        if not registration:
            raise HTTPException(status_code=500, detail="Could not prepare feedback reference.")

        try:
            response_id, was_update = save_feedback(conn, registration["id"])
        except sqlite3.IntegrityError as exc:
            # Older local DBs can still have FK constraints; migrate and retry once.
            if "FOREIGN KEY constraint failed" not in str(exc):
                raise
            conn.rollback()
            migrate_survey_responses_remove_fk(conn)
            conn.commit()
            registration = ensure_registration(conn)
            if not registration:
                raise HTTPException(status_code=500, detail="Could not prepare feedback reference after migration.")
            response_id, was_update = save_feedback(conn, registration["id"])

        if was_update:
            conn.execute("DELETE FROM survey_custom_answers WHERE survey_response_id = ?", (response_id,))
        save_custom_survey_answers(conn, response_id, payload.custom_answers or {})
        audit(conn, None, "SURVEY_UPDATE" if was_update else "SURVEY_SUBMIT", "Audience Survey", response_id, None, f"phone_or_ref={phone}")
        conn.commit()
        return {"message": "Thank you. Your feedback has been updated." if was_update else "Thank you for sharing your feedback.", "id": response_id}

@app.post("/api/admin/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    with connect() as conn:
        user = conn.execute("SELECT * FROM admin_users WHERE username = ?", (payload.username.strip(),)).fetchone()
        if not user or not user["is_active"] or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = secrets.token_urlsafe(32)
        ts = now_iso()
        expires_at = (datetime.now(IST) + timedelta(hours=SESSION_HOURS)).replace(microsecond=0).isoformat()
        conn.execute("INSERT INTO sessions(token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)", (token, user["id"], expires_at, ts))
        conn.execute("UPDATE admin_users SET last_login_at = ?, updated_at = ? WHERE id = ?", (ts, ts, user["id"]))
        audit(conn, user["id"], "LOGIN", "Auth", user["id"], None, "success")
        conn.commit()
        return {"token": token, "user": {"id": user["id"], "full_name": user["full_name"], "username": user["username"], "role": user["role"]}}


@app.post("/api/admin/logout")
def logout(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (user["token"],))
        audit(conn, user["id"], "LOGOUT", "Auth", user["id"], None, "success")
        conn.commit()
    return {"message": "Logged out"}


@app.get("/api/admin/me")
def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": user["id"], "full_name": user["full_name"], "username": user["username"], "role": user["role"]}


@app.get("/api/admin/dashboard")
def dashboard(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT selection_status, COUNT(*) AS count FROM screening_registrations GROUP BY selection_status").fetchall()
        counts = {status: 0 for status in STATUSES}
        for row in rows:
            counts[row["selection_status"]] = row["count"]
        survey_stats = conn.execute("SELECT COUNT(*) AS count, AVG(overall_rating) AS avg_rating FROM survey_responses").fetchone()
        return {
            "total": sum(counts.values()),
            "counts": counts,
            "shortlist_limit": SHORTLIST_LIMIT,
            "survey_count": survey_stats["count"] or 0,
            "average_overall_rating": round(survey_stats["avg_rating"] or 0, 2),
        }


@app.get("/api/admin/registrations")
def list_registrations(
    search: str = "",
    age_group: str = "",
    social_background: str = "",
    primary_language: str = "",
    selection_status: str = "",
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    sql = "SELECT * FROM screening_registrations WHERE 1=1"
    params: list[Any] = []
    if search:
        sql += " AND (name LIKE ? OR phone_number LIKE ? OR remarks LIKE ? OR admin_remarks LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if age_group:
        sql += " AND age_group = ?"; params.append(age_group)
    if social_background:
        sql += " AND social_background = ?"; params.append(social_background)
    if primary_language:
        sql += " AND primary_language = ?"; params.append(primary_language)
    if selection_status:
        sql += " AND selection_status = ?"; params.append(selection_status)
    sql += " ORDER BY datetime(created_at) DESC, id DESC"
    with connect() as conn:
        return {"items": [dict(r) for r in conn.execute(sql, params).fetchall()]}


@app.get("/api/admin/registrations/export.csv")
def export_registrations_csv(user: dict[str, Any] = Depends(get_current_user)) -> StreamingResponse:
    headers = ["Name", "Age Group", "Social Background", "Primary Language", "Phone Number", "Remarks", "Selection Status", "Admin Remarks", "Created At", "Updated At"]
    with connect() as conn:
        rows = conn.execute("SELECT * FROM screening_registrations ORDER BY datetime(created_at) DESC, id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r["name"], r["age_group"], r["social_background"], r["primary_language"], r["phone_number"], r["remarks"], r["selection_status"], r["admin_remarks"], r["created_at"], r["updated_at"]])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=registrations_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.csv"})




def normalize_csv_header(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def first_csv_value(row: dict[str, Any], aliases: list[str]) -> str:
    normalized = {normalize_csv_header(k): v for k, v in row.items()}
    for alias in aliases:
        key = normalize_csv_header(alias)
        if key in normalized and str(normalized[key] or "").strip():
            return str(normalized[key] or "").strip()
    return ""


def map_allowed_value(value: str, allowed: list[str], default: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    for item in allowed:
        if item.lower() == raw.lower():
            return item
    compact = normalize_csv_header(raw)
    for item in allowed:
        if normalize_csv_header(item) == compact:
            return item
    return default


def parse_csv_registrations(text: str, default_status: str = "Approved") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    parsed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not reader.fieldnames:
        return parsed, [{"row": 0, "error": "CSV has no header row"}]
    for index, row in enumerate(reader, start=2):
        name = first_csv_value(row, ["Name", "Full Name", "Participant Name", "Audience Name"])
        phone = first_csv_value(row, ["Phone Number", "Phone", "Mobile", "Mobile Number", "WhatsApp", "Whatsapp Number", "Contact Number"])
        age = first_csv_value(row, ["Age Group", "Age", "AgeGroup"])
        social = first_csv_value(row, ["Social Background", "Background", "Audience Background", "SocialBackground"])
        language = first_csv_value(row, ["Primary Language", "Language", "PrimaryLanguage", "Mother Tongue"])
        remarks = first_csv_value(row, ["Remarks", "Remark", "Comments", "Comment", "Notes", "Note"])
        status = first_csv_value(row, ["Selection Status", "Status", "Registration Status"]) or default_status
        admin_remarks = first_csv_value(row, ["Admin Remarks", "Admin Remark", "Admin Notes"])
        created_at = first_csv_value(row, ["Created At", "Created", "Created Date", "Created Date Time", "Created Date & Time"])
        updated_at = first_csv_value(row, ["Updated At", "Updated", "Updated Date", "Updated Date Time", "Updated Date & Time"])
        phone_digits = "".join(ch for ch in phone if ch.isdigit())[-10:]
        row_errors: list[str] = []
        if len(name) < 2:
            row_errors.append("Name is missing")
        if len(phone_digits) != 10:
            row_errors.append("Phone Number must contain 10 digits")
        age = map_allowed_value(age, AGE_GROUPS, "26-35")
        social = map_allowed_value(social, SOCIAL_BACKGROUNDS, "General Audience")
        language = map_allowed_value(language, PRIMARY_LANGUAGES, "Kannada")
        status = map_allowed_value(status, STATUSES, default_status if default_status in STATUSES else "Approved")
        if row_errors:
            errors.append({"row": index, "name": name, "phone_number": phone, "error": "; ".join(row_errors)})
            continue
        ts = now_iso()
        parsed.append({
            "name": name[:120],
            "age_group": age,
            "social_background": social,
            "primary_language": language,
            "phone_number": phone_digits,
            "remarks": remarks[:500],
            "selection_status": status,
            "admin_remarks": admin_remarks[:500],
            "created_at": created_at or ts,
            "updated_at": updated_at or ts,
        })
    return parsed, errors


@app.get("/api/admin/registrations/sample.csv")
def sample_registrations_csv(user: dict[str, Any] = Depends(get_current_user)) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Age Group", "Social Background", "Primary Language", "Phone Number", "Remarks", "Selection Status", "Admin Remarks"])
    writer.writerow(["Sample Audience", "36-45", "General Audience", "Kannada", "9876543210", "Interested in feedback screening", "Approved", "Imported sample row"])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=registration_upload_template.csv"})


@app.post("/api/admin/registrations/upload-csv")
async def upload_registrations_csv(
    file: UploadFile = File(...),
    default_status: str = Query(default="Approved"),
    user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin")),
) -> dict[str, Any]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    if default_status not in STATUSES:
        default_status = "Approved"
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(status_code=400, detail="CSV is too large. Please upload a file under 2 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    parsed, errors = parse_csv_registrations(text, default_status=default_status)
    inserted = 0
    updated = 0
    skipped_duplicates_in_file = 0
    seen: set[str] = set()
    ts = now_iso()
    with connect() as conn:
        for item in parsed:
            phone = item["phone_number"]
            if phone in seen:
                skipped_duplicates_in_file += 1
                errors.append({"row": None, "phone_number": phone, "error": "Duplicate phone number inside uploaded CSV; later row skipped"})
                continue
            seen.add(phone)
            existing = conn.execute("SELECT * FROM screening_registrations WHERE phone_number = ?", (phone,)).fetchone()
            if existing:
                old = dict(existing)
                conn.execute(
                    """
                    UPDATE screening_registrations
                    SET name=?, age_group=?, social_background=?, primary_language=?, remarks=?, selection_status=?, admin_remarks=?, updated_at=?, updated_by=?
                    WHERE phone_number=?
                    """,
                    (item["name"], item["age_group"], item["social_background"], item["primary_language"], item["remarks"], item["selection_status"], item["admin_remarks"] or old.get("admin_remarks") or "Imported from CSV", ts, user["id"], phone),
                )
                new = conn.execute("SELECT * FROM screening_registrations WHERE phone_number = ?", (phone,)).fetchone()
                audit(conn, user["id"], "CSV_UPDATE", "Registration", old["id"], old, dict(new))
                updated += 1
            else:
                cur = conn.execute(
                    """
                    INSERT INTO screening_registrations
                    (name, age_group, social_background, primary_language, phone_number, occupation, remarks, selection_status, admin_remarks, created_at, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?)
                    """,
                    (item["name"], item["age_group"], item["social_background"], item["primary_language"], phone, item["remarks"], item["selection_status"], item["admin_remarks"] or "Imported from CSV", item["created_at"], ts, user["id"]),
                )
                audit(conn, user["id"], "CSV_INSERT", "Registration", cur.lastrowid, None, item)
                inserted += 1
        audit(conn, user["id"], "CSV_IMPORT", "Registration", None, None, {"filename": file.filename, "inserted": inserted, "updated": updated, "errors": len(errors)})
        conn.commit()
    return {
        "filename": file.filename,
        "inserted": inserted,
        "updated": updated,
        "skipped_duplicates_in_file": skipped_duplicates_in_file,
        "errors": errors[:50],
        "error_count": len(errors),
        "total_rows_read": len(parsed) + len([e for e in errors if e.get("row")]),
    }

@app.get("/api/admin/registrations/{registration_id}")
def get_registration(registration_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Registration not found")
        return dict(row)


@app.put("/api/admin/registrations/{registration_id}")
def update_registration(registration_id: int, payload: RegistrationUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Registration not found")
        if payload.selection_status == "Shortlisted" and shortlist_count(conn, exclude_id=registration_id) >= SHORTLIST_LIMIT:
            raise HTTPException(status_code=400, detail=f"Shortlist limit of {SHORTLIST_LIMIT} already reached. Use Waitlisted.")
        ts = now_iso()
        try:
            conn.execute(
                """
                UPDATE screening_registrations SET name=?, age_group=?, social_background=?, primary_language=?, phone_number=?, remarks=?, selection_status=?, admin_remarks=?, updated_at=?, updated_by=? WHERE id=?
                """,
                (payload.name, payload.age_group, payload.social_background, payload.primary_language, payload.phone_number, payload.remarks or "", payload.selection_status, payload.admin_remarks or "", ts, user["id"], registration_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="This phone number is already used by another registration.")
        new = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        audit(conn, user["id"], "UPDATE", "Registration", registration_id, dict(old), dict(new))
        conn.commit()
        return dict(new)


@app.put("/api/admin/registrations/{registration_id}/status")
def update_status(registration_id: int, payload: StatusUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Registration not found")
        if payload.selection_status == "Shortlisted" and shortlist_count(conn, exclude_id=registration_id) >= SHORTLIST_LIMIT:
            raise HTTPException(status_code=400, detail=f"Shortlist limit of {SHORTLIST_LIMIT} already reached. Use Waitlisted.")
        ts = now_iso()
        conn.execute("UPDATE screening_registrations SET selection_status = ?, admin_remarks = ?, updated_at = ?, updated_by = ? WHERE id = ?", (payload.selection_status, payload.admin_remarks or old["admin_remarks"] or "", ts, user["id"], registration_id))
        new = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        audit(conn, user["id"], "UPDATE_STATUS", "Registration", registration_id, dict(old), dict(new))
        conn.commit()
        return dict(new)


@app.put("/api/admin/registrations-bulk-status")
def bulk_update_status(payload: BulkStatusUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    if not payload.ids:
        raise HTTPException(status_code=400, detail="Select at least one registration")
    unique_ids = sorted(set(payload.ids))
    with connect() as conn:
        if payload.selection_status == "Shortlisted" and shortlist_count(conn) + len(unique_ids) > SHORTLIST_LIMIT:
            raise HTTPException(status_code=400, detail=f"Shortlist limit of {SHORTLIST_LIMIT} would be exceeded. Use Approved or Waitlisted.")
        ts = now_iso()
        updated = 0
        for rid in unique_ids:
            old = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (rid,)).fetchone()
            if not old:
                continue
            conn.execute("UPDATE screening_registrations SET selection_status = ?, admin_remarks = ?, updated_at = ?, updated_by = ? WHERE id = ?", (payload.selection_status, payload.admin_remarks or old["admin_remarks"] or "", ts, user["id"], rid))
            new = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (rid,)).fetchone()
            audit(conn, user["id"], "BULK_UPDATE_STATUS", "Registration", rid, dict(old), dict(new))
            updated += 1
        conn.commit()
        return {"updated": updated, "selection_status": payload.selection_status}


@app.get("/api/admin/ai-approval-proposal")
def ai_approval_proposal(user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        proposal = build_ai_approval_proposal(conn)
        return proposal


@app.post("/api/admin/ai-approval-proposal/approve")
def approve_ai_approval_proposal(payload: AiApprovalApply, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    if not payload.ids:
        raise HTTPException(status_code=400, detail="AI proposal does not contain any records to approve.")
    unique_ids = sorted(set(payload.ids))
    with connect() as conn:
        valid_rows = conn.execute(
            f"SELECT * FROM screening_registrations WHERE id IN ({','.join(['?'] * len(unique_ids))}) AND selection_status IN ('Registered', 'Waitlisted', 'Shortlisted')",
            unique_ids,
        ).fetchall()
        valid_ids = [row["id"] for row in valid_rows]
        if not valid_ids:
            raise HTTPException(status_code=400, detail="No eligible records found to approve from this proposal.")
        ts = now_iso()
        updated = 0
        for old in valid_rows:
            conn.execute(
                "UPDATE screening_registrations SET selection_status = 'Approved', admin_remarks = ?, updated_at = ?, updated_by = ? WHERE id = ?",
                ("Approved from AI-assisted audience mix proposal", ts, user["id"], old["id"]),
            )
            new = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (old["id"],)).fetchone()
            audit(conn, user["id"], "AI_APPROVE", "Registration", old["id"], dict(old), dict(new))
            updated += 1
        conn.commit()
        return {"updated": updated, "selection_status": "Approved", "approved_ids": valid_ids}


@app.delete("/api/admin/registrations/{registration_id}")
def delete_registration(registration_id: int, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, str]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_registrations WHERE id = ?", (registration_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Registration not found")
        conn.execute("DELETE FROM screening_registrations WHERE id = ?", (registration_id,))
        audit(conn, user["id"], "DELETE", "Registration", registration_id, dict(old), None)
        conn.commit()
    return {"message": "Deleted"}


@app.get("/api/admin/screening-details")
def list_screening_details(search: str = "", film_language: str = "", genre: str = "", user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    sql = "SELECT * FROM screening_details WHERE 1=1"
    params: list[Any] = []
    if search:
        sql += " AND (film_title LIKE ? OR director LIKE ? OR producer LIKE ? OR venue_name LIKE ? OR venue_city LIKE ? OR remarks LIKE ?)"
        term = f"%{search}%"; params.extend([term, term, term, term, term, term])
    if film_language:
        sql += " AND film_language = ?"; params.append(film_language)
    if genre:
        sql += " AND genre = ?"; params.append(genre)
    sql += " ORDER BY datetime(updated_at) DESC, id DESC"
    with connect() as conn:
        return {"items": [add_poster_urls(dict(r)) for r in conn.execute(sql, params).fetchall()]}


@app.post("/api/admin/screening-details", status_code=201)
def create_screening_details(payload: ScreeningDetailsPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    ts = now_iso()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO screening_details(
                film_title, film_language, genre, duration_minutes, director, producer, synopsis, screening_date, screening_time, venue_name, venue_city,
                expected_audience_count, actual_audience_count, audience_age_mix, audience_language_mix, audience_social_mix, audience_occupation_mix, remarks, created_at, updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.film_title, payload.film_language, payload.genre, payload.duration_minutes, payload.director or "", payload.producer or "", payload.synopsis or "", payload.screening_date or "", payload.screening_time or "", payload.venue_name or "", payload.venue_city or "", payload.expected_audience_count or 0, payload.actual_audience_count or 0, payload.audience_age_mix or "", payload.audience_language_mix or "", payload.audience_social_mix or "", payload.audience_occupation_mix or "", payload.remarks or "", ts, ts, user["id"]),
        )
        row = conn.execute("SELECT * FROM screening_details WHERE id = ?", (cur.lastrowid,)).fetchone()
        audit(conn, user["id"], "CREATE", "Film & Audience Details", cur.lastrowid, None, dict(row))
        conn.commit()
        return add_poster_urls(dict(row))


@app.put("/api/admin/screening-details/{screening_id}")
def update_screening_details(screening_id: int, payload: ScreeningDetailsPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_details WHERE id = ?", (screening_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Screening details not found")
        ts = now_iso()
        conn.execute(
            """
            UPDATE screening_details SET film_title=?, film_language=?, genre=?, duration_minutes=?, director=?, producer=?, synopsis=?, screening_date=?, screening_time=?, venue_name=?, venue_city=?, expected_audience_count=?, actual_audience_count=?, audience_age_mix=?, audience_language_mix=?, audience_social_mix=?, audience_occupation_mix=?, remarks=?, updated_at=?, updated_by=? WHERE id=?
            """,
            (payload.film_title, payload.film_language, payload.genre, payload.duration_minutes, payload.director or "", payload.producer or "", payload.synopsis or "", payload.screening_date or "", payload.screening_time or "", payload.venue_name or "", payload.venue_city or "", payload.expected_audience_count or 0, payload.actual_audience_count or 0, payload.audience_age_mix or "", payload.audience_language_mix or "", payload.audience_social_mix or "", payload.audience_occupation_mix or "", payload.remarks or "", ts, user["id"], screening_id),
        )
        new = conn.execute("SELECT * FROM screening_details WHERE id = ?", (screening_id,)).fetchone()
        audit(conn, user["id"], "UPDATE", "Film & Audience Details", screening_id, dict(old), dict(new))
        conn.commit()
        return add_poster_urls(dict(new))


@app.post("/api/admin/screening-details/{screening_id}/poster")
def upload_screening_poster(screening_id: int, poster: UploadFile = File(...), user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if poster.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP poster files are allowed")
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_details WHERE id = ?", (screening_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Screening details not found")
        ext = allowed[poster.content_type]
        filename = f"poster_{screening_id}_{secrets.token_hex(8)}{ext}"
        target = UPLOAD_DIR / filename
        with target.open("wb") as f:
            shutil.copyfileobj(poster.file, f)
        ts = now_iso()
        conn.execute("UPDATE screening_details SET poster_path = ?, updated_at = ?, updated_by = ? WHERE id = ?", (filename, ts, user["id"], screening_id))
        new = conn.execute("SELECT * FROM screening_details WHERE id = ?", (screening_id,)).fetchone()
        audit(conn, user["id"], "UPLOAD_POSTER", "Film & Audience Details", screening_id, old["poster_path"] if "poster_path" in old.keys() else None, filename)
        conn.commit()
        return add_poster_urls(dict(new))


@app.get("/api/admin/screening-details/export.csv")
def export_screening_details_csv(user: dict[str, Any] = Depends(get_current_user)) -> StreamingResponse:
    headers = ["Film Title", "Language", "Genre", "Duration", "Director", "Producer", "Synopsis", "Screening Date", "Screening Time", "Venue", "City", "Expected", "Actual", "Age Mix", "Language Mix", "Social Mix", "Occupation Mix", "Remarks", "Poster", "Created At", "Updated At"]
    with connect() as conn:
        rows = conn.execute("SELECT * FROM screening_details ORDER BY datetime(created_at) DESC, id DESC").fetchall()
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(headers)
    for r in rows:
        writer.writerow([r["film_title"], r["film_language"], r["genre"], r["duration_minutes"], r["director"], r["producer"], r["synopsis"], r["screening_date"], r["screening_time"], r["venue_name"], r["venue_city"], r["expected_audience_count"], r["actual_audience_count"], r["audience_age_mix"], r["audience_language_mix"], r["audience_social_mix"], r["audience_occupation_mix"], r["remarks"], poster_url(r["poster_path"]), r["created_at"], r["updated_at"]])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=screening_details_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.csv"})


@app.delete("/api/admin/screening-details/{screening_id}")
def delete_screening_details(screening_id: int, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, str]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM screening_details WHERE id = ?", (screening_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Screening details not found")
        conn.execute("DELETE FROM screening_details WHERE id = ?", (screening_id,))
        audit(conn, user["id"], "DELETE", "Film & Audience Details", screening_id, dict(old), None)
        conn.commit()
    return {"message": "Deleted"}


@app.get("/api/admin/survey-builder")
def get_admin_survey_builder(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        return survey_builder_payload(conn, active_only=False)


@app.post("/api/admin/survey-sections", status_code=201)
def create_survey_section(payload: SurveySectionPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    ts = now_iso()
    key = (payload.section_key or payload.title.lower().replace(" ", "_")).strip().replace("-", "_")[:80] or f"section_{secrets.token_hex(4)}"
    with connect() as conn:
        try:
            cur = conn.execute("INSERT INTO survey_sections(section_key, title, description, display_order, is_active, created_at, updated_at, updated_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (key, payload.title.strip(), payload.description or "", payload.display_order, 1 if payload.is_active else 0, ts, ts, user["id"]))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Section key already exists. Use a different key or title.")
        audit(conn, user["id"], "CREATE", "Survey Section", cur.lastrowid, None, payload.model_dump())
        conn.commit()
        return {"id": cur.lastrowid, "message": "Survey section created"}


@app.put("/api/admin/survey-sections/{section_id}")
def update_survey_section(section_id: int, payload: SurveySectionPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    ts = now_iso()
    with connect() as conn:
        old = conn.execute("SELECT * FROM survey_sections WHERE id = ?", (section_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Survey section not found")
        key = (payload.section_key or old["section_key"]).strip()[:80]
        conn.execute("UPDATE survey_sections SET section_key=?, title=?, description=?, display_order=?, is_active=?, updated_at=?, updated_by=? WHERE id=?", (key, payload.title.strip(), payload.description or "", payload.display_order, 1 if payload.is_active else 0, ts, user["id"], section_id))
        audit(conn, user["id"], "UPDATE", "Survey Section", section_id, dict(old), payload.model_dump())
        conn.commit()
        return {"message": "Survey section updated"}


@app.post("/api/admin/survey-questions", status_code=201)
def create_survey_question(payload: SurveyQuestionPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    ts = now_iso()
    clean_options = [str(x).strip() for x in payload.options if str(x).strip()]
    if payload.question_type == "multiple_choice" and not clean_options:
        raise HTTPException(status_code=400, detail="Multiple choice questions need at least one option")
    with connect() as conn:
        if not conn.execute("SELECT id FROM survey_sections WHERE id = ?", (payload.section_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Survey section not found")
        cur = conn.execute("INSERT INTO survey_questions(section_id, question_text, question_type, options_json, is_required, display_order, is_active, created_at, updated_at, updated_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (payload.section_id, payload.question_text.strip(), payload.question_type, json.dumps(clean_options), 1 if payload.is_required else 0, payload.display_order, 1 if payload.is_active else 0, ts, ts, user["id"]))
        audit(conn, user["id"], "CREATE", "Survey Question", cur.lastrowid, None, payload.model_dump())
        conn.commit()
        return {"id": cur.lastrowid, "message": "Survey question created"}


@app.put("/api/admin/survey-questions/{question_id}")
def update_survey_question(question_id: int, payload: SurveyQuestionPayload, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    ts = now_iso()
    clean_options = [str(x).strip() for x in payload.options if str(x).strip()]
    if payload.question_type == "multiple_choice" and not clean_options:
        raise HTTPException(status_code=400, detail="Multiple choice questions need at least one option")
    with connect() as conn:
        old = conn.execute("SELECT * FROM survey_questions WHERE id = ?", (question_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Survey question not found")
        conn.execute("UPDATE survey_questions SET section_id=?, question_text=?, question_type=?, options_json=?, is_required=?, display_order=?, is_active=?, updated_at=?, updated_by=? WHERE id=?", (payload.section_id, payload.question_text.strip(), payload.question_type, json.dumps(clean_options), 1 if payload.is_required else 0, payload.display_order, 1 if payload.is_active else 0, ts, user["id"], question_id))
        audit(conn, user["id"], "UPDATE", "Survey Question", question_id, dict(old), payload.model_dump())
        conn.commit()
        return {"message": "Survey question updated"}


@app.delete("/api/admin/survey-questions/{question_id}")
def hide_survey_question(question_id: int, user: dict[str, Any] = Depends(require_roles("Super Admin", "Admin"))) -> dict[str, Any]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM survey_questions WHERE id = ?", (question_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Survey question not found")
        conn.execute("UPDATE survey_questions SET is_active = 0, updated_at = ?, updated_by = ? WHERE id = ?", (now_iso(), user["id"], question_id))
        audit(conn, user["id"], "HIDE", "Survey Question", question_id, dict(old), None)
        conn.commit()
        return {"message": "Survey question hidden"}


@app.get("/api/admin/registration-analytics")
def registration_analytics(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM screening_registrations").fetchone()["count"]
        latest_screening = conn.execute("SELECT expected_audience_count, actual_audience_count FROM screening_details ORDER BY datetime(updated_at) DESC, id DESC LIMIT 1").fetchone()
        expected_capacity = int(latest_screening["expected_audience_count"] or SHORTLIST_LIMIT) if latest_screening else SHORTLIST_LIMIT
        actual_audience = int(latest_screening["actual_audience_count"] or 0) if latest_screening else 0
        status_counts = [dict(r) for r in conn.execute("SELECT selection_status AS label, COUNT(*) AS value FROM screening_registrations GROUP BY selection_status ORDER BY value DESC").fetchall()]
        status_map = {r["label"]: r["value"] for r in status_counts}
        approved_like = sum(status_map.get(x, 0) for x in ["Approved", "Shortlisted", "Attended"])
        waitlisted = status_map.get("Waitlisted", 0)
        rejected = status_map.get("Rejected", 0)
        demographics = {
            "age_group": [dict(r) for r in conn.execute("SELECT age_group AS label, COUNT(*) AS value FROM screening_registrations GROUP BY age_group ORDER BY value DESC, label").fetchall()],
            "social_background": [dict(r) for r in conn.execute("SELECT social_background AS label, COUNT(*) AS value FROM screening_registrations GROUP BY social_background ORDER BY value DESC, label").fetchall()],
            "primary_language": [dict(r) for r in conn.execute("SELECT primary_language AS label, COUNT(*) AS value FROM screening_registrations GROUP BY primary_language ORDER BY value DESC, label").fetchall()],
            "selection_status": status_counts,
        }
        daily = [dict(r) for r in conn.execute("SELECT substr(created_at, 1, 10) AS label, COUNT(*) AS value FROM screening_registrations GROUP BY substr(created_at, 1, 10) ORDER BY label").fetchall()]
        consent_feedback_join = conn.execute("SELECT COUNT(DISTINCT sr.id) AS count FROM screening_registrations sr JOIN survey_responses sv ON sv.registration_id = sr.id").fetchone()["count"]
        insights = []
        if total == 0:
            insights.append("No registrations yet. Share the landing page link and enable the Registration button.")
        else:
            fill_rate = round((approved_like / expected_capacity) * 100, 1) if expected_capacity else 0
            insights.append(f"Approval fill rate is {fill_rate}% against the expected audience capacity of {expected_capacity}.")
            if approved_like < expected_capacity:
                insights.append(f"You can still approve around {max(expected_capacity - approved_like, 0)} more people to reach the target audience size.")
            if waitlisted > 0:
                insights.append(f"There are {waitlisted} waitlisted registrations available as backup for dropouts.")
            if rejected > approved_like and approved_like < expected_capacity:
                insights.append("More records are rejected than approved while seats remain. Review rejected records before closing registrations.")
            if consent_feedback_join:
                insights.append(f"{consent_feedback_join} registered audience members have submitted feedback so far.")
        return {
            "total": total,
            "expected_capacity": expected_capacity,
            "actual_audience": actual_audience,
            "approved_like": approved_like,
            "waitlisted": waitlisted,
            "rejected": rejected,
            "status_counts": status_counts,
            "demographics": demographics,
            "daily_registrations": daily,
            "feedback_from_registered": consent_feedback_join,
            "ai_insights": insights,
        }


@app.get("/api/admin/survey-analytics")
def survey_analytics(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        reg_total = conn.execute("SELECT COUNT(*) AS count FROM screening_registrations").fetchone()["count"]
        fb_total = conn.execute("SELECT COUNT(*) AS count FROM survey_responses").fetchone()["count"]
        avgs = {}
        for field in ["overall_rating", "story_rating", "acting_rating", "music_rating", "pace_rating", "emotional_impact_rating", "visual_quality_rating", "dialogue_rating", "length_rating"]:
            avgs[field] = round(conn.execute(f"SELECT AVG({field}) AS value FROM survey_responses").fetchone()["value"] or 0, 2)
        demographics = {
            "age_group": [dict(r) for r in conn.execute("SELECT age_group AS label, COUNT(*) AS value FROM screening_registrations GROUP BY age_group ORDER BY value DESC").fetchall()],
            "social_background": [dict(r) for r in conn.execute("SELECT social_background AS label, COUNT(*) AS value FROM screening_registrations GROUP BY social_background ORDER BY value DESC").fetchall()],
            "primary_language": [dict(r) for r in conn.execute("SELECT primary_language AS label, COUNT(*) AS value FROM screening_registrations GROUP BY primary_language ORDER BY value DESC").fetchall()],
        }
        mc = [dict(r) for r in conn.execute("""
            SELECT q.question_text, a.answer_text AS label, COUNT(*) AS value
            FROM survey_custom_answers a JOIN survey_questions q ON q.id = a.question_id
            WHERE q.question_type = 'multiple_choice'
            GROUP BY q.id, a.answer_text ORDER BY q.display_order, value DESC
        """).fetchall()]
        text_rows = [r[0] or "" for r in conn.execute("SELECT liked_most FROM survey_responses UNION ALL SELECT improvements FROM survey_responses UNION ALL SELECT remarks FROM survey_responses UNION ALL SELECT answer_text FROM survey_custom_answers").fetchall()]
        themes = {}
        keywords = ["slow", "length", "emotional", "camera", "grandfather", "grandson", "music", "ending", "confusing", "poster", "acting", "journey", "remove"]
        blob = " ".join(text_rows).lower()
        for k in keywords:
            count = blob.count(k)
            if count:
                themes[k] = count
        insights = []
        if avgs.get("pace_rating", 0) and avgs["pace_rating"] < 3.5:
            insights.append("Pace/editing needs review. Check slow-parts and remove/shorten responses before final cut decisions.")
        if themes.get("confusing"):
            insights.append("Some viewers may have clarity issues. Review confusing-part comments for story communication.")
        if avgs.get("emotional_impact_rating", 0) >= 4:
            insights.append("Emotional impact appears strong; use this as a positioning strength.")
        if not insights:
            insights.append("Feedback volume is still building. Use test data or collect more responses for stronger insights.")
        return {"registration_total": reg_total, "feedback_total": fb_total, "average_ratings": avgs, "demographics": demographics, "multiple_choice_distribution": mc, "themes": themes, "ai_insights": insights}


@app.get("/api/admin/surveys")
def list_surveys(search: str = "", would_recommend: str = "", user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    sql = "SELECT * FROM survey_responses WHERE 1=1"
    params: list[Any] = []
    if search:
        sql += " AND (name LIKE ? OR phone_number LIKE ? OR liked_most LIKE ? OR improvements LIKE ? OR memorable_scene LIKE ? OR one_word_reaction LIKE ? OR audience_type LIKE ? OR remarks LIKE ?)"
        term = f"%{search}%"; params.extend([term, term, term, term, term, term, term, term])
    if would_recommend:
        sql += " AND would_recommend = ?"; params.append(would_recommend)
    sql += " ORDER BY datetime(created_at) DESC, id DESC"
    with connect() as conn:
        return {"items": [dict(r) for r in conn.execute(sql, params).fetchall()]}


@app.get("/api/admin/surveys/export.csv")
def export_surveys_csv(user: dict[str, Any] = Depends(get_current_user)) -> StreamingResponse:
    headers = ["Name", "Phone", "Overall", "Story", "Acting", "Music", "Pace", "Emotional Impact", "Visual Quality", "Dialogue", "Length", "Understood Story", "Connected With Characters", "Preferred Audience", "Theatre or OTT", "One Word Reaction", "Audience Type", "Consent Quote", "Liked Most", "Improvements", "Memorable Scene", "Would Recommend", "Contact Permission", "Remarks", "Created At"]
    with connect() as conn:
        rows = conn.execute("SELECT * FROM survey_responses ORDER BY datetime(created_at) DESC, id DESC").fetchall()
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(headers)
    for r in rows:
        writer.writerow([r["name"], r["phone_number"], r["overall_rating"], r["story_rating"], r["acting_rating"], r["music_rating"], r["pace_rating"], r["emotional_impact_rating"], r["visual_quality_rating"], r["dialogue_rating"], r["length_rating"], r["understood_story"], r["connected_with_characters"], r["preferred_audience"], r["theatre_or_ott"], r["one_word_reaction"], r["audience_type"], r["consent_quote"], r["liked_most"], r["improvements"], r["memorable_scene"], r["would_recommend"], r["contact_permission"], r["remarks"], r["created_at"]])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=survey_responses_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.csv"})


@app.get("/api/admin/app-config")
def get_app_config(user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        cfg = get_config(conn)
        return {
            "registration_success_message": cfg.get("registration_success_message", ""),
            "registration_waitlist_message": cfg.get("registration_waitlist_message", ""),
            "waitlist_threshold": int(cfg.get("waitlist_threshold", "40") or 40),
        }


@app.put("/api/admin/app-config")
def update_app_config(payload: AppConfigUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    ts = now_iso()
    with connect() as conn:
        old = get_config(conn)
        values = {
            "registration_success_message": payload.registration_success_message,
            "registration_waitlist_message": payload.registration_waitlist_message,
            "waitlist_threshold": str(payload.waitlist_threshold),
        }
        for key, value in values.items():
            conn.execute("INSERT INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?) ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value, updated_at=excluded.updated_at", (key, value, ts))
        audit(conn, user["id"], "UPDATE", "Workflow Settings", None, old, values)
        conn.commit()
        return {"message": "Workflow settings updated", **values, "waitlist_threshold": payload.waitlist_threshold}


@app.get("/api/admin/landing-buttons")
def get_landing_buttons(user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        config = get_config(conn)
        return landing_button_settings_from_config(config)


@app.put("/api/admin/landing-buttons")
def update_landing_buttons(payload: LandingButtonSettingsUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    ts = now_iso()
    with connect() as conn:
        old = landing_button_settings_from_config(get_config(conn))
        values = {
            "landing_show_registration_button": "1" if payload.show_registration_button else "0",
            "landing_show_survey_button": "1" if payload.show_survey_button else "0",
            "landing_show_feedback_qr_button": "1" if payload.show_feedback_qr_button else "0",
        }
        for key, value in values.items():
            conn.execute(
                "INSERT INTO app_config(config_key, config_value, updated_at) VALUES (?, ?, ?) ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value, updated_at=excluded.updated_at",
                (key, value, ts),
            )
        new = {
            "show_registration_button": payload.show_registration_button,
            "show_survey_button": payload.show_survey_button,
            "show_feedback_qr_button": payload.show_feedback_qr_button,
        }
        audit(conn, user["id"], "UPDATE", "Landing Button Settings", None, old, new)
        conn.commit()
        return new


@app.get("/api/admin/page-settings")
def get_page_settings(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM page_settings ORDER BY page_type, display_order, page_key").fetchall()
        return {"items": [dict(r) for r in rows]}


@app.put("/api/admin/page-settings")
def update_page_settings(payload: PageSettingsUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    ts = now_iso()
    with connect() as conn:
        old = [dict(r) for r in conn.execute("SELECT * FROM page_settings ORDER BY page_type, display_order").fetchall()]
        valid_keys = {r["page_key"] for r in conn.execute("SELECT page_key FROM page_settings").fetchall()}
        for item in payload.items:
            key = str(item.get("page_key", ""))
            if key not in valid_keys:
                continue
            label = str(item.get("page_label", "")).strip()[:80] or key
            visible = 1 if bool(item.get("is_visible", True)) else 0
            try:
                order = int(item.get("display_order", 1))
            except ValueError:
                order = 1
            conn.execute("UPDATE page_settings SET page_label=?, is_visible=?, display_order=?, updated_at=? WHERE page_key=?", (label, visible, order, ts, key))
        new = [dict(r) for r in conn.execute("SELECT * FROM page_settings ORDER BY page_type, display_order").fetchall()]
        audit(conn, user["id"], "UPDATE", "Landing Button Settings", None, old, new)
        conn.commit()
        return {"items": new}


@app.get("/api/admin/users")
def list_users(user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT id, full_name, username, phone_number, role, is_active, last_login_at, created_at, updated_at FROM admin_users ORDER BY id").fetchall()
        return {"items": [dict(r) for r in rows]}


@app.post("/api/admin/users", status_code=201)
def create_user(payload: AdminUserCreate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    ts = now_iso()
    try:
        with connect() as conn:
            cur = conn.execute("INSERT INTO admin_users(full_name, username, phone_number, password_hash, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?)", (payload.full_name, payload.username, payload.phone_number or "", hash_password(payload.password), payload.role, ts, ts))
            new = conn.execute("SELECT id, full_name, username, phone_number, role, is_active, created_at, updated_at FROM admin_users WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user["id"], "CREATE", "User Management", cur.lastrowid, None, dict(new))
            conn.commit()
            return dict(new)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")


@app.put("/api/admin/users/{admin_user_id}")
def update_user(admin_user_id: int, payload: AdminUserUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="User not found")
        ts = now_iso()
        conn.execute("UPDATE admin_users SET full_name=?, phone_number=?, role=?, updated_at=? WHERE id=?", (payload.full_name, payload.phone_number or "", payload.role, ts, admin_user_id))
        new = conn.execute("SELECT id, full_name, username, phone_number, role, is_active, created_at, updated_at FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        audit(conn, user["id"], "UPDATE", "User Management", admin_user_id, dict(old), dict(new))
        conn.commit()
        return dict(new)


@app.put("/api/admin/users/{admin_user_id}/reset-password")
def reset_password(admin_user_id: int, payload: PasswordReset, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, str]:
    with connect() as conn:
        old = conn.execute("SELECT * FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="User not found")
        ts = now_iso()
        conn.execute("UPDATE admin_users SET password_hash=?, updated_at=? WHERE id=?", (hash_password(payload.password), ts, admin_user_id))
        audit(conn, user["id"], "RESET_PASSWORD", "User Management", admin_user_id, None, "password changed")
        conn.commit()
        return {"message": "Password reset"}


@app.put("/api/admin/users/{admin_user_id}/status")
def set_user_active(admin_user_id: int, payload: ActiveUpdate, user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    if admin_user_id == user["id"] and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")
    with connect() as conn:
        old = conn.execute("SELECT * FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="User not found")
        ts = now_iso()
        conn.execute("UPDATE admin_users SET is_active=?, updated_at=? WHERE id=?", (1 if payload.is_active else 0, ts, admin_user_id))
        new = conn.execute("SELECT id, full_name, username, role, is_active FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        audit(conn, user["id"], "UPDATE_STATUS", "User Management", admin_user_id, dict(old), dict(new))
        conn.commit()
        return dict(new)


@app.get("/api/admin/audit-logs")
def audit_logs(user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT audit_logs.*, admin_users.username
            FROM audit_logs LEFT JOIN admin_users ON admin_users.id = audit_logs.user_id
            ORDER BY datetime(audit_logs.created_at) DESC, audit_logs.id DESC LIMIT 500
            """
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@app.post("/api/admin/test-data")
def create_test_data(count: int = Query(default=50, ge=1, le=500), user: dict[str, Any] = Depends(require_roles("Super Admin"))) -> dict[str, Any]:
    """Create reliable test data for both registration and feedback analytics.

    This version is safe for older local databases where survey_responses still
    has a strict foreign-key constraint. Generated feedback is analytics test
    data, so FK checks are temporarily disabled only during generated feedback
    insert/update operations.
    """
    ts = now_iso()
    registrations_created = 0
    registrations_updated = 0
    feedback_created = 0
    custom_answers_created = 0

    with connect() as conn:
        active_questions = [dict(r) for r in conn.execute(
            "SELECT * FROM survey_questions WHERE is_active = 1 ORDER BY display_order, id"
        ).fetchall()]

        test_phones = [f"90000{i:05d}"[-10:] for i in range(count)]

        # Clean old generated feedback first.
        if test_phones:
            placeholders = ",".join("?" for _ in test_phones)
            old_response_ids = [r["id"] for r in conn.execute(
                f"SELECT id FROM survey_responses WHERE phone_number IN ({placeholders})",
                test_phones,
            ).fetchall()]
            if old_response_ids:
                id_placeholders = ",".join("?" for _ in old_response_ids)
                conn.execute(f"DELETE FROM survey_custom_answers WHERE survey_response_id IN ({id_placeholders})", old_response_ids)
                conn.execute(f"DELETE FROM survey_responses WHERE id IN ({id_placeholders})", old_response_ids)
        conn.commit()

        # Create/update test registrations first with FK checks on.
        for i in range(count):
            phone = f"90000{i:05d}"[-10:]
            name = f"Test Audience {i+1}"
            age_group = AGE_GROUPS[i % len(AGE_GROUPS)]
            social_background = SOCIAL_BACKGROUNDS[i % len(SOCIAL_BACKGROUNDS)]
            primary_language = PRIMARY_LANGUAGES[i % len(PRIMARY_LANGUAGES)]
            status_value = ["Registered", "Approved", "Shortlisted", "Waitlisted", "Attended"][i % 5]

            row = conn.execute("SELECT id FROM screening_registrations WHERE phone_number = ?", (phone,)).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE screening_registrations
                    SET name=?, age_group=?, social_background=?, primary_language=?,
                        remarks=?, selection_status=?, updated_at=?
                    WHERE phone_number=?
                    """,
                    (name, age_group, social_background, primary_language, "Test data for analytics", status_value, ts, phone),
                )
                registrations_updated += 1
            else:
                conn.execute(
                    """
                    INSERT INTO screening_registrations(
                        name, age_group, social_background, primary_language, phone_number,
                        occupation, remarks, selection_status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, '', ?, ?, ?, ?)
                    """,
                    (name, age_group, social_background, primary_language, phone, "Test data for analytics", status_value, ts, ts),
                )
                registrations_created += 1

        conn.commit()

        # Older local DBs may still have old FK constraints on survey_responses.
        # Turn off FK checks for generated feedback rows only.
        conn.execute("PRAGMA foreign_keys = OFF")

        for i in range(count):
            phone = f"90000{i:05d}"[-10:]
            name = f"Test Audience {i+1}"
            reg = conn.execute("SELECT id FROM screening_registrations WHERE phone_number = ?", (phone,)).fetchone()
            reg_id = reg["id"] if reg else 0

            common = {
                "overall": min(5, 3 + (i % 3)),
                "story": min(5, 3 + ((i + 1) % 3)),
                "acting": min(5, 3 + ((i + 2) % 3)),
                "music": min(5, 3 + ((i + 3) % 3)),
                "pace": min(5, 2 + (i % 4)),
                "emotional": min(5, 3 + ((i + 1) % 3)),
                "visual": min(5, 3 + ((i + 2) % 3)),
                "dialogue": min(5, 3 + ((i + 3) % 3)),
                "length": min(5, 2 + ((i + 1) % 4)),
                "understood": ["Yes", "Mostly", "Somewhat"][i % 3],
                "connected": ["Strongly", "Somewhat", "Not much"][i % 3],
                "audience": ["Family audience", "Kannada cinema lovers", "Festival audience", "General audience"][i % 4],
                "ott": ["Theatre", "OTT", "Both"][i % 3],
                "reaction": ["Emotional", "Nostalgic", "Warm", "Slow", "Beautiful"][i % 5],
                "audience_type": ["General Audience", "Family Audience", "Film / Media Background", "Kannada Cinema Audience"][i % 4],
                "quote": ["Yes", "No"][i % 2],
                "liked": ["Grandfather and grandson bonding worked well.", "The antique camera portions were memorable.", "The emotional scenes were strong.", "The Mysore to Jaipur journey had warmth."][i % 4],
                "improve": ["Some travel portions felt slow and can be tightened.", "A few scenes can be shortened before the second half.", "The ending can be made clearer.", "The camera sale decision needs stronger emotional build-up."][i % 4],
                "scene": ["The grandfather picking up the camera again.", "The boy holding the vintage camera.", "The journey moment between Mysore and Jaipur.", "The emotional family scene."][i % 4],
                "recommend": ["Yes", "Maybe", "No"][i % 3],
                "contact": ["Yes", "No"][i % 2],
                "remarks": "Test feedback themes: slow pace, emotional bonding, camera, ending, journey, family.",
            }

            cur = conn.execute(
                """
                INSERT INTO survey_responses(
                    registration_id, name, phone_number, overall_rating, story_rating, acting_rating,
                    music_rating, pace_rating, emotional_impact_rating, visual_quality_rating,
                    dialogue_rating, length_rating, understood_story, connected_with_characters,
                    preferred_audience, theatre_or_ott, one_word_reaction, audience_type, consent_quote,
                    liked_most, improvements, memorable_scene, would_recommend, contact_permission,
                    remarks, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reg_id, name, phone, common["overall"], common["story"], common["acting"], common["music"], common["pace"],
                    common["emotional"], common["visual"], common["dialogue"], common["length"], common["understood"],
                    common["connected"], common["audience"], common["ott"], common["reaction"], common["audience_type"],
                    common["quote"], common["liked"], common["improve"], common["scene"], common["recommend"],
                    common["contact"], common["remarks"], ts, ts
                ),
            )
            response_id = cur.lastrowid
            feedback_created += 1

            for q in active_questions:
                try:
                    opts = json.loads(q.get("options_json") or "[]")
                except Exception:
                    opts = []
                ans = opts[i % len(opts)] if q["question_type"] == "multiple_choice" and opts else [
                    "High point: emotional bond between grandfather and grandson.",
                    "Low point: some middle portions felt slow.",
                    "Remove or shorten a few travel beats.",
                    "Poster created curiosity about the vintage camera."
                ][i % 4]
                conn.execute(
                    "INSERT INTO survey_custom_answers(survey_response_id, question_id, answer_text, created_at) VALUES (?, ?, ?, ?)",
                    (response_id, q["id"], ans, ts),
                )
                custom_answers_created += 1

        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")

        audit(conn, user["id"], "CREATE_TEST_DATA", "Registration/Feedback", None, None,
              f"registrations_created={registrations_created}; registrations_updated={registrations_updated}; feedback_created={feedback_created}; custom_answers={custom_answers_created}")
        conn.commit()

    return {
        "registrations_created": registrations_created,
        "registrations_updated": registrations_updated,
        "feedback_created": feedback_created,
        "custom_answers_created": custom_answers_created,
        "message": "Test registration and feedback analytics data created successfully."
    }




# Railway / production single-service frontend hosting
# In Railway, the React build is expected at frontend/dist. The backend serves
# the built SPA at "/" and keeps all /api routes handled above.
DEFAULT_STATIC_DIR = BASE_DIR.parent / "frontend" / "dist"
STATIC_DIR = Path(os.getenv("STATIC_DIR", str(DEFAULT_STATIC_DIR)))

@app.get("/", include_in_schema=False)
def production_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "backend_running",
        "message": "Frontend build not found. Run npm install && npm run build in frontend, or set STATIC_DIR to the built frontend/dist folder.",
        "api_health": "/api/health"
    }

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    # Serve common static files in frontend/dist root when available.
    for static_name in ["vite.svg", "favicon.ico", "payana_feedback_qr.png", "default_poster.png"]:
        static_file = STATIC_DIR / static_name
        if static_file.exists():
            @app.get(f"/{static_name}", include_in_schema=False)
            def serve_static_file(static_name: str = static_name):
                return FileResponse(STATIC_DIR / static_name)

@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa_fallback(full_path: str):
    # Never swallow API requests. Let FastAPI return normal API 404 for /api/*.
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    requested = STATIC_DIR / full_path
    if STATIC_DIR.exists() and requested.exists() and requested.is_file():
        return FileResponse(requested)
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "backend_running",
        "message": "Frontend build not found. Build frontend before deployment or check Railway build command.",
        "api_health": "/api/health"
    }

