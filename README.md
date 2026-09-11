# Team Task Manager (TSM) API

A robust RESTful API for a simplified Trello/Asana-style task management system, built with Django and Django REST Framework. This project demonstrates backend engineering practices including role-based access control, JWT authentication, query optimization, comprehensive automated testing, and cloud deployment.

## 🚀 Live Demo & API Documentation
The API is fully containerized and deployed to the cloud. You can interact with the endpoints and create a test account via the self-hosted Swagger UI:
👉 **[TSM Backend Live API Docs](https://tsm-backend.liara.run/api/docs/)**

---

## ✨ Key Features & Engineering Decisions

*   **Query & Performance Optimization:** Eliminated N+1 query issues by using `select_related` and `prefetch_related` across list and detail views. Replaced heavy Python loops with database-level ORM operations using `annotate` (e.g., counting memberships).
*   **Security Hardening:** Implemented environment-based configuration for `DEBUG` and `ALLOWED_HOSTS`. Enforced strict security middleware including HTTPS redirects, secure cookies, and HSTS. Implemented JWT blacklisting to invalidate revoked refresh tokens.
*   **Database Configuration:** Uses `dj-database-url` to configure SQLite for local development and PostgreSQL for production.
*   **Atomic Transactions:** Critical endpoints, such as `TransferOwnershipView`, are wrapped in `transaction.atomic()` to ensure data integrity during complex role reassignments.
*   **API Rate Limiting (Throttling):** Implemented global `AnonRateThrottle` (20/min) and `UserRateThrottle` (100/min), with highly restrictive custom throttling (5/hour) for sensitive endpoints like ownership transfer.
*   **Self-Hosted OpenAPI Docs:** Integrated `drf-spectacular` with a sidecar setup to serve Swagger UI assets locally via WhiteNoise, bypassing geo-restricted external CDNs.
*   **Nested + Flat URL Structure:** Creating/listing requires a parent (e.g., `POST /api/teams/{id}/tasks/`), making hierarchy explicit. Retrieving/updating/deleting needs only the resource ID (e.g., `PATCH /api/tasks/{id}/`).

## 🛠️ Tech Stack

*   **Backend:** Python, Django, Django REST Framework (DRF)
*   **Database:** PostgreSQL (Production), SQLite (Development)
*   **Auth:** JSON Web Tokens (JWT) via `djangorestframework-simplejwt`
*   **DevOps & Deployment:** Docker, Docker Compose, Gunicorn, WhiteNoise, Liara PaaS
*   **Testing & Docs:** `coverage.py` (99% overall coverage), `drf-spectacular` (OpenAPI 3.0)

---

## 🛡️ Authorization & Business Logic Security

*   **404 Instead of 403:** Every `get_queryset()` filters by the requesting user's membership *before* object lookup. Users with no relationship to a resource receive a `404 Not Found` rather than `403 Forbidden`, helping prevent ID enumeration attacks.
*   **Role-Escalation Prevention:** Custom validators in `MembershipRoleUpdateSerializer` strictly prevent direct assignment of the `OWNER` role through standard update endpoints.
*   **Owner Delete Protection:** System prevents the last active Owner of a team from deleting their own membership.

### Permission Matrix

| Action | Owner | Admin | Member |
|--------|:---:|:---:|:---:|
| Edit team info | ✅ | ✅ | ❌ |
| Delete team | ✅ | ❌ | ❌ |
| Transfer team ownership | ✅ | ❌ | ❌ |
| Add a member | ✅ | ✅ | ❌ |
| Change a member's role | ✅ | ❌ | ❌ |
| Remove a Member / Admin | ✅ | ✅ (Members only) | ❌ |
| Create a task | ✅ | ✅ | ✅ |
| Edit/delete any task | ✅ | ✅ | ❌ |
| Edit/delete own task | ✅ | ✅ | ✅ |
| Comment on a task | ✅ | ✅ | ✅ |

---

## 🌐 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|--------------|
| POST | `/api/register/` | Register a new user account |
| POST | `/api/token/` | Obtain access + refresh token pair |
| POST | `/api/token/refresh/` | Refresh an access token |

### Teams
| Method | Endpoint | Description |
|--------|----------|--------------|
| GET/POST | `/api/teams/` | List user's teams / Create a new team |
| GET/PUT/DEL | `/api/teams/{id}/` | Retrieve / Update / Delete a team |
| POST | `/api/teams/{id}/transfer_ownership/` | Atomically transfer team ownership |

*(For full endpoints including Tasks, Memberships, and Comments, please visit the Live API Docs link above).*

---

## 🐳 Setup & Installation (Docker)

The recommended way to run this project locally is via Docker.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/AH-Hatamian/Team-Task-Manager.git](https://github.com/AH-Hatamian/Team-Task-Manager.git)
    cd Team-Task-Manager
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file in the root directory:
    ```ini
    DEBUG=True
    SECRET_KEY=your-secure-secret-key
    DJANGO_SECURE_SSL_REDIRECT=False
    ```

3.  **Build and Start Containers:**
    ```bash
    docker-compose up -d --build
    ```
    The API will be available at `http://localhost:8000/api/docs/`.

---

## 🧪 Testing

The project includes a comprehensive automated test suite maintaining a **99% overall test coverage** across models, views, custom permissions, and validation logic.

To run the test suite and check coverage inside the Docker container:
```bash
docker-compose exec web coverage run manage.py test
docker-compose exec web coverage report
