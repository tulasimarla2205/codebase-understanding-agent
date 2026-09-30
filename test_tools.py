"""
Independent Test Suite for Repository Inspection Tools
Tests:
1. list_files
2. search_code
3. read_file (with 1-based line numbers and sandboxing)
4. get_dependencies (Node.js and Python ecosystems)
5. Sandbox security verification
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from backend.tools import list_files, search_code, read_file, get_dependencies, read_documentation

def test_all_tools():
    print("=" * 60)
    print("RUNNING REPOSITORY INSPECTION TOOL TEST SUITE")
    print("=" * 60)
    
    sample_auth_repo = CURRENT_DIR / "repositories" / "sample-auth-service"
    sample_python_repo = CURRENT_DIR / "repositories" / "sample-python-task-api"
    
    # -------------------------------------------------------------
    # 1. Test list_files
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing list_files() on sample-auth-service...")
    res_list = list_files(str(sample_auth_repo))
    assert res_list["success"] is True, f"list_files failed: {res_list.get('error')}"
    assert res_list["total_files"] >= 6, f"Expected >= 6 files, got {res_list['total_files']}"
    file_paths = [f["path"] for f in res_list["files"]]
    print(f"  -> Discovered {len(file_paths)} files:")
    for fp in file_paths:
        print(f"     * {fp}")
    assert any("src/services/authService.js" in p for p in file_paths), "Missing authService.js"
    assert any("package.json" in p for p in file_paths), "Missing package.json"
    print("  [PASS] list_files successfully verified.")

    # -------------------------------------------------------------
    # 2. Test search_code
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing search_code() for 'jwt.sign'...")
    res_search = search_code(str(sample_auth_repo), query="jwt.sign")
    assert res_search["success"] is True, f"search_code failed: {res_search.get('error')}"
    assert res_search["total_matches"] > 0, "Expected matches for jwt.sign"
    print(f"  -> Found {res_search['total_matches']} match(es):")
    for m in res_search["matches"]:
        print(f"     * {m['file_path']} (Line {m['line_number']}): {m['line_content'].strip()}")
    assert res_search["matches"][0]["file_path"] == "src/services/authService.js"
    print("  [PASS] search_code successfully verified.")

    # -------------------------------------------------------------
    # 3. Test read_file with line numbers
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing read_file() on 'src/services/authService.js' (Lines 35 to 55)...")
    res_read = read_file(str(sample_auth_repo), file_path="src/services/authService.js", start_line=35, end_line=55)
    assert res_read["success"] is True, f"read_file failed: {res_read.get('error')}"
    assert "jwt.sign" in res_read["content"]
    assert res_read["start_line"] == 35
    print("  -> Snippet with 1-based line numbers:")
    for line in res_read["content"].split("\n")[:6]:
        print(f"     {line}")
    print("  [PASS] read_file successfully verified.")

    # -------------------------------------------------------------
    # 4. Test get_dependencies (Node.js & Python)
    # -------------------------------------------------------------
    print("\n[TEST 4A] Testing get_dependencies() on sample-auth-service (Node.js)...")
    res_deps_node = get_dependencies(str(sample_auth_repo))
    assert res_deps_node["success"] is True
    assert "Node.js/npm" in res_deps_node["ecosystems_detected"]
    dep_names = [d["name"] for d in res_deps_node["dependencies"]]
    print(f"  -> Detected packages: {', '.join(dep_names)}")
    assert "jsonwebtoken" in dep_names
    assert "bcryptjs" in dep_names
    print("  [PASS] Node.js get_dependencies successfully verified.")

    print("\n[TEST 4B] Testing get_dependencies() on sample-python-task-api (Python)...")
    res_deps_py = get_dependencies(str(sample_python_repo))
    assert res_deps_py["success"] is True
    assert "Python/pip" in res_deps_py["ecosystems_detected"]
    py_dep_names = [d["name"] for d in res_deps_py["dependencies"]]
    print(f"  -> Detected packages: {', '.join(py_dep_names)}")
    assert "fastapi" in py_dep_names
    print("  [PASS] Python get_dependencies successfully verified.")

    # -------------------------------------------------------------
    # 5. Test Sandboxing (Directory Traversal Prevention)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Sandboxing Security (attempting traversal ../../)...")
    res_sandbox = read_file(str(sample_auth_repo), file_path="../../main.py")
    assert res_sandbox["success"] is False, "Sandboxing failed to block directory traversal!"
    print(f"  -> Security Traversal Blocked as expected: {res_sandbox['error']}")
    print("  [PASS] Sandbox security successfully verified.")

    # -------------------------------------------------------------
    # 6. Test read_documentation
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing read_documentation()...")
    res_doc = read_documentation(str(sample_auth_repo))
    assert res_doc["success"] is True
    assert "README.md" in res_doc["documentation_files"]
    print(f"  -> Documentation files: {res_doc['documentation_files']}")
    print("  [PASS] read_documentation successfully verified.")

    print("\n" + "=" * 60)
    print("ALL REPOSITORY INSPECTION TOOL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_all_tools()
