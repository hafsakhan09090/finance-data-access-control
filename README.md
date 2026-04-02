# 📊 Finance Data Access Control Backend

A RESTful API for a finance dashboard with **role-based access control (RBAC)**, built using Flask. This project enables secure access to financial data based on user roles such as Admin, Analyst, and Viewer.

---

## 🚀 Tech Stack

* **Backend Framework:** Flask
* **ORM:** SQLAlchemy
* **Database:** SQLite
* **Authentication:** JWT (JSON Web Tokens)

---

## ⚙️ Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hafsakhan09090/finance-data-access-control.git
cd finance-data-access-control
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Environment

* **Windows:**

```bash
venv\Scripts\activate
```

* **Mac/Linux:**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

---

## 👤 Default Users

| Username | Password   | Role    |
| -------- | ---------- | ------- |
| admin    | admin123   | Admin   |
| analyst1 | analyst123 | Analyst |
| viewer1  | viewer123  | Viewer  |

---

## 🔐 Authentication

This API uses **JWT tokens** for authentication.

### Get Token

```http
POST /api/auth/login
```

**Request Body:**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

---

## 📡 API Endpoints

| Method | Endpoint               | Description              |
| ------ | ---------------------- | ------------------------ |
| POST   | /api/auth/login        | Get JWT token            |
| GET    | /api/transactions      | List transactions        |
| POST   | /api/transactions      | Create transaction       |
| GET    | /api/dashboard/summary | Income & expense totals  |
| GET    | /api/dashboard/trends  | Monthly financial trends |

---

## 🧪 Testing with PowerShell

### 1. Login & Get Token

```powershell
$r = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" \
  -Method POST \
  -Body '{"username":"admin","password":"admin123"}' \
  -ContentType "application/json"
```

### 2. Access Dashboard

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/dashboard/summary" \
  -Method GET \
  -Headers @{ Authorization = "Bearer $($r.token)" }
```

---

## ✨ Features

* ✅ Role-Based Access Control (Admin / Analyst / Viewer)
* ✅ Secure JWT Authentication
* ✅ Transaction CRUD Operations with Filtering
* ✅ Financial Dashboard (Summary & Trends)
* ✅ Error Handling & Validation
* ✅ Lightweight SQLite Database

---

## 📌 Notes

* Ensure the server is running on `http://localhost:5000`
* Use tools like **Postman** or **cURL** for API testing


