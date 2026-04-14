# 🎓 ILES — Internship Logging & Evaluation System

> A web-based platform that manages the full internship lifecycle for university students.

---

## 📚 About the Project

ILES (Internship Logging & Evaluation System) is a web-based platform that manages the full internship lifecycle for university students. It allows student interns to submit weekly activity logs, enables workplace supervisors to review and approve them, allows academic supervisors to assign weighted evaluation scores, and gives administrators a real-time programme dashboard.

### 🧩 System Modules

| Module | Description |
| -------- | ----------- |
| **M1 — Auth & User Management** | Login, registration, and role-based access control |
| **M2 — Placements** | Linking students to companies and supervisors |
| **M3 — Logbook** | Weekly log submission with deadline enforcement |
| **M4 — Review Workflow** | Supervisor review, approvals, and notifications |
| **M5 — Dashboards & Scoring** | Evaluation scores, charts, and admin analytics |

---

## 🛠️ Tech Stack

| Layer | Technology |
| ------- | ---------- |
| **Backend** | Python 3.11+, Django 4.x, Django REST Framework |
| **Frontend** | React 18, React Router DOM |
| **Database** | PostgreSQL |
| **Authentication** | JWT (SimpleJWT) |
| **Version Control** | Git & GitHub |

---

## ⚙️ Prerequisites

Before running the project, make sure you have the following installed:

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 15+
- Git
- VS Code *(recommended editor)*

Verify your installations by running:

```bash
python --version
node --version
psql --version
git --version
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/iles.git
cd iles
```

### 2. Backend Setup (Django)

```bash
# Navigate to backend folder
cd iles_backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations (make sure PostgreSQL DB 'iles_db' exists)
python manage.py migrate

# Start the backend server
python manage.py runserver
```

> 🔗 Backend runs at: **<http://127.0.0.1:8000>**

### 3. Frontend Setup (React)

```bash
# Open a new terminal and navigate to frontend folder
cd iles_frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

> 🔗 Frontend runs at: **<http://localhost:3000>**

---

## 🔁 Daily Git Workflow

Follow this workflow every day **without exception**:

```bash
# 1. Switch to your branch
git checkout m5-dashboard

# 2. Pull latest changes from dev
git pull origin dev

# 3. Do your work, then stage and commit
git add .
git commit -m "feat(dashboard): add score chart component"

# 4. Push to your branch
git push origin m5-dashboard
```

---

## 🌿 Team Branches

| Branch | Purpose |
| -------- | --------- |
| `main` | Production-ready code only |
| `dev` | Shared integration branch *(always pull from here)* |
| `m1-auth` | M1: Auth & User Management |
| `m2-placement` | M2: Placements Module |
| `m3-logbook` | M3: Logbook Module |
| `m4-review` | M4: Review Workflow |
| `m5-dashboard` | M5: Dashboards & Scoring |

---

## 📅 Project Timeline

| Week | Focus |
| ------ | ------- |
| Week 1 | Environment setup, SDLC foundations, Django & React scaffolding |
| Week 2 | Custom user model, JWT auth, placement APIs |
| Week 3 | Logbook module, weekly log forms, deadline logic |
| Week 4 | Review workflow, state machine, notifications |
| Week 5 | Dashboards, scoring engine, charts |
| Week 6 | Integration, testing, bug fixes |
| Week 7 | Final polish, deployment, presentation |

---

## 👥 Authors

**Tambwe Rahim Stone** 
**Kamwine Jonan** 

---

## Prepared by Group 5
