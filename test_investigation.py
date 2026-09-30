"""
End-to-End Investigation Verification Test
Tests:
1. sample-auth-service (Node.js / Express):
   "How does user authentication work in this project from login request to authenticated API access?"
2. sample-python-task-api (Python / FastAPI):
   "How does task creation and listing work in this project?"
"""

import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agent import CodebaseAgent
from backend.tools import list_files, search_code, read_file, get_dependencies
from backend.analyzer import verify_dependency_usage

def test_auth_service_investigation():
    print("=" * 70)
    print("TEST 1: INVESTIGATION ON sample-auth-service (Node.js / Express)")
    print("=" * 70)

    repo_dir = PROJECT_ROOT / "repositories" / "sample-auth-service"
    question = "How does user authentication work in this project from login request to authenticated API access?"

    print(f"[REPO]: {repo_dir.name}")
    print(f"[QUESTION]: {question}\n")

    # 1. Verify Repository Discovery
    discovered = list_files(str(repo_dir))
    assert discovered["success"] is True, f"Discovery failed: {discovered.get('error')}"
    file_paths = [f["path"] for f in discovered["files"]]
    print(f"Discovered {len(file_paths)} files:")
    for fp in file_paths:
        print(f"  - {fp}")

    expected_files = [
        "package.json", "README.md", "src/index.js", "src/config/jwtConfig.js",
        "src/controllers/authController.js", "src/middleware/authMiddleware.js",
        "src/models/userModel.js", "src/routes/authRoutes.js", "src/services/authService.js"
    ]
    for ef in expected_files:
        assert ef in file_paths, f"Expected file '{ef}' was not discovered!"
    print("  [OK] All 9 repository files discovered.")

    # 2. Verify Dependency Extraction & Code Usage Verification
    raw_deps = get_dependencies(str(repo_dir))
    assert raw_deps["success"] is True
    verified_deps = verify_dependency_usage(str(repo_dir), raw_deps["dependencies"])
    used_deps = [d["name"] for d in verified_deps if d["is_used_in_code"]]
    print(f"Dependencies verified in source code: {', '.join(used_deps)}")
    assert "jsonwebtoken" in used_deps
    assert "bcryptjs" in used_deps
    assert "express" in used_deps
    print("  [OK] Dependencies verified against real source imports.")

    # 3. Execute Full Agent Investigation
    agent = CodebaseAgent(repo_path=str(repo_dir))
    response = agent.run_investigation(question)

    assert response.success is True, f"Investigation failed: {response.error}"
    assert response.question == question, f"Contaminated question: {response.question}"
    assert len(response.investigation_steps) >= 4, "Too few investigation steps"
    assert len(response.evidence) >= 2, "Too few evidence items"
    assert len(response.execution_flow) >= 3, "Too few execution flow steps"

    print(f"\nActivity Steps Logged ({len(response.investigation_steps)}):")
    for step in response.investigation_steps:
        print(f"  [{step.step_number}] {step.activity} -> {step.result_summary or ''}")

    print(f"\nEvidence Collected ({len(response.evidence)} items):")
    for ev in response.evidence:
        print(f"  - File: {ev.file_path} | Lines: {ev.lines}")
        print(f"    Finding: {ev.finding}")
        assert ev.file_path in file_paths, f"Evidence cites invalid file: {ev.file_path}"
        assert ev.lines, "Evidence missing line range"

    print(f"\nExecution Flow Steps ({len(response.execution_flow)} nodes):")
    for node in response.execution_flow:
        print(f"  Step {node.step}: {node.component_or_function} ({node.file_path})")

    for section in ["SUMMARY", "KEY FINDINGS", "EXECUTION FLOW", "EVIDENCE", "DEPENDENCIES"]:
        assert section in response.final_answer, f"Missing section '{section}' in final answer"

    print("\n  [PASS] sample-auth-service investigation passed completely!")

def test_python_api_investigation():
    print("\n" + "=" * 70)
    print("TEST 2: INVESTIGATION ON sample-python-task-api (Python / FastAPI)")
    print("=" * 70)

    repo_dir = PROJECT_ROOT / "repositories" / "sample-python-task-api"
    question = "How does task creation and listing work in this project?"

    print(f"[REPO]: {repo_dir.name}")
    print(f"[QUESTION]: {question}\n")

    agent = CodebaseAgent(repo_path=str(repo_dir))
    response = agent.run_investigation(question)

    assert response.success is True, f"Python repo investigation failed: {response.error}"
    assert response.question == question
    assert len(response.evidence) >= 1
    assert len(response.execution_flow) >= 1

    print(f"Activity Steps Logged ({len(response.investigation_steps)}):")
    for step in response.investigation_steps:
        print(f"  [{step.step_number}] {step.activity} -> {step.result_summary or ''}")

    print(f"Evidence Collected ({len(response.evidence)} items):")
    for ev in response.evidence:
        print(f"  - File: {ev.file_path} (Lines {ev.lines}): {ev.finding}")

    print("\n  [PASS] sample-python-task-api investigation passed completely!")

def run_all():
    test_auth_service_investigation()
    test_python_api_investigation()
    print("\n" + "=" * 70)
    print("ALL INVESTIGATION SUITES PASSED FOR BOTH REPOSITORIES!")
    print("=" * 70)

if __name__ == "__main__":
    run_all()
