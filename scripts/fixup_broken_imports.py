#!/usr/bin/env python3
"""Fix files broken by minimize_imports.py, restoring the missing import
directly in the file that actually fails to build rather than in the file it
was originally removed from.

What was removed is reconstructed from git (each file's current imports diffed
against `git show HEAD:<path>`), not from any saved log -- this can be re-run
standalone against whatever the working tree currently looks like.

Algorithm per round:
1. Build the whole scope plus the direct external importers of touched files;
   collect the failing targets.
2. For each failing file, gather candidate imports from everywhere in its own
   transitive import closure that lost something (nearest first), add them one
   at a time until it builds, then prune back to the minimal subset that's
   still needed.
3. Repeat until a round makes no more progress.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import minimize_imports as mi  # noqa: E402

REPO_ROOT = mi.REPO_ROOT
MAX_ROUNDS = 20


@dataclass(frozen=True)
class RemovedImport:
    module: str
    prefix: str  # e.g. "public import", "meta import", "import"


def import_prefix(line: str) -> str:
    code = mi.strip_line_comment(line).strip()
    tokens = code.split()
    i = 0
    while i < len(tokens) and tokens[i] in {"public", "meta"}:
        i += 1
    return " ".join(tokens[: i + 1])  # includes the "import" token itself


def original_lines(path: Path) -> list[str] | None:
    rel = path.relative_to(REPO_ROOT)
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.splitlines(keepends=True)


def removed_imports_map(paths: list[Path]) -> dict[str, list[RemovedImport]]:
    result: dict[str, list[RemovedImport]] = {}
    for path in paths:
        orig_lines = original_lines(path)
        if orig_lines is None:
            continue
        orig_imports, _ = mi.parse_header(orig_lines)
        cur_imports, _ = mi.parse_header(path.read_text().splitlines(keepends=True))
        cur_modules = {imp.module for imp in cur_imports}
        removed = [
            RemovedImport(module=imp.module, prefix=import_prefix(orig_lines[imp.line_number - 1]))
            for imp in orig_imports
            if imp.module not in cur_modules
        ]
        if removed:
            result[mi.module_name(path)] = removed
    return result


def transitive_closure(start: str, cache: dict[str, list[str]]) -> list[str]:
    """BFS from `start` (excluded from the result), nearest modules first."""
    order: list[str] = []
    seen = {start}
    frontier = [start]
    while frontier:
        nxt: list[str] = []
        for m in frontier:
            if m not in cache:
                path = mi.module_to_path(m)
                if path.exists() and not mi.is_excluded(path):
                    try:
                        imports, _ = mi.parse_header(path.read_text().splitlines(keepends=True))
                        cache[m] = [imp.module for imp in imports]
                    except (UnicodeDecodeError, OSError):
                        cache[m] = []
                else:
                    cache[m] = []
            for dep in cache[m]:
                if dep not in seen:
                    seen.add(dep)
                    nxt.append(dep)
                    order.append(dep)
        frontier = nxt
    return order


def candidates_for(
    module: str, removed_map: dict[str, list[RemovedImport]], cache: dict[str, list[str]]
) -> list[RemovedImport]:
    chain = [module] + transitive_closure(module, cache)
    seen_modules: set[str] = set()
    out: list[RemovedImport] = []
    for m in chain:
        for ri in removed_map.get(m, []):
            if ri.module not in seen_modules:
                seen_modules.add(ri.module)
                out.append(ri)
    return out


def lake_build_ok(module: str) -> tuple[bool, str]:
    result = subprocess.run(["lake", "build", module], cwd=REPO_ROOT, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def insert_import(path: Path, ri: RemovedImport) -> None:
    lines = path.read_text().splitlines(keepends=True)
    imports, _ = mi.parse_header(lines)
    new_line = f"{ri.prefix} {ri.module}\n"
    same_group = [imp for imp in imports if import_prefix(lines[imp.line_number - 1]) == ri.prefix]
    if same_group:
        insert_after = max(
            (imp.line_number for imp in same_group if imp.module < ri.module), default=None
        )
        insert_at = insert_after if insert_after is not None else min(imp.line_number for imp in same_group) - 1
    elif imports:
        insert_at = max(imp.line_number for imp in imports)
    else:
        raise RuntimeError(f"{path}: no import block found to insert into")
    lines.insert(insert_at, new_line)
    path.write_text("".join(lines))


def remove_import(path: Path, module: str) -> None:
    lines = path.read_text().splitlines(keepends=True)
    imports, _ = mi.parse_header(lines)
    target = next(imp for imp in imports if imp.module == module)
    del lines[target.line_number - 1]
    path.write_text("".join(lines))


def fix_file(module: str, removed_map: dict[str, list[RemovedImport]], cache: dict[str, list[str]]) -> bool:
    path = mi.module_to_path(module)
    pool = candidates_for(module, removed_map, cache)
    if not pool:
        print(f"{module}: no removed-import candidates found in its transitive closure")
        return False

    added: list[RemovedImport] = []
    ok = False
    output = ""
    for ri in pool:
        insert_import(path, ri)
        added.append(ri)
        ok, output = lake_build_ok(module)
        print(f"  try +{ri.module}: {'OK' if ok else 'still failing'}")
        if ok:
            break

    if not ok:
        print(f"{module}: still failing after trying all {len(pool)} candidate(s); last error:")
        print(output[-2000:])
        return False

    for ri in list(added):
        remove_import(path, ri.module)
        still_ok, _ = lake_build_ok(module)
        if still_ok:
            added.remove(ri)
            print(f"  pruned redundant +{ri.module}")
        else:
            insert_import(path, ri)

    print(f"{module}: fixed, added {[ri.module for ri in added]}")
    return True


def detect_failures(scope_paths: list[Path], removed_map: dict[str, list[RemovedImport]]) -> list[str]:
    scope_modules = {mi.module_name(p) for p in scope_paths}
    touched_modules = set(removed_map)
    importers = mi.find_external_importers(touched_modules, set(scope_paths))
    targets = sorted(scope_modules | set(importers))

    result = subprocess.run(["lake", "build", *targets], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        return []
    output = result.stdout + result.stderr
    marker = "Some required targets logged failures:"
    if marker not in output:
        print("lake build failed but no per-target failure list found; full output tail:")
        print(output[-3000:])
        return []
    tail = output.split(marker, 1)[1]
    return [line.strip("- \n") for line in tail.splitlines() if line.strip().startswith("-")]


def main() -> int:
    args = sys.argv[1:]
    detect_only = "--detect-only" in args
    args = [a for a in args if a != "--detect-only"]
    if not args:
        print("usage: fixup_broken_imports.py <folder-or-file> [<more paths>...] [--detect-only]")
        return 1

    scope_paths = mi.discover_files(args)
    removed_map = removed_imports_map(scope_paths)
    if not removed_map:
        print("No removed imports found in this scope (nothing for minimize_imports.py to have touched).")
        return 0
    print(f"{len(removed_map)} file(s) in scope have removed imports (per git diff against HEAD).")

    cache: dict[str, list[str]] = {}

    if detect_only:
        failures = detect_failures(scope_paths, removed_map)
        print(f"\n{len(failures)} failing target(s): {failures}")
        for module in failures:
            pool = candidates_for(module, removed_map, cache)
            print(f"\n{module}: candidate pool (nearest first):")
            for ri in pool:
                print(f"  {ri.prefix} {ri.module}")
        return 0

    for round_no in range(1, MAX_ROUNDS + 1):
        print(f"\n=== round {round_no}: detecting failures ===")
        failures = detect_failures(scope_paths, removed_map)
        if not failures:
            print("Clean build. Done.")
            return 0
        print(f"{len(failures)} failing target(s): {failures}")

        progressed = False
        for module in failures:
            print(f"\nFixing {module}")
            if fix_file(module, removed_map, cache):
                progressed = True
        if not progressed:
            print("\nNo progress this round; giving up. Remaining failures need manual attention:")
            for m in failures:
                print(f"  {m}")
            return 1

    print(f"Exceeded {MAX_ROUNDS} rounds without converging.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
