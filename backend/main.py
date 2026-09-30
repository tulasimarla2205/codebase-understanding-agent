import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from .models import (
    InvestigateRequest,
    InvestigateResponse,
    ToolExecutionResult
)
from .tools import (
    list_files,
    search_code,
    read_file,
    get_dependencies,
    read_documentation
)
from .agent import CodebaseAgent

# Load environment variables from .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
REPOSITORIES_DIR = BASE_DIR / "repositories"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure repositories folder exists
REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Codebase Understanding Agent API",
    description="Agentic codebase exploration, evidence extraction, and architecture investigation engine.",
    version="1.0.0"
)

# Enable CORS for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def resolve_repo_path(repo_input: str) -> Path:
    """Resolve repository path either from repositories/ subfolder or direct path."""
    repo_input_clean = repo_input.strip()
    
    # Check if it is a named folder inside repositories/
    candidate_1 = REPOSITORIES_DIR / repo_input_clean
    if candidate_1.exists() and candidate_1.is_dir():
        return candidate_1.resolve()
        
    # Check if it is an absolute or relative path
    candidate_2 = Path(repo_input_clean).resolve()
    if candidate_2.exists() and candidate_2.is_dir():
        return candidate_2
        
    raise HTTPException(
        status_code=404,
        detail=f"Repository not found at '{repo_input}'. Available in 'repositories/': {[d.name for d in REPOSITORIES_DIR.iterdir() if d.is_dir()]}"
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "codebase-understanding-agent",
        "version": "1.0.0",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "openai_api_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/api/repositories")
def list_available_repositories():
    """List available sample repositories in the repositories/ folder."""
    repos = []
    if REPOSITORIES_DIR.exists():
        for item in sorted(REPOSITORIES_DIR.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                # Check for manifest / README
                has_readme = (item / "README.md").exists()
                has_package_json = (item / "package.json").exists()
                has_requirements = (item / "requirements.txt").exists()
                
                tag = "Unknown"
                if has_package_json:
                    tag = "Node.js / JavaScript"
                elif has_requirements or (item / "pyproject.toml").exists():
                    tag = "Python"
                elif (item / "pom.xml").exists():
                    tag = "Java"
                elif (item / "go.mod").exists():
                    tag = "Go"
                elif (item / "Cargo.toml").exists():
                    tag = "Rust"
                    
                repos.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": tag,
                    "has_readme": has_readme
                })
    return {"repositories": repos}

@app.post("/api/investigate", response_model=InvestigateResponse)
def investigate_codebase(req: InvestigateRequest):
    """
    Run the Codebase Understanding Agent on a target repository with a developer question.
    """
    try:
        resolved_repo = resolve_repo_path(req.repository_path)
        agent = CodebaseAgent(repo_path=str(resolved_repo), model_name=req.model_name or "gemini-2.5-flash")
        response = agent.run_investigation(req.question)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# Direct Tool Endpoints for Independent Inspection and Debugging
# ====================================================================

@app.get("/api/tools/list_files")
def api_list_files(repo: str = Query(...), subpath: str = Query(default="")):
    """Direct test endpoint for list_files tool."""
    resolved_repo = resolve_repo_path(repo)
    return list_files(str(resolved_repo), subpath=subpath)

@app.get("/api/tools/search_code")
def api_search_code(repo: str = Query(...), query: str = Query(...), ext: Optional[str] = Query(default=None)):
    """Direct test endpoint for search_code tool."""
    resolved_repo = resolve_repo_path(repo)
    return search_code(str(resolved_repo), query=query, file_extension=ext)

@app.get("/api/tools/read_file")
def api_read_file(
    repo: str = Query(...),
    file_path: str = Query(...),
    start_line: int = Query(default=1),
    end_line: Optional[int] = Query(default=None)
):
    """Direct test endpoint for read_file tool with line numbers."""
    resolved_repo = resolve_repo_path(repo)
    return read_file(str(resolved_repo), file_path=file_path, start_line=start_line, end_line=end_line)

@app.get("/api/tools/get_dependencies")
def api_get_dependencies(repo: str = Query(...)):
    """Direct test endpoint for get_dependencies tool."""
    resolved_repo = resolve_repo_path(repo)
    return get_dependencies(str(resolved_repo))

@app.get("/api/tools/read_documentation")
def api_read_documentation(repo: str = Query(...)):
    """Direct test endpoint for read_documentation tool."""
    resolved_repo = resolve_repo_path(repo)
    return read_documentation(str(resolved_repo))

# Mount frontend files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
