
# Team Task Manager

A backend-only REST API for a simplified Trello/Asana-style task management system, built with Django and Django REST Framework. This project demonstrates backend engineering practices including role-based access control, JWT authentication, and secure API design — with no frontend included by design.

## Features

- **JWT Authentication** via `djangorestframework-simplejwt`
- **Role-based access control** with three roles per team: Owner, Admin, Member
- **Team-scoped resources** — tasks, memberships, and comments are all scoped to a team and filtered by the requester's membership
- **Nested + flat URL structure** — list/create endpoints are nested under their parent resource; detail endpoints (retrieve/update/delete) are addressed directly by their own ID
- **Security-first design** — resources outside a user's membership return `404` instead of `403` to prevent ID enumeration
- **Custom permission classes** enforcing a full Owner/Admin/Member permission matrix across every resource

## Tech Stack

- Python / Django
- Django REST Framework
- djangorestframework-simplejwt (JWT authentication)
- SQLite (development)

## Project Structure

The project is organized around four core models:

- **Team** — top-level resource; owns tasks and memberships
- **Membership** — through-model linking `User` and `Team`, carrying a `role` (Owner / Admin / Member)
- **Task** — scoped to a `Team`, with separate `assignee` and `created_by` fields
- **Comment** — scoped to a `Task`, exposing a `team` property for consistent permission checks

## Setup & Installation

```bash
# Clone the repository
git clone <repo-url>
cd team-task-manager

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser (optional, for Django admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

## Authentication

This API uses JWT authentication. Obtain a token pair with your username and password, then include the access token in the `Authorization` header of subsequent requests.

```
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

For all authenticated requests:
```
Authorization: Bearer <access_token>
```

Refresh an expired access token:
```
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ..."
}
```

## API Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|--------------|
| POST | `/api/token/` | Obtain access + refresh token pair |
| POST | `/api/token/refresh/` | Refresh an access token |

### Teams

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/teams/` | List teams the current user is a member of |
| POST | `/api/teams/` | Create a new team (creator becomes Owner automatically) |
| GET | `/api/teams/{id}/` | Retrieve a team's details |
| PUT/PATCH | `/api/teams/{id}/` | Update a team (Owner or Admin only) |
| DELETE | `/api/teams/{id}/` | Delete a team (Owner only) |

### Tasks

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/teams/{team_id}/tasks/` | List tasks belonging to a team |
| POST | `/api/teams/{team_id}/tasks/` | Create a task under a team (any member) |
| GET | `/api/my_tasks/` | List tasks assigned to the current user, across all teams |
| GET | `/api/tasks/{id}/` | Retrieve a task's details |
| PUT/PATCH | `/api/tasks/{id}/` | Update a task (Owner, Admin, or the task's creator) |
| DELETE | `/api/tasks/{id}/` | Delete a task (Owner, Admin, or the task's creator) |

### Memberships

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/teams/{team_id}/memberships/` | List a team's members |
| POST | `/api/teams/{team_id}/memberships/` | Add a member to the team (Owner or Admin only) |
| GET | `/api/memberships/{id}/` | Retrieve a membership's details |
| PATCH | `/api/memberships/{id}/` | Change a member's role (Owner only) |
| DELETE | `/api/memberships/{id}/` | Remove a member (Owner can remove anyone; Admin can only remove Members) |

### Comments

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/tasks/{task_id}/comments/` | List comments on a task |
| POST | `/api/tasks/{task_id}/comments/` | Add a comment (any team member) |
| GET | `/api/comments/{id}/` | Retrieve a comment |
| PUT/PATCH | `/api/comments/{id}/` | Edit a comment (author only) |
| DELETE | `/api/comments/{id}/` | Delete a comment (author, Owner, or Admin) |

## Permission Matrix

| Action | Owner | Admin | Member |
|--------|:---:|:---:|:---:|
| Edit team info | ✅ | ✅ | ❌ |
| Delete team | ✅ | ❌ | ❌ |
| Add a member | ✅ | ✅ | ❌ |
| Change a member's role | ✅ | ❌ | ❌ |
| Remove a Member | ✅ | ✅ | ❌ |
| Remove an Admin/Owner | ✅ | ❌ | ❌ |
| Create a task | ✅ | ✅ | ✅ |
| Edit/delete any task | ✅ | ✅ | ❌ |
| Edit/delete own task | ✅ | ✅ | ✅ |
| Comment on a task | ✅ | ✅ | ✅ |
| Edit own comment | ✅ | ✅ | ✅ |
| Delete own comment | ✅ | ✅ | ✅ |
| Delete others' comment | ✅ | ✅ | ❌ |

## Key Architectural Decisions

**JWT over session authentication.** The API is designed to be consumed independently of any frontend, so token-based authentication was chosen over Django's session auth to keep the API stateless and consistent with common industry practice.

**Nested list/create, flat detail URLs.** Creating or listing a resource requires knowing its parent (e.g. `POST /api/teams/{id}/tasks/`), since REST resource creation should make the hierarchy explicit. Retrieving, updating, or deleting a specific resource only needs its own ID (e.g. `PATCH /api/tasks/{id}/`), since the ID alone is already unique. This mirrors the URL structure used in the project's Phase 2 (classic Django views).

**Generic Views instead of ViewSets + Router.** Because the URL structure is a mix of nested and flat patterns, DRF's `ModelViewSet` + `DefaultRouter` combination — which assumes a single uniform resource pattern — was a poor fit without adding an extra dependency (`drf-nested-routers`). Explicit `generics.ListCreateAPIView` / `generics.RetrieveUpdateDestroyAPIView` pairs, wired up with manually defined URL patterns, keep full control over the hierarchy without external packages.

**404 instead of 403 for non-members.** Every `get_queryset()` filters by the requesting user's membership before any object is looked up. This means a user with no relationship to a resource gets a `404 Not Found` rather than a `403 Forbidden`, preventing them from even confirming the resource exists (ID enumeration protection). This applies specifically to users with *no* membership; a member whose *role* is insufficient for a given action (e.g. a Member attempting to delete a team) correctly receives a `403`, since they already know the resource exists.

**Object-level permission classes per resource.** Each resource (`Team`, `Task`, `Membership`, `Comment`) has a dedicated `BasePermission` subclass that checks the requester's role via a shared `get_user_role()` helper, and — where relevant — ownership of the specific object (e.g. a task's `created_by`, a comment's `author`). This keeps authorization logic centralized in `permissions.py`, separate from serializer-level data validation.

## Running Tests

*(Coming soon — automated test coverage for access-control logic is planned.)*

## License

This project is for portfolio and educational purposes.
