import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import DependencyItem, DependencyAnalysisResult

IGNORE_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "target", "out", "bin",
    ".venv", "venv", "env", ".idea", ".vscode", ".next", ".nuxt", "coverage",
    ".tox", ".cache", ".turbo"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".exe", ".dll", ".so", ".dylib", ".bin",
    ".iso", ".tar", ".gz", ".zip", ".7z", ".png", ".jpg", ".jpeg",
    ".gif", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".eot", ".mp4",
    ".mp3", ".wav", ".pdf", ".lock", ".class", ".o", ".obj"
}

def is_binary_file(file_path: Path, block_size: int = 1024) -> bool:
    """Check if a file appears to be binary by inspecting for null bytes or decoding failures."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(block_size)
            if b"\x00" in chunk:
                return True
            # Attempt decoding chunk as utf-8
            chunk.decode("utf-8")
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return True

def safe_resolve_repo_path(repo_base_path: str, target_subpath: str = "") -> Path:
    """
    Safely resolve a target path within a repository base directory.
    Ensures directory traversal attacks (e.g. '../') are blocked and sandboxed.
    """
    base = Path(repo_base_path).resolve()
    if not base.exists() or not base.is_dir():
        raise ValueError(f"Repository directory does not exist or is not a directory: {repo_base_path}")
    
    if not target_subpath:
        return base
        
    # Strip any leading slashes/backslashes to resolve relative to base
    cleaned_subpath = target_subpath.lstrip("/\\")
    resolved_target = (base / cleaned_subpath).resolve()
    
    # Check that resolved_target is inside base
    try:
        resolved_target.relative_to(base)
    except ValueError:
        raise PermissionError(f"Access denied: Path '{target_subpath}' escapes repository boundary.")
        
    return resolved_target

def parse_package_json(content: str, rel_path: str) -> List[DependencyItem]:
    """Extract dependencies and devDependencies from package.json."""
    deps = []
    try:
        data = json.loads(content)
        for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
            if dep_type in data and isinstance(data[dep_type], dict):
                for name, ver in data[dep_type].items():
                    deps.append(DependencyItem(
                        name=name,
                        version=str(ver),
                        ecosystem="Node.js/npm",
                        source_file=rel_path
                    ))
    except Exception:
        pass
    return deps

def parse_requirements_txt(content: str, rel_path: str) -> List[DependencyItem]:
    """Extract dependencies from requirements.txt."""
    deps = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r") or line.startswith("-i"):
            continue
        # Split on standard comparison operators
        parts = re.split(r"(==|>=|<=|~=|>|<|!=)", line, maxsplit=1)
        pkg_name = parts[0].strip()
        version = parts[1] + parts[2].strip() if len(parts) > 2 else None
        if pkg_name:
            deps.append(DependencyItem(
                name=pkg_name,
                version=version,
                ecosystem="Python/pip",
                source_file=rel_path
            ))
    return deps

def parse_pyproject_toml(content: str, rel_path: str) -> List[DependencyItem]:
    """Simple regex-based extractor for pyproject.toml dependencies."""
    deps = []
    in_deps_section = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and ("dependencies" in stripped or "project.dependencies" in stripped):
            in_deps_section = True
            continue
        elif stripped.startswith("["):
            in_deps_section = False
            continue
        
        if in_deps_section and stripped:
            m = re.match(r'["\']([a-zA-Z0-9_\-\.]+)(?:([=><~!^][^"\']+))?["\']', stripped)
            if m:
                deps.append(DependencyItem(
                    name=m.group(1),
                    version=m.group(2).strip() if m.group(2) else None,
                    ecosystem="Python/pyproject",
                    source_file=rel_path
                ))
            else:
                m_kv = re.match(r'([a-zA-Z0-9_\-\.]+)\s*=\s*["\']([^"\']+)["\']', stripped)
                if m_kv:
                    deps.append(DependencyItem(
                        name=m_kv.group(1),
                        version=m_kv.group(2),
                        ecosystem="Python/poetry",
                        source_file=rel_path
                    ))
    return deps

def parse_pom_xml(content: str, rel_path: str) -> List[DependencyItem]:
    """Extract dependencies from Maven pom.xml using regex."""
    deps = []
    dep_blocks = re.findall(r"<dependency>(.*?)</dependency>", content, re.DOTALL)
    for block in dep_blocks:
        group = re.search(r"<groupId>(.*?)</groupId>", block)
        artifact = re.search(r"<artifactId>(.*?)</artifactId>", block)
        version = re.search(r"<version>(.*?)</version>", block)
        if artifact:
            pkg_name = f"{group.group(1)}:{artifact.group(1)}" if group else artifact.group(1)
            deps.append(DependencyItem(
                name=pkg_name,
                version=version.group(1) if version else None,
                ecosystem="Java/Maven",
                source_file=rel_path
            ))
    return deps

def parse_go_mod(content: str, rel_path: str) -> List[DependencyItem]:
    """Extract require dependencies from go.mod."""
    deps = []
    in_require = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require ("):
            in_require = True
            continue
        elif in_require and line.startswith(")"):
            in_require = False
            continue
        elif line.startswith("require ") and not line.startswith("require ("):
            parts = line.split()
            if len(parts) >= 3:
                deps.append(DependencyItem(
                    name=parts[1],
                    version=parts[2],
                    ecosystem="Go/GoModules",
                    source_file=rel_path
                ))
        elif in_require and line and not line.startswith("//"):
            parts = line.split()
            if len(parts) >= 2:
                deps.append(DependencyItem(
                    name=parts[0],
                    version=parts[1],
                    ecosystem="Go/GoModules",
                    source_file=rel_path
                ))
    return deps

def parse_cargo_toml(content: str, rel_path: str) -> List[DependencyItem]:
    """Extract dependencies from Rust Cargo.toml."""
    deps = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[dependencies]") or stripped.startswith("[dev-dependencies]"):
            in_deps = True
            continue
        elif stripped.startswith("["):
            in_deps = False
            continue
        
        if in_deps and stripped and not stripped.startswith("#"):
            if "=" in stripped:
                parts = stripped.split("=", 1)
                name = parts[0].strip()
                val = parts[1].strip().strip('"\'')
                deps.append(DependencyItem(
                    name=name,
                    version=val,
                    ecosystem="Rust/Cargo",
                    source_file=rel_path
                ))
    return deps

def verify_dependency_usage(repo_base_path: str, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Verify whether declared dependencies are actually imported and used in the repository source files.
    Returns enriched dependency analysis with usage evidence (file paths and line numbers).
    """
    base_dir = safe_resolve_repo_path(repo_base_path)
    results = []
    
    for dep in dependencies:
        dep_name = dep.get("name", "")
        if not dep_name:
            continue
            
        # Clean package name for import matching (e.g. '@types/node' -> 'node', 'bcryptjs' -> 'bcryptjs')
        clean_name = dep_name.split("/")[-1]
        
        # Patterns for Node.js (require/import) and Python (import)
        patterns = [
            re.compile(rf"""require\s*\(\s*['"]{re.escape(dep_name)}['"]\s*\)"""),
            re.compile(rf"""from\s+['"]{re.escape(dep_name)}['"]"""),
            re.compile(rf"""import\s+.*\s+from\s+['"]{re.escape(dep_name)}['"]"""),
            re.compile(rf"""import\s+{re.escape(clean_name)}"""),
            re.compile(rf"""from\s+{re.escape(clean_name)}\s+import"""),
        ]
        
        used_locations = []
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file_name in files:
                file_p = Path(root) / file_name
                ext = file_p.suffix.lower()
                if ext in IGNORE_EXTENSIONS or file_name.startswith(".") or file_p.name in ["package.json", "package-lock.json", "requirements.txt", "pyproject.toml", "pom.xml", "go.mod", "Cargo.toml"]:
                    continue
                if is_binary_file(file_p):
                    continue
                    
                rel_path = file_p.relative_to(base_dir).as_posix()
                try:
                    with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, start=1):
                            if any(p.search(line) for p in patterns):
                                used_locations.append({
                                    "file": rel_path,
                                    "line": line_idx,
                                    "statement": line.strip()
                                })
                except Exception:
                    continue
                    
        results.append({
            "name": dep_name,
            "version": dep.get("version"),
            "ecosystem": dep.get("ecosystem"),
            "manifest_file": dep.get("source_file"),
            "is_used_in_code": len(used_locations) > 0,
            "usage_count": len(used_locations),
            "usage_evidence": used_locations
        })
        
    return results
