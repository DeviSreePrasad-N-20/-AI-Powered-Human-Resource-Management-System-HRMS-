# AI-Powered Human Resource Management System (HRMS)

This project implements the PDF brief for an AI-powered HRMS with six integrated modules:

1. Employee Records & Directory
2. Recruitment & ATS
3. Leave & Attendance
4. Performance Reviews
5. Onboarding Assistant
6. HR Analytics & Insights

The app is designed as a full-stack monorepo with a FastAPI backend, SQLite persistence, and a React + Vite frontend. It ships with seeded demo data so the workflows are visible immediately after startup.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React 19, TypeScript, Vite
- AI features: OpenAI-backed Responses API integration with a local fallback mode
- File handling: `python-multipart`, `pypdf`
- PDF export: ReportLab

## Features

### Module 1: Employee Records & Directory

- Add employees with department, manager, contact, skills, and profile details
- Auto-generate a professional employee bio
- Flag incomplete or potentially duplicate employee profiles
- Search employees by name, department, role, or skills
- Upload employee documents
- Visual org chart
- Export employee directory as CSV

### Module 2: Recruitment & ATS

- Create job postings with JD, required skills, and experience level
- Upload candidate resumes
- AI resume match score with reasoning
- Top strengths and top gaps per candidate
- Five tailored interview questions per candidate
- Hiring pipeline stage updates
- Side-by-side candidate comparison

### Module 3: Leave & Attendance

- Apply for leave by type and date range
- Approve or reject leave requests
- Leave balance tracking by employee
- Attendance marking for Present, WFH, Half Day, or Absent
- Monthly attendance summary
- Team leave calendar
- AI unusual leave pattern detection
- AI capacity risk hinting for overlapping leave

### Module 4: Performance Reviews

- Create review cycles
- Employee self-assessment form
- Manager review with five rating categories
- AI-generated review summary
- Mismatch detection between self-rating and manager rating
- Development action suggestions
- Export final review as PDF

### Module 5: AI Onboarding Assistant

- Create onboarding role checklists
- Assign personalized checklist to a joiner
- Track onboarding progress
- Upload policy or handbook documents
- Document-grounded onboarding assistant
- Fallback to HR contact if answer is not found in uploaded documents
- Most-asked question analytics

### Module 6: HR Analytics & Insights

- Headcount by department
- Attrition rate
- Average tenure by department
- Open vs filled positions
- Leave utilization rate
- AI-generated monthly HR summary with highlights, risks, and recommended actions

## Project Structure

```text
HRSH/
├─ backend/
│  ├─ app/
│  │  ├─ routers/
│  │  ├─ services/
│  │  ├─ database.py
│  │  ├─ main.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  └─ seed.py
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ types/
│  │  └─ utils/
│  └─ package.json
└─ README.md
```

## Setup Instructions

### 1. Backend

Create a `.env` file in the project root or `backend` folder:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=low
OPENAI_TIMEOUT_SECONDS=45
HR_CONTACT_EMAIL=hr@company.local
```

You can copy from `.env.example`.

Important:

- Do not place your real API key inside `README.md` or commit it to GitHub.
- Create your OpenAI key in your own OpenAI dashboard, then paste it only into `.env`.
- The backend reads `OPENAI_API_KEY` from `.env` automatically.

Then start the backend:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs on `http://127.0.0.1:8000`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://127.0.0.1:5173`.

## Deployment Prep

- Backend now supports `BACKEND_CORS_ORIGINS`, `DATA_DIR`, `UPLOADS_DIR`, and optional `DATABASE_URL`.
- Frontend now supports `VITE_API_BASE` through `frontend/.env.example`.
- A full deployment checklist is available in `DEPLOYMENT.md`.

## Demo Data

On first startup the backend seeds:

- sample employees and reporting hierarchy
- one open engineering job
- sample candidates with AI scoring
- leave balances and leave requests
- one active review cycle
- one onboarding role and policy document

## AI Design Notes

- If `OPENAI_API_KEY` is present, the backend uses OpenAI's Responses API for employee bios, resume scoring, interview questions, review summaries, grounded onboarding answers, and monthly HR summaries.
- If the key is missing or an OpenAI request fails, the backend falls back to the local heuristic AI layer so the app still works.
- The onboarding assistant remains document-grounded: it first retrieves relevant uploaded excerpts and only answers from that retrieved context.
- Seed data intentionally stays on the local fallback path to avoid API cost during first boot.
- Safe example backend key setup:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Known Limitations

- Authentication and role-based access control are not implemented.
- OpenAI usage is request-based and does not yet include prompt/version tracking or response caching beyond monthly summary memoization.
- Charts are rendered with lightweight UI patterns instead of a dedicated chart library.
- Files are stored locally; cloud storage and async background processing are not included.

## Suggested Demo Flow

1. Show the employee directory, search, org chart, and CSV export.
2. Create a job and upload a candidate resume to demonstrate AI scoring.
3. Submit and approve a leave request, then inspect capacity and pattern signals.
4. Submit self-assessment and manager review to generate the AI review summary and export PDF.
5. Upload a policy document and ask the onboarding assistant a grounded question.
6. End with the HR analytics panel and monthly summary.

## Screenshots / GIFs

The repository is ready for screenshots once both services are running. Good capture candidates are:

- dashboard overview
- employee directory plus org chart
- recruitment candidate scoring cards
- leave queue plus calendar
- performance review summary
- onboarding chatbot with grounded answer
