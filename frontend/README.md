# Course Allocation: frontend

React + Vite single-page app for the FastAPI backend.

## Run it

You need [Node.js](https://nodejs.org) (the LTS version). Check with `node --version`.

1. Start the backend in one terminal (project root, venv active):
   `uvicorn app.main:app --reload`
2. In a second terminal:
   ```
   cd frontend
   npm install
   npm run dev
   ```
3. Open http://localhost:5173 and log in.

If the backend is not at http://localhost:8000, copy `.env.example` to `.env` and change `VITE_API_URL`.

## What each role sees

| Role | Pages |
|---|---|
| Faculty | My Profile, Teaching History, Preferences, My Allocations |
| Department Coordinator | Rankings, Preferences (approve/reject), Courses, Sections, Instructors, Semesters, Audit Log: can edit |
| Program Coordinator | The same pages except Audit Log, read-only |

The menu hides what a role can't use, but the real enforcement is in the backend, which refuses
the request even if someone types the address by hand.

## How the code is organised

```
src/
  main.jsx          starts the app
  App.jsx           the list of pages and who may open each
  api.js            the ONLY file that talks to the backend (adds the login token, turns errors into messages)
  auth.jsx          who is logged in (the /me response) + login/logout
  styles.css        colours and layout (design tokens at the top)
  components/
    ui.jsx          small reusable pieces: Table, Modal, Button, Pill, Notice, useLoad ...
    Layout.jsx      the sidebar + page frame
  pages/
    Login.jsx
    faculty/        the four faculty pages
    coordinator/    Rankings, Review, Courses, Sections, Instructors, Semesters, AuditLog
```

To add a page: create a file in `pages/`, add a route in `App.jsx`, add a link in `components/Layout.jsx`.
Every page loads data with `useLoad(() => api.get("/something"))` and changes it with `api.post/patch/del`.

## Build for production

`npm run build` creates a `dist/` folder of static files.
