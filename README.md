# SIMDAA SOLVO

**Ask. Solve. Share.**

SIMDAA SOLVO is an internal Doubt Clearance and Knowledge Sharing Platform developed for Simdaa Technologies. The platform enables employees, trainees, interns, and mentors to ask questions, share solutions, collaborate, and build a centralized knowledge repository instead of relying on scattered communication across emails, chats, meetings, and messaging platforms.

---

## Overview

Organizations often face challenges when technical knowledge is shared through multiple communication channels. Valuable information gets lost, repeated questions consume time, and new team members struggle to find previous solutions.

SIMDAA SOLVO solves this problem by providing a centralized platform where users can:

* Ask technical and non-technical questions
* Answer and discuss queries
* Vote on useful answers
* Build a searchable knowledge base
* Encourage participation through community collaboration
* Preserve organizational knowledge

---

## Key Features

### User Management

* User Registration
* User Authentication
* Role-Based Access
* Admin Management

### Question Management

* Create Questions
* View Questions
* Categorize Questions
* Question Status Tracking

### Answer Management

* Submit Answers
* View Answers by Question
* Accepted Answer Support

### Voting System

* Upvote Answers
* Community-driven answer ranking

### Categories

* Organize questions into categories
* Easy navigation and filtering

### Knowledge Sharing

* Centralized knowledge repository
* Reusable solutions for future reference

### Future Enhancements

* Knowledge Base Articles
* AI Assistant Integration
* Smart Search
* Notifications
* Points & Badges System
* Leaderboard
* File Attachments

---

## Technology Stack

### Frontend

* React.js
* Vite
* HTML5
* CSS3
* JavaScript

### Backend

* FastAPI
* Python

### Database

* Microsoft SQL Server
* SQLAlchemy ORM

### API Documentation

* Swagger UI
* OpenAPI

### Authentication

* JWT Authentication

### AI Integration (Future)

* Ollama
* Open Source LLMs
* Gemini API

---

## Project Structure

```text
SIMDAA_SOLVO/
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── user_routes.py
│   │   │   ├── category_routes.py
│   │   │   ├── question_routes.py
│   │   │   ├── answer_routes.py
│   │   │   └── vote_routes.py
│   │   │
│   │   ├── models.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│
├── docs/
│
└── README.md
```

---

## Database Modules

### Users

Stores user information and roles.

### Categories

Stores question categories.

### Questions

Stores all user questions.

### Answers

Stores answers for questions.

### Votes

Stores answer votes.

---

## API Modules

### User APIs

```http
POST /users/
GET /users/
GET /users/{id}
```

### Category APIs

```http
POST /categories/
GET /categories/
GET /categories/{id}
```

### Question APIs

```http
POST /questions/
GET /questions/
GET /questions/{id}
```

### Answer APIs

```http
POST /answers/
GET /answers/question/{question_id}
```

### Vote APIs

```http
POST /votes/
GET /votes/answer/{answer_id}
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/SarangiBendre/SIMDAA_SOLVO.git
cd SIMDAA_SOLVO
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Database

Update database connection string inside:

```text
backend/app/database.py
```

Example:

```python
DATABASE_URL = "mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+18+for+SQL+Server"
```

---

## Run Backend Server

```bash
uvicorn app.main:app --reload
```

Server:

```text
http://127.0.0.1:8000
```

Swagger Documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Testing

All APIs were tested successfully using:

* Swagger UI
* SQL Server Database Verification

Modules Tested:

* Users
* Categories
* Questions
* Answers
* Votes

---

## Project Objectives

* Centralize organizational knowledge
* Reduce duplicate questions
* Improve collaboration
* Increase productivity
* Enable faster onboarding
* Build a searchable knowledge repository

---

## Future Roadmap

### Phase 2

* JWT Authentication
* Role Management
* File Uploads
* Notifications

### Phase 3

* Knowledge Base
* Smart Search
* AI Assistant Integration

### Phase 4

* Points System
* Badges
* Leaderboard
* Analytics Dashboard

---

## Developer

**Sarangi Bendre**
B.Tech Artificial Intelligence & Machine Learning
Data Analyst Intern – Simdaa Technologies

GitHub: [SarangiBendre](https://github.com/SarangiBendre?utm_source=chatgpt.com)

---

## License

This project was developed as an internal knowledge-sharing platform for learning, internship, and organizational collaboration purposes.
