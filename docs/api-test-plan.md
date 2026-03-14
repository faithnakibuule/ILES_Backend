# ILES API Test Plan
**Author:** Kessie 
**Purpose:** List all API endpoints each user role will need, so the team builds the right things.

## How to Read This Table

| Column | Meaning |
|--------|---------|
| URL | The address React sends a request to |
| Method | GET = read data, POST = create, PATCH = update, DELETE = remove |
| What it does | Plain English description |
| Who can use it | Which role is allowed |

## Role: Student Intern

| URL | Method | What it does | Who can use it |
|-----|--------|-------------|----------------|
| /api/auth/login/ | POST | Student logs in, receives a JWT token | Anyone (unauthenticated) |
| /api/auth/me/ | GET | Returns the student's own profile (name, email, role) | Student (authenticated) |
| /api/placements/my/ | GET | Returns the student's active placement details | Student only |
| /api/logs/ | GET | Lists all of the student's own weekly logs | Student only |
| /api/logs/ | POST | Creates a new weekly log (starts as DRAFT) | Student only |
| /api/logs/{id}/ | PATCH | Edits a DRAFT log | Student only |
| /api/logs/{id}/submit/ | POST | Changes log status from DRAFT → SUBMITTED | Student only |
| /api/evaluations/my/ | GET | Returns the student's scored evaluations | Student only |
| /api/notifications/ | GET | Lists the student's notifications | Student only |
| /api/notifications/{id}/read/ | PATCH | Marks a notification as read | Student only |
| /api/dashboards/student-stats/ | GET | Returns counts for the student's dashboard stat cards | Student only |

## Role: Workplace Supervisor

| URL | Method | What it does | Who can use it |
|-----|--------|-------------|----------------|
| /api/auth/login/ | POST | Supervisor logs in, receives a JWT token | Anyone (unauthenticated) |
| /api/auth/me/ | GET | Returns supervisor's own profile | Workplace Supervisor (authenticated) |
| /api/placements/?supervisor=me | GET | Lists all interns assigned to this supervisor | Workplace Supervisor only |
| /api/logs/?status=SUBMITTED&supervisor=me | GET | Lists all logs awaiting review from this supervisor's interns | Workplace Supervisor only |
| /api/logs/{id}/review/ | POST | Approves a submitted log → status becomes REVIEWED | Workplace Supervisor only |
| /api/logs/{id}/send_back/ | POST | Sends a log back to DRAFT with a comment | Workplace Supervisor only |
| /api/notifications/ | GET | Lists the supervisor's notifications | Workplace Supervisor only |
| /api/dashboards/workplace-stats/ | GET | Returns pending_reviews, approved_today, total_interns counts | Workplace Supervisor only |

## Role: Academic Supervisor

| URL | Method | What it does | Who can use it |
|-----|--------|-------------|----------------|
| /api/auth/login/ | POST | Academic supervisor logs in | Anyone (unauthenticated) |
| /api/auth/me/ | GET | Returns academic supervisor's own profile | Academic Supervisor (authenticated) |
| /api/logs/?status=REVIEWED | GET | Lists all logs ready to be scored | Academic Supervisor only |
| /api/evaluations/ | POST | Creates a scored evaluation for a REVIEWED log | Academic Supervisor only |
| /api/evaluations/{id}/ | GET | Retrieves a specific evaluation | Academic Supervisor only |
| /api/dashboards/academic-stats/ | GET | Returns logs_to_score, avg_cohort_score, fully_approved | Academic Supervisor only |
| /api/dashboards/cohort-scores/ | GET | Returns a ranked list of students with their average scores | Academic Supervisor only |

## Role: Administrator

| URL | Method | What it does | Who can use it |
|-----|--------|-------------|----------------|
| /api/auth/login/ | POST | Admin logs in | Anyone (unauthenticated) |
| /api/auth/me/ | GET | Returns admin's own profile | Admin (authenticated) |
| /api/admin/users/ | GET | Lists all users (filterable by role) | Admin only |
| /api/admin/users/ | POST | Creates a new user (assigns role) | Admin only |
| /api/admin/users/{id}/ | PATCH | Edits a user's role or deactivates them | Admin only |
| /api/placements/ | GET | Lists all placements in the system | Admin only |
| /api/placements/ | POST | Creates a new placement (assigns student to supervisor) | Admin only |
| /api/placements/{id}/ | PATCH | Updates placement status | Admin only |
| /api/admin/stats/ | GET | Returns system-wide counts for admin dashboard stat cards | Admin only |
| /api/dashboards/logs-per-week/ | GET | Returns log counts grouped by week number (for bar chart) | Admin only |
| /api/dashboards/status-distribution/ | GET | Returns count of logs per status (for pie chart) | Admin only |
| /api/admin/export/placements/ | GET | Downloads a CSV file of all placements | Admin only |
| /api/admin/export/logs/ | GET | Downloads a CSV file of all logs with scores | Admin only |

## Notes for the Team

- All endpoints **except** `/api/auth/login/` and `/api/auth/register/` require a valid JWT token in the request header: `Authorization: Bearer <token>`
- If a user tries to access an endpoint they don't have permission for, the API must return **HTTP 403 Forbidden**
- If a resource is not found, the API must return **HTTP 404 Not Found**
- All successful creations return **HTTP 201 Created**
- All successful reads return **HTTP 200 OK**