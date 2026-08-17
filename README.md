# Smart University Complaint System

A web-based complaint management system developed using **Flask**. The system allows students to submit and track complaints while providing separate dashboards and complaint management features for **Administrators** and the **Head of Department (HOD)**.

## Features

### Student

- Secure login
- Submit complaints
- Select complaint category
- Select who the complaint is directed against
- Add a complaint description
- Submit emergency complaints
- View submitted complaints
- Track complaint status
- View Pending, Forwarded, and Solved complaint counts
- Monthly complaint limit of 5 complaints

### Admin

- Secure role-based access
- View complaint queue
- Priority-based complaint sorting
- View emergency complaints with higher priority
- Solve individual complaints
- Forward complaints to HOD
- Group similar compatible complaints
- Solve grouped complaints
- Forward grouped complaints to HOD
- Undo pending complaint groups

### Head of Department (HOD)

- Secure role-based access
- View complaints directed against Admin
- View complaints forwarded by Admin
- Priority-based complaint sorting
- Solve authorized complaints

## User Roles

The system contains three main roles:

| Role | Responsibilities |
|------|------------------|
| Student | Submit and track complaints |
| Admin | Manage, group, solve, and forward complaints |
| HOD | Handle complaints against Admin and forwarded complaints |

## Complaint Workflow

```text
Student
   |
   | Submit Complaint
   v
Pending
   |
   +--------------------+
   |                    |
   v                    v
Admin Solves       Admin Forwards
   |                    |
   v                    v
Solved              HOD Reviews
                          |
                          v
                       Solved
```

## Complaint Priority

Complaints are sorted according to priority:

1. Emergency + Pending
2. Pending
3. Forwarded
4. Solved

Newer complaints are displayed first when complaints have the same priority.

## Monthly Complaint Limit

Each student can submit a maximum of:

```text
5 complaints per month
```

When the limit is reached, the student cannot submit additional complaints for that month.

## Complaint Grouping

Administrators can group multiple compatible pending complaints.

Rules:

- At least 2 complaints must be selected
- Complaints must be Pending
- Complaints must not already belong to another group
- Complaints cannot be directed against Admin
- All complaints in the group must have the same `Directed Against` value

Grouped complaints can be:

- Solved together
- Forwarded to HOD together
- Ungrouped while they are still Pending

## Technologies Used

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy

### Database

- SQLite

### Frontend

- HTML
- CSS
- JavaScript
- Bootstrap 5
- Bootstrap Icons

### Security

- Werkzeug password hashing
- Flask session management
- Role-based access control

## Project Structure

```text
smart_uni_complaint_system/
│
├── app.py
├── models.py
├── extensions.py
├── seed.py
├── create_users.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── script.js
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── student_dashboard.html
│   ├── admin_dashboard.html
│   ├── hod_dashboard.html
│   └── submit_complaint.html
│
└── instance/
    └── complaints.db
```

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
```

### 2. Go to the Project Folder

```bash
cd smart_uni_complaint_system
```

### 3. Create a Virtual Environment

```bash
python -m venv .env
```

### 4. Activate the Virtual Environment

#### Windows PowerShell

```powershell
.env\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

Start the Flask application:

```bash
python app.py
```

The application will run on:

```text
http://127.0.0.1:5000
```

Open this address in your browser.

## Create Test Users

You can create the initial test users by running:

```bash
python seed.py
```

This creates the following users:

| Username | Password | Role |
|----------|----------|------|
| student1 | student123 | Student |
| admin1 | admin123 | Admin |
| hod1 | hod123 | HOD |

You can also create an additional student user using:

```bash
python create_users.py
```

## Database

The application uses SQLite with the following main models:

### User

Stores:

- User ID
- Username
- Password Hash
- Role

### Complaint

Stores:

- Complaint ID
- Student ID
- Category
- Directed Against
- Description
- Urgency Level
- Status
- Date Submitted
- Group ID

## Security Notes

This is currently a prototype project.

Before deploying to production:

- Change the Flask secret key
- Store the secret key in environment variables
- Disable `debug=True`
- Use a production-ready database
- Add CSRF protection
- Add proper form validation
- Add better error handling

## Future Improvements

- Email notifications
- Complaint search and filtering
- Admin analytics
- Complaint categories management
- File attachments
- User registration
- Password reset
- Notification system
- Better audit logging
- REST API
- Deployment to a production server

## Author

**Mudasir Rehman**

## Project Status

🚧 Prototype Phase — Under Development