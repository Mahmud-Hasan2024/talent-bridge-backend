### 📄 `README.md`

# 🌐 Talent Bridge Job Portal API

Talent Bridge is a **Django REST Framework–powered job portal** where **Employers** can post jobs, **Job Seekers** can apply or withdraw applications, and **Admins** can manage all platform activities.  
It includes **JWT authentication**, **role-based dashboards**, **Swagger API documentation**, and **SSLCommerz payment gateway** integration.

---

## 🚀 Live Demo

- 🔗 **Production:** [https://talent-bridge-frontend-psi.vercel.app/](https://talent-bridge-frontend-psi.vercel.app/)

- 🌍 **Base API:** [https://talent-bridge-api.vercel.app/api/v1/](https://talent-bridge-api.vercel.app/api/v1/)
- 📘 **Swagger Docs:** [https://talent-bridge-api.vercel.app/swagger/](https://talent-bridge-api.vercel.app/swagger/)

---

## 👤 Demo Accounts

| Role       | Email                      | Password   |
| ---------- | -------------------------- | ---------- |
| Admin      | `admin1@dhakajobs.local`   | `kgb12345` |
| Employer   | `hello@sylhetdata.com`     | `kgb12345` |
| Job Seeker | `seeker15@jobportal.local` | `kgb12345` |

Use these credentials to log in and explore the API in Swagger or Postman.

---

## 🧠 Features

- 👤 **Custom User Roles:** Admin, Employer, and Job Seeker
- 💼 **Job Management:** Employers can post, edit, and delete job listings
- 📄 **Applications:** Job Seekers can apply or withdraw job applications
- ⭐ **Reviews:** Job Seekers can review employers
- 💳 **Payments:** SSLCommerz gateway integration
- 📊 **Dashboards:** Role-based analytics and activity overview
- 🔐 **JWT Authentication (Djoser)**
- 🧾 **Swagger API Docs (drf-yasg)**
- 🧹 **Seed Script:** Automatically populates realistic demo data

---

## 🧰 Tech Stack

| Component      | Technology                    |
| -------------- | ----------------------------- |
| Backend        | Django, Django REST Framework |
| Authentication | Djoser + JWT                  |
| Database       | PostgreSQL / SQLite           |
| Payments       | SSLCommerz                    |
| API Docs       | Swagger (drf-yasg)            |
| Deployment     | Vercel                        |

---

## ⚙️ Local Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/talent-bridge-api.git
cd talent-bridge-api
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Migrate Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 6️⃣ Run Development Server

```bash
python manage.py runserver
```

Visit: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🔐 Authentication (JWT)

### Register

`POST /accounts/register/`

### Login

`POST /accounts/login/`

Include your token in request headers:

```makefile
Authorization: Bearer <your_token>
```

---

## 📚 API Endpoints

### 🔸 Jobs

| Method | Endpoint      | Description                |
| ------ | ------------- | -------------------------- |
| GET    | `/jobs/`      | List all jobs              |
| POST   | `/jobs/`      | Create job (Employer only) |
| GET    | `/jobs/{id}/` | Get single job             |
| PATCH  | `/jobs/{id}/` | Update job                 |
| DELETE | `/jobs/{id}/` | Delete job                 |

### 🔸 Applications

| Method | Endpoint                                     | Description           |
| ------ | -------------------------------------------- | --------------------- |
| GET    | `/jobs/{job_pk}/applications/`               | List all applications |
| POST   | `/jobs/{job_pk}/applications/`               | Apply for a job       |
| DELETE | `/jobs/{job_pk}/applications/{id}/withdraw/` | Withdraw application  |

### 🔸 Accounts

| Method | Endpoint              | Description           |
| ------ | --------------------- | --------------------- |
| POST   | `/accounts/register/` | Register new user     |
| POST   | `/accounts/login/`    | Login and obtain JWT  |
| GET    | `/accounts/profile/`  | Retrieve user profile |

### 🔸 Dashboard

| Method | Endpoint                   | Description              |
| ------ | -------------------------- | ------------------------ |
| GET    | `/dashboard/`              | Dashboard data           |
| GET    | `/dashboard/stats/?days=7` | Stats for a given period |

---

## 📊 API Documentation

Swagger UI available at:  
👉 [https://talent-bridge-api.vercel.app/swagger/](https://talent-bridge-api.vercel.app/swagger/)

---

## 💾 Sample Data

To populate demo users, jobs, and reviews:

```bash
python manage.py populate_data
```

This will:

- Delete existing records
- Create sample employers, seekers, jobs, and applications

---

## 💳 Payments (SSLCommerz)

SSLCommerz integration is configured for secure transaction handling.  
Endpoints are available under `/payments/` (sandbox-ready).

---

## 🧠 Future Improvements

- Enhance dashboard analytics with charts
- Implement notification service
- Expand payment gateway features

---

## Deployment

For deployment instructions, refer to the [DEPLOYMENT.md](DEPLOYMENT.md) file.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Mahamud Hasan**  
Northern University Bangladesh

Learn more about me in my [About Me](About_Author.md) file.

---
