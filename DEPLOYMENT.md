### 📄 `DEPLOYMENT.md`

# 🚀 Deployment Details

## 🌍 Live Links

- **Base API:** [https://talent-bridge-api.vercel.app/api/v1/](https://talent-bridge-api.vercel.app/api/v1/)
- **Swagger Documentation:** [https://talent-bridge-api.vercel.app/swagger/](https://talent-bridge-api.vercel.app/swagger/)

---

## 👤 Demo Accounts

| Role       | Email                      | Password   |
| ---------- | -------------------------- | ---------- |
| Admin      | `admin1@dhakajobs.local`   | `kgb12345` |
| Employer   | `hello@sylhetdata.com`     | `kgb12345` |
| Job Seeker | `seeker15@jobportal.local` | `kgb12345` |

Use these credentials to log in and explore the API in Swagger or Postman.

---

## 🧩 API Headers

When calling secure endpoints, include:

```makefile
Authorization: Bearer <your_token>
```

Tokens can be obtained via:

```bash
POST /accounts/login/
```

---

## 🧠 Notes

- Hosted on **Vercel**
- Backend powered by **Django + DRF + Djoser (JWT)**
- Database: **PostgreSQL (Production)**
- Payments: **SSLCommerz Sandbox (Configured)**
- Version: `v1` (Base URL: `/api/v1/`)

---
