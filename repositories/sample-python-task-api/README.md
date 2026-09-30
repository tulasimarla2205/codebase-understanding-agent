# Sample Task Management API

A lightweight FastAPI service managing todo tasks, task assignees, and prioritization.

## Key Modules
- `main.py`: Creates FastAPI instance and registers routers.
- `routers/tasks.py`: Task CRUD endpoints (`GET /tasks`, `POST /tasks`, `DELETE /tasks/{id}`).
- `services/task_service.py`: Business logic for status transitions and notification hooks.
- `models/task.py`: Pydantic data schemas.
