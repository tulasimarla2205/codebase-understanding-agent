from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None

class FileItem(BaseModel):
    path: str
    is_dir: bool
    size: int
    line_count: Optional[int] = None

class SearchMatch(BaseModel):
    file_path: str
    line_number: int
    line_content: str

class DependencyItem(BaseModel):
    name: str
    version: Optional[str] = None
    ecosystem: str
    source_file: str

class DependencyAnalysisResult(BaseModel):
    ecosystems_detected: List[str]
    dependencies: List[DependencyItem]
    files_analyzed: List[str]

class EvidenceItem(BaseModel):
    status: str = Field(default="CONFIRMED", description="CONFIRMED | SUPPORTED | NOT DETERMINED")
    file_path: str
    lines: str
    finding: str
    relevance_score: Optional[float] = None
    snippet: Optional[str] = None

class ExecutionFlowNode(BaseModel):
    step: int
    file_path: str
    component_or_function: str
    description: str

class InvestigationStep(BaseModel):
    step_number: int
    activity: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    result_summary: Optional[str] = None

class InvestigateRequest(BaseModel):
    repository_path: str = Field(..., description="Local path or folder name within repositories directory")
    question: str = Field(..., description="Developer question about the codebase")
    model_name: Optional[str] = Field(default="gemini-2.5-flash", description="LLM model to use")

class InvestigateResponse(BaseModel):
    success: bool
    question: str
    repository: str
    is_answerable: bool = Field(default=True, description="Whether the question can be established from the repository")
    investigation_steps: List[InvestigationStep]
    evidence: List[EvidenceItem]
    execution_flow: List[ExecutionFlowNode]
    final_answer: str
    error: Optional[str] = None
