import py_compile
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

files_to_check = [
    BASE / "backend" / "models.py",
    BASE / "backend" / "analyzer.py",
    BASE / "backend" / "tools.py",
    BASE / "backend" / "agent.py",
    BASE / "backend" / "main.py",
    BASE / "test_tools.py",
    BASE / "test_investigation.py"
]

print("=== 1. CHECKING PYTHON SYNTAX ON ALL BACKEND FILES ===")
for f in files_to_check:
    try:
        py_compile.compile(str(f), doraise=True)
        print(f"  [OK] {f.relative_to(BASE)}")
    except py_compile.PyCompileError as e:
        print(f"  [FAIL] {f.relative_to(BASE)}: {e}")
        sys.exit(1)

print("\n=== 2. RUNNING test_tools.py ===")
from test_tools import test_all_tools
test_all_tools()

print("\n=== 3. RUNNING test_investigation.py ===")
from test_investigation import run_all
run_all()

print("\n=== SUCCESS: ALL BACKEND MODULES AND INVESTIGATION SUITES PASSED! ===")
