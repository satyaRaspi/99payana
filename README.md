# Payana Screening Registration v1.2.40

Production-base update built from the v1.2.10/v1.2.11 line.

## What is included

- Public landing page with configurable landing buttons
- Public registration form
- Public post-screening survey form
- Fully configurable survey module
  - Build survey sections
  - Add multiple-choice questions
  - Add short-text questions
  - Mark questions required/optional
  - Hide questions without deleting past answers
- Honest criticism questionnaire seeded by default
  - Poster reaction
  - Highs and lows
  - Things not liked
  - Slow portions
  - What to remove/shorten
  - Confusing parts
  - Grandfather-grandson bonding
  - Antique camera journey
  - Recommendation intent
- Name, phone number, and consent to contact captured in survey
- Feedback analytics dashboard
  - Ratings averages
  - Demographic mix
  - Multiple-choice answer distribution
  - Simple AI-assisted insight summary
  - Repeated feedback theme counts
- Test data creation button
- Admin reports and CSV exports
- SQLite database
- Python FastAPI backend
- React/Vite frontend
- Railway-ready Dockerfile

## Default Super Admin

Username: `admin`  
Password: `admin123`

## Run locally

```bash
python3 start_dev.py
```

On Windows:

```bat
python start_dev.py
```

Open:

```text
http://localhost:5173
```

Backend health:

```text
http://localhost:8000/api/health
```

## Railway

Deploy from GitHub. The included Dockerfile builds the React frontend and serves it from FastAPI.

Health check path:

```text
/api/health
```


## v1.2.40 update

Added a dedicated Admin → Analytics page with two sections:

1. Registration Analytics — totals, status mix, age group mix, social background mix, language mix, daily trend, approval/capacity view, and AI-assisted registration notes.
2. Feedback Analytics — rating averages, demographic mix, multiple-choice distribution, repeated text themes, and AI-assisted feedback notes.

The Analytics page also includes Refresh and Create Test Data actions.


## v1.2.40 - Registration CSV Upload

Added Admin Registration CSV upload from the Registration Report page. Admin/Super Admin can upload a CSV, select a default status, download a sample CSV template, and see an import summary with inserted, updated, and error counts. Phone Number is used as the unique key for update/insert.


## v1.2.40 Update
- Added a landing page link/button to show the feedback QR code in a dialog.
- Dialog text: "scan this to provide feedback".
- QR code asset is bundled in the frontend public folder as `payana_feedback_qr.png`.
- QR visibility follows the existing Survey button visibility setting.


## v1.2.40 Update
- Feedback QR dialog now opens with a clean white background for better QR visibility and readability.

- Removed the visible Login/Admin Dashboard button from the landing page navigation.
- Admin login is now accessed directly at `/#login`.
- Existing `/#admin` links are redirected to `/#login` for backward compatibility.


## v1.2.40 Fix
- Fixed hidden admin login route. Open `/#login` directly to access the login page.
- Added hash route listener so manually changing the URL hash updates the screen without needing a refresh.
- Supports both `/#login` and legacy `/#admin`.


## v1.2.40
- Redesigned landing page with a minimal poster-first layout.
- Removed the top navigation band/frame from the landing page.
- Landing page now focuses on the uploaded poster with event details and action buttons below.


## v1.2.40
- Fixed backend startup issue from v1.2.22.
- Added independent landing-page checkbox for Feedback QR link.


## v1.2.40
- Added Download Feedback CSV option for survey responses.
- Added visual chart cards for Registration Analytics and Feedback Analytics.


## v1.2.40
- Fixed backend startup issue after feedback CSV export addition.
- Kept Download Feedback CSV and analytics visualisations.


## v1.2.40
- Fixed backend startup error caused by feedback CSV export endpoint dependency name.
- Feedback CSV export now uses the existing admin session dependency.


## v1.2.40
- Fixed feedback analytics test data generation.
- Create Test Data now creates or updates both registrations and survey responses.
- Re-running test data no longer silently skips feedback due to duplicate phone numbers.


## v1.2.40
- Fixed Create Test Data foreign-key failure for feedback analytics.
- Test data now re-reads registration IDs before inserting survey responses.
- Existing databases with stricter FK constraints are handled safely.


## v1.2.40
- Fixed feedback CSV export error caused by using db() instead of the app's connect() database helper.
- Feedback test data and analytics remain from v1.2.28.


## v1.2.40
- Fixed feedback test-data generation by committing registrations before creating feedback responses.
- Feedback form no longer validates phone number against registration or 10-digit format.
- Auto-creates a feedback reference registration when needed so feedback can save cleanly.
- Converted Audience Type, Right Audience, and One-word Reaction to dropdowns.


## v1.2.40
- Fixed feedback save flow.
- Removed remaining backend phone-number validation from feedback submission.
- Feedback now auto-creates a reference registration row when needed and updates existing feedback if the same reference is reused.


## v1.2.40
- Fixed Survey Builder page Failed to fetch issue.
- Restored missing survey_builder_payload backend helper used by public and admin survey builder endpoints.
- Survey Builder now safely handles empty or older local DB builder tables.


## v1.2.40
- Fixed feedback save and test-data creation with verified backend flow.
- Removed SurveyCreate validators that could reject feedback dropdown/default values.
- Test data now deletes previous generated feedback rows and recreates them reliably.


## v1.2.40
- Fixed feedback save and test-data creation by restoring the missing save_custom_survey_answers backend helper.
- Verified feedback submit, test data creation, survey analytics, and CSV export using FastAPI TestClient.


## v1.2.40
- Fixed feedback save failure caused by older local DB foreign-key constraints on survey_responses.
- Added startup migration to rebuild survey_responses without blocking FK dependency while preserving existing feedback rows.
- Feedback submit retries once after migration if an old FK constraint is encountered.


## v1.2.40
- Fixed Create Test Data FK failure on older local databases.
- Generated feedback rows are now inserted with FK checks temporarily disabled for test data only.
- Registration creation and analytics remain unchanged.


## v1.2.40
- Fixed Railway deployment root URL returning {"detail":"Not Found"}.
- Backend now serves the built React frontend at `/` and falls back to index.html for SPA routes.
- Added Dockerfile that builds frontend and serves it through FastAPI in one Railway service.
- Added Railway config using `/api/health` as health check.


## v1.2.40
- Changed Railway deployment from Dockerfile builder to Nixpacks to avoid deployment getting stuck at Docker npm install.
- Added explicit nixpacks.toml using Python 3.11 and Node 20.
- Removed Dockerfile from this build.
- Railway still builds frontend/dist and FastAPI serves it at `/`.


## v1.2.40
- Fixed Railway Docker build where vite was not found.
- Dockerfile now uses npm ci --include=dev and runs the local Vite binary from node_modules.
- Railway config explicitly uses Dockerfile builder.


## v1.2.40
- Railway Docker build no longer runs npm install or npm ci.
- Frontend is pre-built into frontend/dist and Dockerfile copies the built files directly.
- Dockerfile is Python-only for faster Railway deployment.
