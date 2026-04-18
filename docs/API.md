# ILES API DOCUMENTATION 
# AUTHOR : MISHA 

A simple guide to how front end talks to the back end 
This document explains available API endpoints _ how to connect to back end .
Each API does one specific task : get data , save data , update data , or delete data 

The Basics 
Base URL (where all requests go ):
http://localhost:8000

How to stay logged in :
After logging in the back end gives you a token (like a temporary ID card ) You must send that token with  every request that requires login , like this :
Authorization :bearer <your_token_here>

Who can do what ? 
The system has 4 types of users (roles )
Student -The intern 
Workplace supervisor - supervises the student at the company 
Academic Supervisor - supervises from the University 
Admin - manages everything 

The END POINTS
LOGGING IN AMD REGISTRATION 
Register a new account 
POST /api/auth/register/
No login needed

What to send :
{
    "email": "jane@university.ac.ug",
    "password": "mypassword13",
    "role": "student"
}

What you get back 
{
    "id": 12,
    "email": "jane@university.ac.ug",
    "role": "student"
}

Log in 
POST /api/auth/login/

What to send :
{
    "email": jane@university.ac.ug",
    "password" : "mypassword123"
}

What you get back :
{
    "access": "Your_token_here",
    "refresh": "your_refresh_token_here",
    "role": "student"
}
 Save the access token - you'll need  it for everything else.

 Refresh your token (when it expires)
 POST /api/auth/token/refresh/
 No login needed.
 What to send:
 {
    "refresh": "your_refresh_token_here"
 }

 What to get back: a new access token.

 YOUR PROFILE 
 See your own profie 
 GET /api/auth/me/
 Must be logged in .

 What you get back:
 {
    "id": 12,
    "email": "jane@university.ac.ug",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "student",
    "phone": "+256700000"
 }

 Update your profile 
 PATCH /api/auth/me/
 Must be logged in . 

 What to send (only the fields you want to change):
 {
    "first_name": "Janet",
    "phone": "+2567111111"
}

PLACEMENTS
A placement = a student's internship at a company.

See placements

GET /api/placements/
Must be logged in.
Each user automatically sees only what they're allowed to see.

What you get back(example):
{
    "id": 3,
    " company_name": "Stanbic Bank Uganda",
    "start_date": "2025-06-01",
    "end_date": "2025-08-31",
    "status": "ACTIVE"
}

Placement can have these statuses:
STATUS         |    MEANING
PENDING        | Not  started yet 
ACTIVE         |Currently ongoing 
COMPLETED      |Finished 
CANCELLED      |Called off

Create a placement
POST /api/placements/
Admin only 

What to send :
{
    "student": 12,
    "workplace_supervisor": 7,
    "academic_supervisor": 5,
    "company_name": "Stanbic Bank Uganda",
    "start_date": "2025-06-01",
    "end_date": "2025-08-31"
}

WEEKLY LOGS
Students write a log every week describing what they did 
A log through these stages:

DRAFT -> SUBMITTED -> REVIEWED -> APPROVED    |
            | SENT BACK -> student fixes it -> SUBMITTED Again

Stage   |  Who changes it    | What it means 
DRAFT   | Student            | Written but not sent yet
SUBMITTED| Student           | Sent to work place supervisor
REVIEWED | Workplace Supervisor| Checked , forwarded to university 
APPROVED | Academic Supervisor | Scored and fully accepted

See all logs 
GET /api/logbook/logs/
Must be logged in.
Everyone sees only their own relevant logs automatically.

Write a new log 
POST /api/logbook/logs
Students only.

What to send :
{
    "placement": 3,
    "week_number": 5,
    "activities": "I have helped with database testing and migration .",
    "Learning_points": "I learned how to write SQL rollback scripts."
}

Submit a log (send it for a review)
POST /api/logbook/logs/{id}/submit/
Students only. Changes status from Draft -> Submitted.
Nothing to send . You get back: 
{ "message": "Log submitted successfully." }

Approve a log (workplace supervisor)
POST /api/logbook/logs/{id}/review_log/
Workplace Supervisors only .  Changes status : SUBMITTED -> REVIEWED.
Nothing to send .You get back:

{" message " : 'Log approved and marked as Reviewed."}

Send a log back for fixes 
POST /api/logbook/logs/{id}/send_back/
Workplace Supervisors only.  Changes status back to DRAFT .
What to send:
{
    "review_comment" : "Please add more detail about the challenges you faced."
}

See the history  of a log 
GET /api/logbook/logs/{logs_id}/history/
Must be logged in 
Shows every action ever taken on this log (submitted , reviewed, sent back, scored).

SCORES (EVALUATIONS)
Academic Supervisors score logs that have been reviewed.

Score a log 
POST /api/reviews/evaluations/
Academic Supervisors score logs that have been reviewed.

Score a log
POST /api/reviews/evaluations/
Academic Supervisors only.
The log must be in reviewed status . After scoring , it automatically becomes approved .

What to send:
{
    "log": 24,
    "total_score": "87.50",
    "criteria_scores": {
        "professionalism": 18,
        "technical_skill": 22,
        "communication": 17
    },
    "comments": "Great work this week , keep it up."
}

See Evaluations 
GET /api/reviews/evaluations/
Must be logged in.
Students see scores on their own logs . Academic supervisors see scores they gave .

NOTIFICATIONS
See your notifications 
GET /api/reviews/notifications/
Must be logged in.
[
    {
        "message" : "Your week 4 log has been reviewed.",
        "is_read": false,
        "created_at": "2025-07-02T10:00:00Z"
    }
]

Mark one notification as read 
PATCH /api/reviews/notifications/{id}/mark_as_read/

Mark all notifications as read 
POST /api/reviews/notifications/mark_all_read/

DASHBOARD STATS
Numbers shown on each user's dashboard screen.

Endpoint                                |  Who uses it        | What it returns 
GET /api/dashboards/student-stats/      |Student              |Logs Submitted , approved , overdue
GET /api/dashboards/workplace-stats/    | Workplace Supervisor  | Pending reviews, total interns 
GET /api/dashboards/academic-stats/     | Academic Supervisor        | Logs to score average cohort score 
GET /api/dashboards/admin-stats/        | Admin  | Total students, active placements 
GET /api/dashboards/pending-logs/       | Workplace Supervisor  | List of logs waiting fro review
GET /api/dashboards/student-progress/me/ | Any   |How many logs exist per week 
GET /api/dashboards/logs-per-week/      | Any    | How many logs exist per week
GET /api/dashboards/status-distribution/ | Any  | Count of logs by status
GET /api/dashboards/cohort-scores        |Academic Supervisor    | Ranked list of student scores 

When Things go Wrong 
code    | What it means    | What to do on the frontend 
400    | You sent bad or missing data | Show a form error message 
401    | Not logged in     | Redirect to login page 
403    | Logged in but not allowed  | Show "Access Denied" message 
404    | That item doesnt exist     | Show  "Not Found " message 
429    | Too many attempts    | Show "Please wait and try again "
500    | Something broke on the server     | Show " Something went wrong " 
