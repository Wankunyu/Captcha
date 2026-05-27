#!/usr/bin/env python3
"""Build a clean, submission-facing source artifact from tracked files."""

from __future__ import annotations

import argparse
import fnmatch
import io
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ARCHIVE = "dist/cognition-usenixsec26-artifact.tar.gz"
DEFAULT_PREFIX = "cognition-usenixsec26-artifact"
ARCHIVE_MANIFEST = "artifact_manifest.json"

EXCLUDE_PATTERNS = (
    ".git",
    ".git/**",
    ".gitattributes.lock",
    ".planning",
    ".planning/**",
    ".codex",
    ".codex/**",
    ".claude",
    ".claude/**",
    "AGENTS.md",
    "CLAUDE.md",
    "secrets.yaml",
    "secrets.local.yaml",
    "*.secret.yaml",
    ".env",
    ".env.*",
    ".venv",
    ".venv/**",
    "env",
    "env/**",
    "__pycache__",
    "__pycache__/**",
    "*/__pycache__/**",
    ".pytest_cache",
    ".pytest_cache/**",
    ".ruff_cache",
    ".ruff_cache/**",
    ".ipynb_checkpoints",
    ".ipynb_checkpoints/**",
    "*/.ipynb_checkpoints/**",
    ".DS_Store",
    "**/.DS_Store",
    "dist",
    "dist/**",
    "artifact_dist",
    "artifact_dist/**",
    "*.tar.gz",
    "*.zip",
    "results/local_runs/**/collect-*.background.log",
    "results/local_runs/**/*.pid",
    "results/local_runs/**/*.watch.log",
    "results/local_runs/**/pause_after_*",
    "results/local_runs/**/run-*.sh",
    "results/local_runs/local-*",
    "results/local_runs/local-*/**",
)


def _normalized(path: str | Path) -> str:
    normalized = Path(path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def is_excluded(path: str | Path, patterns: tuple[str, ...] = EXCLUDE_PATTERNS) -> bool:
    normalized = _normalized(path)
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        entry.decode("utf-8") for entry in completed.stdout.split(b"\0") if entry
    ]


def package_files(root: Path) -> list[str]:
    return [
        path for path in tracked_files(root) if not is_excluded(path) and (root / path).is_file()
    ]


def build_archive(root: Path, output_path: Path, prefix: str) -> tuple[Path, int]:
    files = package_files(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as archive:
        for relative_path in files:
            archive.add(
                root / relative_path,
                arcname=f"{prefix}/{relative_path}",
                recursive=False,
            )
        manifest_payload = {
            "schema_version": "cognition.artifact_package_manifest.v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "file_count": len(files),
            "included_files": files,
            "excluded_patterns": list(EXCLUDE_PATTERNS),
        }
        manifest_bytes = json.dumps(manifest_payload, indent=2).encode("utf-8") + b"\n"
        manifest_info = tarfile.TarInfo(f"{prefix}/{ARCHIVE_MANIFEST}")
        manifest_info.size = len(manifest_bytes)
        archive.addfile(manifest_info, io.BytesIO(manifest_bytes))
    return output_path, len(files)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a clean artifact archive from git-tracked repository files."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root; defaults to current directory.",
    )
    parser.add_argument("--output", default=DEFAULT_ARCHIVE, help="Output .tar.gz path.")
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help="Archive top-level directory name.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List included files without writing an archive.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()

    if args.list:
        for relative_path in package_files(root):
            print(relative_path)
        return 0

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    archive_path, file_count = build_archive(root, output_path, args.prefix)
    print(f"Wrote {archive_path} with {file_count} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
