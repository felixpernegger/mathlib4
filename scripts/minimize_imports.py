#!/usr/bin/env python3
"""Remove Lean imports that are not actually needed, verified by compiling.

For every import in every targeted file, tentatively delete the import line and
type-check the file with `lake env lean`. If it still compiles, the removal is
kept; otherwise the line is restored. This is empirical (build-verified), unlike
a purely textual/graph-based redundant-import heuristic.

Files within the target scope are processed in dependency order (files that are
imported by other in-scope files first), and files with only a single import
line are skipped entirely (that import is almost always load-bearing).

Caveat: this only verifies that each *edited* file itself still compiles. It
does not check files outside the target scope that might transitively depend on
a removed import through one of the edited files. Only use this on folders with
no (or already-verified) external importers.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_SEARCH_ROOTS = ["Mathlib", "Archive", "Counterexamples"]


@dataclass(frozen=True)
class ImportLine:
    line_number: int
    module: str
    keep: bool
    all_private: bool


@dataclass
class LeanFile:
    path: Path
    module: str
    imports: list[ImportLine]
    keep_all: bool
    lines: list[str]


def module_name(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).with_suffix("")
    return ".".join(rel.parts)


def path_from_arg(arg: str) -> Path:
    path = Path(arg)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def is_excluded(path: Path) -> bool:
    rel_parts = path.relative_to(REPO_ROOT).parts
    return ".lake" in rel_parts or (rel_parts and rel_parts[0] == "MathlibTest")


def discover_files(args: list[str]) -> list[Path]:
    files: list[Path] = []
    for arg in args:
        root = path_from_arg(arg)
        if not root.exists():
            raise FileNotFoundError(root)
        if root.is_file():
            if root.suffix == ".lean" and not is_excluded(root):
                files.append(root)
            continue
        files.extend(path for path in root.rglob("*.lean") if not is_excluded(path))
    return sorted(set(files))


def strip_line_comment(line: str) -> str:
    return line.split("--", 1)[0]


def parse_import_line(line: str, line_number: int) -> ImportLine | None:
    code = strip_line_comment(line).strip()
    if not code:
        return None
    tokens = code.split()
    i = 0
    while i < len(tokens) and tokens[i] in {"public", "meta"}:
        i += 1
    if i >= len(tokens) or tokens[i] != "import":
        return None
    i += 1
    all_private = False
    if i < len(tokens) and tokens[i] == "all":
        all_private = True
        i += 1
    if i >= len(tokens):
        return None
    module = tokens[i]
    if not module.replace(".", "").replace("_", "").isalnum():
        return None
    return ImportLine(
        line_number=line_number,
        module=module,
        keep="shake: keep" in line,
        all_private=all_private,
    )


def parse_header(lines: list[str]) -> tuple[list[ImportLine], bool]:
    """Parse the leading import block of a Lean file's lines. Reusable on either
    lines read from disk or lines fetched from `git show` for a past revision."""
    imports: list[ImportLine] = []
    keep_all = any("shake: keep-all" in line for line in lines)
    in_block_comment = False
    seen_module = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if in_block_comment:
            if "-/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/-"):
            in_block_comment = "-/" not in stripped
            continue
        if not stripped or stripped.startswith("--"):
            continue
        if stripped == "module":
            seen_module = True
            continue

        imp = parse_import_line(line, line_number)
        if imp is not None:
            imports.append(imp)
            continue

        if seen_module or imports:
            break

    return imports, keep_all


def module_to_path(module: str) -> Path:
    return REPO_ROOT.joinpath(*module.split(".")).with_suffix(".lean")


def parse_file(path: Path) -> LeanFile:
    lines = path.read_text().splitlines(keepends=True)
    imports, keep_all = parse_header(lines)
    return LeanFile(path=path, module=module_name(path), imports=imports, keep_all=keep_all, lines=lines)


def topological_order(files: list[LeanFile]) -> list[LeanFile]:
    by_module = {f.module: f for f in files}
    deps: dict[str, set[str]] = {
        f.module: {imp.module for imp in f.imports if imp.module in by_module} for f in files
    }
    ordered: list[LeanFile] = []
    placed: set[str] = set()
    remaining = set(by_module)
    while remaining:
        ready = sorted(m for m in remaining if deps[m] <= placed)
        if not ready:
            # cycle (shouldn't happen for real Lean imports); break arbitrarily
            ready = sorted(remaining)[:1]
        for m in ready:
            ordered.append(by_module[m])
            placed.add(m)
            remaining.discard(m)
    return ordered


def find_external_importers(target_modules: set[str], target_paths: set[Path]) -> list[str]:
    """Modules of files outside target_paths that directly import one of target_modules."""
    if not target_modules:
        return []

    pattern = re.compile(
        r"^\s*(public\s+|meta\s+)*import\s+(all\s+)?("
        + "|".join(re.escape(m) for m in target_modules)
        + r")\s*(--.*)?$"
    )

    candidates: list[Path] = []
    for root_name in EXTERNAL_SEARCH_ROOTS:
        root = REPO_ROOT / root_name
        if root.exists():
            candidates.extend(root.rglob("*.lean"))

    importers: set[str] = set()
    for path in candidates:
        if path in target_paths or is_excluded(path):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            if pattern.match(line):
                importers.add(module_name(path))
                break

    return sorted(importers)


def verify_importers(modules: list[str]) -> bool:
    print(f"\nVerifying {len(modules)} external importer(s) with `lake build`...")
    result = subprocess.run(["lake", "build", *modules], cwd=REPO_ROOT)
    return result.returncode == 0


def lake_env_lean_ok(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    result = subprocess.run(
        ["lake", "env", "lean", str(rel)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def process_file(lean_file: LeanFile, *, dry_run: bool) -> tuple[int, int]:
    if lean_file.keep_all:
        print(f"{lean_file.path.relative_to(REPO_ROOT)}: skipped (shake: keep-all)")
        return 0, 0
    if len(lean_file.imports) <= 1:
        print(f"{lean_file.path.relative_to(REPO_ROOT)}: skipped (single import)")
        return 0, 0

    candidates = [imp for imp in lean_file.imports if not imp.keep and not imp.all_private]
    lines = list(lean_file.lines)
    removed_line_numbers: set[int] = set()
    removed = 0
    kept = 0

    for imp in candidates:
        trial_lines = [line for idx, line in enumerate(lines, start=1) if idx not in removed_line_numbers | {imp.line_number}]
        lean_file.path.write_text("".join(trial_lines))

        rel = lean_file.path.relative_to(REPO_ROOT)
        if lake_env_lean_ok(lean_file.path):
            removed_line_numbers.add(imp.line_number)
            removed += 1
            print(f"{rel}: removed {imp.module}")
        else:
            kept += 1
            print(f"{rel}: kept {imp.module} (needed)")

    final_lines = [line for idx, line in enumerate(lines, start=1) if idx not in removed_line_numbers]
    if dry_run:
        lean_file.path.write_text("".join(lines))
    else:
        lean_file.path.write_text("".join(final_lines))

    return removed, kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Lean files or directories to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="report only; restore all files to their original state at the end"
    )
    parser.add_argument(
        "--verify-importers",
        action="store_true",
        help=(
            "after processing, find files outside the target scope that directly import a "
            "touched file, and run `lake build` on them as a report-only downstream check. "
            "Does not auto-restore anything on failure."
        ),
    )
    args = parser.parse_args()

    paths = discover_files(args.paths)
    if not paths:
        print("No .lean files found")
        return 0

    files = topological_order([parse_file(p) for p in paths])

    total_removed = 0
    total_kept = 0
    touched_files = 0
    touched_modules: set[str] = set()
    for lean_file in files:
        removed, kept = process_file(lean_file, dry_run=args.dry_run)
        total_removed += removed
        total_kept += kept
        if removed:
            touched_files += 1
            touched_modules.add(lean_file.module)

    print()
    print(f"Files processed: {len(files)}")
    print(f"Files with an import removed: {touched_files}")
    print(f"Imports removed: {total_removed}")
    print(f"Imports kept (needed): {total_kept}")
    if args.dry_run:
        print("(dry run: all files restored to original state)")

    if args.verify_importers and not args.dry_run:
        if not touched_modules:
            print("\nNo files were touched; skipping importer verification.")
        else:
            target_paths = {p.path for p in files}
            importers = find_external_importers(touched_modules, target_paths)
            if not importers:
                print(f"\nNo external files directly import the {len(touched_modules)} touched module(s).")
            else:
                ok = verify_importers(importers)
                print()
                if ok:
                    print(f"OK: all {len(importers)} external importer(s) still build.")
                else:
                    print(
                        f"FAILURE: at least one of {len(importers)} external importer(s) failed to build. "
                        "No changes were auto-restored -- review the `lake build` output above and manually "
                        "restore the offending import(s) in the touched files listed below, or re-run with "
                        "git to inspect the diff."
                    )
                    print("Touched files:")
                    for m in sorted(touched_modules):
                        print(f"  {m}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
