import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import FileItem, SearchMatch, DependencyAnalysisResult, DependencyItem
from .analyzer import (
    IGNORE_DIRS,
    IGNORE_EXTENSIONS,
    is_binary_file,
    safe_resolve_repo_path,
    parse_package_json,
    parse_requirements_txt,
    parse_pyproject_toml,
    parse_pom_xml,
    parse_go_mod,
    parse_cargo_toml,
)

def list_files(repo_path: str, subpath: str = "", max_files: int = 500) -> Dict[str, Any]:
    """
    List files and directories in the repository safely.
    Ignores common build/generated folders (.git, node_modules, __pycache__, dist, build, etc.).
    
    Args:
        repo_path: Path to the root repository folder.
        subpath: Optional relative subfolder inside the repository to list.
        max_files: Max files to return to avoid overwhelming context.
        
    Returns:
        Dict with total_count, directories, and files list.
    """
    try:
        target_dir = safe_resolve_repo_path(repo_path, subpath)
        base_dir = Path(repo_path).resolve()
        
        file_list = []
        dir_list = []
        
        for root, dirs, files in os.walk(target_dir):
            # Prune ignored directories in place
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            
            rel_root = Path(root).relative_to(base_dir).as_posix()
            if rel_root != ".":
                dir_list.append(rel_root)
                
            for file_name in files:
                file_p = Path(root) / file_name
                ext = file_p.suffix.lower()
                if ext in IGNORE_EXTENSIONS or file_name.startswith("."):
                    continue
                
                rel_file_path = file_p.relative_to(base_dir).as_posix()
                try:
                    file_size = file_p.stat().st_size
                except Exception:
                    file_size = 0
                
                # Estimate line count for small/medium text files
                line_count = None
                if file_size < 1_000_000 and not is_binary_file(file_p):
                    try:
                        with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = sum(1 for _ in f)
                    except Exception:
                        pass
                        
                file_list.append({
                    "path": rel_file_path,
                    "size": file_size,
                    "line_count": line_count
                })
                
                if len(file_list) >= max_files:
                    break
            if len(file_list) >= max_files:
                break
                
        return {
            "success": True,
            "subpath": subpath or "/",
            "total_files": len(file_list),
            "directories": sorted(dir_list)[:100],
            "files": file_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "files": [],
            "directories": []
        }

def search_code(
    repo_path: str,
    query: str,
    max_results: int = 40,
    file_extension: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for a text string or regex pattern across source code files in the repository.
    Returns matching file paths, line numbers, and line contents.
    
    Args:
        repo_path: Path to the root repository folder.
        query: Search term or regex pattern.
        max_results: Maximum number of matches to return (default 40).
        file_extension: Optional filter (e.g. '.js', '.py', '.ts').
    """
    try:
        base_dir = safe_resolve_repo_path(repo_path)
        matches: List[Dict[str, Any]] = []
        files_searched = 0
        
        # Prepare regex (case-insensitive)
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            # If query is not a valid regex, escape it and search literally
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            
            for file_name in files:
                file_p = Path(root) / file_name
                ext = file_p.suffix.lower()
                
                if ext in IGNORE_EXTENSIONS or file_name.startswith("."):
                    continue
                if file_extension and ext != file_extension.lower():
                    continue
                # Skip large files (> 2MB)
                try:
                    if file_p.stat().st_size > 2_000_000:
                        continue
                except Exception:
                    continue
                    
                if is_binary_file(file_p):
                    continue
                    
                files_searched += 1
                rel_path = file_p.relative_to(base_dir).as_posix()
                
                try:
                    with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, start=1):
                            if pattern.search(line):
                                matches.append({
                                    "file_path": rel_path,
                                    "line_number": line_idx,
                                    "line_content": line.rstrip()
                                })
                                if len(matches) >= max_results:
                                    break
                except Exception:
                    continue
                    
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break
                
        return {
            "success": True,
            "query": query,
            "total_matches": len(matches),
            "files_searched": files_searched,
            "matches": matches
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "matches": []
        }

def read_file(
    repo_path: str,
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read content of a file within the repository, returning lines with 1-based line numbers.
    Safely enforces repository sandboxing and checks for binary files.
    
    Args:
        repo_path: Path to the root repository folder.
        file_path: Relative file path within the repository.
        start_line: Starting line number (1-based, inclusive).
        end_line: Ending line number (1-based, inclusive). If None, reads up to 250 lines from start_line.
    """
    try:
        resolved_file = safe_resolve_repo_path(repo_path, file_path)
        
        if not resolved_file.is_file():
            return {
                "success": False,
                "file_path": file_path,
                "error": f"File not found: '{file_path}'"
            }
            
        if is_binary_file(resolved_file):
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Cannot read binary file '{file_path}'"
            }
            
        # Default window: up to 250 lines to prevent token blowup
        if end_line is None:
            end_line = start_line + 250
            
        start_line = max(1, start_line)
        end_line = max(start_line, end_line)
        
        formatted_lines = []
        raw_lines = []
        total_lines = 0
        
        with open(resolved_file, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                total_lines = idx
                if start_line <= idx <= end_line:
                    clean_line = line.rstrip("\r\n")
                    formatted_lines.append(f"{idx:4d} | {clean_line}")
                    raw_lines.append({"line_number": idx, "content": clean_line})
                    
        return {
            "success": True,
            "file_path": Path(file_path).as_posix(),
            "start_line": start_line,
            "end_line": min(end_line, total_lines),
            "total_lines": total_lines,
            "content": "\n".join(formatted_lines),
            "lines": raw_lines
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e)
        }

def get_dependencies(repo_path: str) -> Dict[str, Any]:
    """
    Analyze repository configuration files to detect dependencies, libraries, and frameworks.
    Supports Python (requirements.txt, pyproject.toml), Node.js (package.json),
    Java (pom.xml), Go (go.mod), Rust (Cargo.toml), and more.
    """
    try:
        base_dir = safe_resolve_repo_path(repo_path)
        all_deps: List[Dict[str, Any]] = []
        files_analyzed: List[str] = []
        ecosystems: set = set()
        
        # Search for known manifest files
        manifest_patterns = [
            ("package.json", parse_package_json, "Node.js/npm"),
            ("requirements.txt", parse_requirements_txt, "Python/pip"),
            ("pyproject.toml", parse_pyproject_toml, "Python"),
            ("pom.xml", parse_pom_xml, "Java/Maven"),
            ("go.mod", parse_go_mod, "Go/GoModules"),
            ("Cargo.toml", parse_cargo_toml, "Rust/Cargo")
        ]
        
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            
            for file_name in files:
                for manifest_name, parser_fn, default_eco in manifest_patterns:
                    if file_name.lower() == manifest_name.lower():
                        file_p = Path(root) / file_name
                        rel_path = file_p.relative_to(base_dir).as_posix()
                        try:
                            with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            parsed = parser_fn(content, rel_path)
                            for d in parsed:
                                ecosystems.add(d.ecosystem)
                                all_deps.append(d.dict())
                            files_analyzed.append(rel_path)
                        except Exception:
                            continue
                            
        return {
            "success": True,
            "ecosystems_detected": sorted(list(ecosystems)),
            "files_analyzed": files_analyzed,
            "total_dependencies": len(all_deps),
            "dependencies": all_deps
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ecosystems_detected": [],
            "files_analyzed": [],
            "dependencies": []
        }

def read_documentation(repo_path: str) -> Dict[str, Any]:
    """
    Scan for documentation files (README, ARCHITECTURE, CONTRIBUTING, docs/) in the repository.
    Returns list of discovered docs and content of the primary README.
    """
    try:
        base_dir = safe_resolve_repo_path(repo_path)
        doc_files = []
        primary_readme_content = None
        primary_readme_path = None
        
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file_name in files:
                lower = file_name.lower()
                if lower.endswith(".md") or lower.endswith(".rst") or lower.endswith(".txt"):
                    file_p = Path(root) / file_name
                    rel_path = file_p.relative_to(base_dir).as_posix()
                    doc_files.append(rel_path)
                    
                    if "readme" in lower and primary_readme_content is None:
                        try:
                            with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                                primary_readme_content = f.read(5000) # first 5000 chars
                                primary_readme_path = rel_path
                        except Exception:
                            pass
                            
        return {
            "success": True,
            "documentation_files": doc_files,
            "primary_readme_path": primary_readme_path,
            "readme_preview": primary_readme_content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "documentation_files": []
        }
