# SecondChance: Breaking Beyond the Bars

A rehabilitation progress tracking system. Correctional staff record each inmate's progress
through six rehabilitation stages, and the system turns it into a measurable Readiness Score
for release-preparation decisions.

Built with full-stack Django (templates), PostgreSQL on Supabase, and Bootstrap 5.

## Core feature (Project Development 2): Rehabilitation Pipeline

The pipeline is the main thing SecondChance exists to do. It works end to end through the
database, the Django backend, and the templates.

**What users can do**
- **Inmate records:** add, view, search, edit, and delete inmate records (inmate number, name,
  date of birth, sentence dates, status, notes).
- **Six-stage pipeline:** for each inmate, record progress on Initial Assessment, Education,
  Skills Training, Counseling, Work Program, and Release Preparation (status, hours, completion
  date, remarks). Each inmate page shows the six stages and a completion progress bar.

**Validation and business rules**
- Inmate number must be unique. Date of birth must be in the past. Sentence end must be after
  sentence start.
- One record per stage per inmate. A completed stage needs a completion date that is not in the
  future and not before the sentence start. Only completed stages can have a completion date.
- Clear success and error messages on every form.

**Data and relationships (PostgreSQL / Supabase)**
- `Inmate.created_by` is a ForeignKey to the user who added the inmate.
- `ProgressRecord.inmate` is a ForeignKey to `Inmate`, and `ProgressRecord.recorded_by` is a
  ForeignKey to the user who recorded the stage.

**Roles**
| Role | Access |
|---|---|
| Staff | Create, view, edit, and delete only their own inmates and stage records |
| Admin | View and manage all inmates and stage records |
| Reviewer | Read-only access to all inmates and stage records |

Each role's dashboard shows the pipeline: staff see their own counts and recent inmates,
admins see system-wide totals, reviewers see a read-only summary.

## Standard features (Project Development 1)
Registration, login/logout, role-based dashboards, and user profile all still work.

## Setup
```bash
git clone <your-repo-url>
cd <repo-folder>
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```
Edit `.env`: set `DJANGO_SECRET_KEY` and `DATABASE_URL` (Supabase Session pooler string or a local
PostgreSQL URL).

```bash
python manage.py migrate
python manage.py createsuperuser      # becomes the Admin account
python manage.py runserver
```
Open http://127.0.0.1:8000/. Run the tests with `python manage.py test accounts pipeline`
(the database user needs permission to create a test database).

## Main pages
`/` home, `/register/`, `/login/`, `/dashboard/` (role redirect), `/profile/`,
`/pipeline/` (inmate list), `/pipeline/inmates/new/`, `/pipeline/inmates/<id>/`

## Secrets
`.env`, `venv/`, and `__pycache__/` are in `.gitignore`. Only `.env.example` is committed.
