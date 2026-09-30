from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: str = Field(default="medium")

class Task(TaskCreate):
    id: str
    completed: bool = False
    created_at: datetime
    updated_at: datetime
