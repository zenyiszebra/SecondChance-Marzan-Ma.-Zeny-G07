# SecondChance: Breaking Beyond the Bars

A rehabilitation progress tracking system. Correctional staff record each inmate's progress
through six rehabilitation stages, and the system calculates a measurable Readiness Score for
release-preparation decisions.

**Phase 1 (this repo so far): Account Feature** built with full-stack Django and PostgreSQL.

## Tech stack
- Django 5.2 (backend and frontend through Django templates, Bootstrap 5 from a CDN)
- PostgreSQL (hosted on Supabase, or any local PostgreSQL). SQLite is not used.
- Pillow for profile photos, python-dotenv and dj-database-url for configuration

## Account Feature
| Part | Where |
|---|---|
| Registration (validation, unique username/email, password confirmation, hashed passwords) | `accounts/forms.py` `RegisterForm`, `accounts/views.py` `register_view` |
| Login / logout, invalid-credential error, protected pages | `UserLoginView`, `UserLogoutView`, `@login_required`, `role_required` |
| Role-based dashboards (Admin, Staff, Reviewer) | `accounts/views.py`, `accounts/decorators.py`, `accounts/templates/accounts/*_dashboard.html` |
| User profile (view and edit own profile, photo upload) | `profile_view`, `profile_edit`, `ProfileForm` |

**Roles.** Users register as *Staff* or *Reviewer*. *Admin* accounts are made with
`python manage.py createsuperuser`, which sets the Admin role automatically, so nobody can
register themselves as an admin. A user who opens another role's dashboard URL is sent back to
their own dashboard with an error message.

## Setup
```bash
git clone <your-repo-url>
cd <repo-folder>
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```
Edit `.env`: set `DJANGO_SECRET_KEY` and `DATABASE_URL`.

**Supabase:** create a project, click **Connect**, copy the **Session pooler** connection string,
paste it as `DATABASE_URL` and keep `?sslmode=require`. URL-encode special characters in the
password. For local PostgreSQL, use `postgresql://user:password@localhost:5432/secondchance`.

```bash
python manage.py makemigrations accounts
python manage.py migrate
python manage.py createsuperuser      # this account becomes the Admin
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Tests
```bash
python manage.py test accounts
```
Django creates a temporary `test_...` database, so the database user needs permission to create
databases (works with local PostgreSQL; if Supabase refuses, run the tests against local PostgreSQL).

## Pages
`/` home, `/register/`, `/login/`, `/logout/` (POST), `/dashboard/` (role redirect),
`/dashboard/admin/`, `/dashboard/staff/`, `/dashboard/reviewer/`, `/profile/`, `/profile/edit/`

## Secrets
`.env`, `venv/`, and `__pycache__/` are in `.gitignore`. Only `.env.example` is committed.
