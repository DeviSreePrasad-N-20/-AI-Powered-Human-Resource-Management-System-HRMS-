# Deployment Guide

This project is ready to deploy, but there are a few things to prepare first because the backend currently stores:

- the database in SQLite
- uploaded files on local disk

That means your backend host must support persistent storage, or you must provide your own `DATABASE_URL` and `UPLOADS_DIR`.

## Best Option For Tomorrow

Use this setup if you want the simplest deployment path:

- Frontend: any static host
- Backend: any Python host with a persistent disk
- Database: SQLite on that persistent disk
- Uploads: saved on that persistent disk

## Pre-Deployment Checklist

Do these before you deploy:

1. Rotate the OpenAI key you pasted in chat and create a fresh one.
2. Confirm the OpenAI project has active billing or quota.
3. Decide your backend URL.
4. Decide your frontend URL.
5. Choose where backend data should persist.
6. Test the app locally one last time.

## Backend Environment Variables

Set these on the backend host:

```env
OPENAI_API_KEY=your_real_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=low
OPENAI_TIMEOUT_SECONDS=45
HR_CONTACT_EMAIL=hr@yourcompany.com
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
DATA_DIR=/absolute/persistent/path/data
UPLOADS_DIR=/absolute/persistent/path/uploads
```

Optional:

```env
DATABASE_URL=sqlite:////absolute/persistent/path/data/hrms.db
```

Notes:

- If `DATABASE_URL` is not set, the app automatically uses `DATA_DIR/hrms.db`.
- `BACKEND_CORS_ORIGINS` accepts a comma-separated list if you have more than one frontend URL.
- If your host gives you a mounted disk path, point `DATA_DIR` and `UPLOADS_DIR` there.

## Frontend Environment Variables

Set this on the frontend host when frontend and backend are on different domains:

```env
VITE_API_BASE=https://your-backend-domain.com
```

If you deploy behind one domain with a reverse proxy, you can leave `VITE_API_BASE` empty and use same-origin requests.

## Local Production Check

Run this before tomorrow:

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m compileall app
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

## What To Check After Backend Deploy

Open these in the browser:

- `/health`
- `/dashboard`
- `/analytics/monthly-summary`

Make sure:

- `/health` returns `"status": "ok"`
- `ai_provider` shows `"openai"` if your key has working quota
- uploaded files open correctly from `/uploads/...`

## What To Check After Frontend Deploy

Make sure these flows work:

1. Open each module page from the top buttons.
2. Create an employee.
3. Create a job.
4. Upload a candidate resume.
5. Submit a leave request.
6. Save a performance review.
7. Upload a policy document and ask a question.

## Important Production Notes

- If your OpenAI key has no quota, the app still works, but it will fall back to local AI logic.
- If your backend host has no persistent disk, uploaded files and database records may disappear after restart.
- Authentication is not implemented yet, so do not expose this app for public signup or public internet use without protection.
- For a real company deployment later, move from SQLite and local uploads to managed database and object storage.
