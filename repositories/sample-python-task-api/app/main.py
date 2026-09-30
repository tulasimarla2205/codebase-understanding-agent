from fastapi import FastAPI, HTTPException
from typing import List, Optional
from .models import Task, TaskCreate
from . import services

app = FastAPI(title="Sample Task Management API")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "task-api"}

@app.get("/tasks", response_model=List[Task])
def get_tasks(completed: Optional[bool] = None):
    return services.list_all_tasks(completed=completed)

@app.post("/tasks", response_model=Task, status_code=201)
def add_task(payload: TaskCreate):
    return services.create_task(payload)

@app.patch("/tasks/{task_id}/complete", response_model=Task)
def mark_done(task_id: str):
    task = services.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
