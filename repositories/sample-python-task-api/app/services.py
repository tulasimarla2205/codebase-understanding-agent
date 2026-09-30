import uuid
from datetime import datetime
from typing import List, Optional
from .models import Task, TaskCreate

tasks_db = {}

def list_all_tasks(completed: Optional[bool] = None) -> List[Task]:
    all_tasks = list(tasks_db.values())
    if completed is not None:
        return [t for t in all_tasks if t.completed == completed]
    return all_tasks

def create_task(data: TaskCreate) -> Task:
    task_id = str(uuid.uuid4())
    now = datetime.utcnow()
    task = Task(
        id=task_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        completed=False,
        created_at=now,
        updated_at=now
    )
    tasks_db[task_id] = task
    return task

def complete_task(task_id: str) -> Optional[Task]:
    if task_id not in tasks_db:
        return None
    task = tasks_db[task_id]
    task.completed = True
    task.updated_at = datetime.utcnow()
    return task
