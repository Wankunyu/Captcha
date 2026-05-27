#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Losslessly compress few-shot image assets while keeping pixel dimensions unchanged.

Workflow:
1. Read all image paths from few_shot_image_manifest.json.
2. Use zopflipng for PNG and jpegtran for JPEG to perform lossless optimisation.
3. Replace originals only when the compressed file is smaller and dimensions match,
   then emit a JSON summary report.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

from PIL import Image


PNG_EXTS = {".png"}
JPEG_EXTS = {".jpg", ".jpeg", ".jpe", ".jfif"}


@dataclass
class CompressionResult:
    path: Path
    original_size: int
    new_size: int
    width: int
    height: int
    changed: bool
    tool: str
    message: str = ""

    @property
    def bytes_saved(self) -> int:
        return self.original_size - self.new_size

    @property
    def ratio(self) -> float:
        if self.original_size == 0:
            return 0.0
        return 1.0 - self.new_size / self.original_size


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def compress_png(path: Path, tmp_dir: Path) -> Tuple[bool, Path, str]:
    """Compress a PNG using zopflipng. Returns (success, output_path, message)."""
    output_path = tmp_dir / path.name
    cmd = [
        "zopflipng",
        "-m",
        "--keepchunks=bKGD,cHRM,gAMA,iCCP,sRGB",
        str(path),
        str(output_path),
    ]
    code, out, err = run_command(cmd)
    message = (out + err).strip()
    if code != 0 or not output_path.exists():
        return False, output_path, message
    return True, output_path, message


def compress_jpeg(path: Path, tmp_dir: Path) -> Tuple[bool, Path, str]:
    """Losslessly optimise a JPEG using jpegtran."""
    output_path = tmp_dir / path.name
    cmd = [
        "jpegtran",
        "-copy",
        "none",
        "-optimize",
        "-progressive",
        "-outfile",
        str(output_path),
        str(path),
    ]
    code, out, err = run_command(cmd)
    message = (out + err).strip()
    if code != 0 or not output_path.exists():
        return False, output_path, message
    return True, output_path, message


def ensure_dimensions(path: Path, expected_size: Tuple[int, int]) -> Tuple[int, int]:
    """Return image dimensions and assert they match expectation."""
    with Image.open(path) as img:
        size = img.size
    if expected_size and size != expected_size:
        raise RuntimeError(
            f"Image dimensions changed for {path}: {size} != {expected_size}"
        )
    return size


def load_manifest(manifest_path: Path) -> List[Path]:
    """Load image list from manifest file."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    images = manifest.get("images", [])
    if not images:
        raise ValueError("Manifest does not contain an 'images' list.")
    return [Path(p) for p in images]


def compress_images(image_paths: Iterable[Path]) -> List[CompressionResult]:
    results: List[CompressionResult] = []
    for path in image_paths:
        if not path.exists():
            results.append(
                CompressionResult(
                    path=path,
                    original_size=0,
                    new_size=0,
                    width=0,
                    height=0,
                    changed=False,
                    tool="n/a",
                    message="missing",
                )
            )
            continue

        suffix = path.suffix.lower()
        if suffix in PNG_EXTS:
            handler: Callable[[Path, Path], Tuple[bool, Path, str]] = compress_png
            tool = "zopflipng"
        elif suffix in JPEG_EXTS:
            handler = compress_jpeg
            tool = "jpegtran"
        else:
            results.append(
                CompressionResult(
                    path=path,
                    original_size=path.stat().st_size,
                    new_size=path.stat().st_size,
                    width=0,
                    height=0,
                    changed=False,
                    tool="skip",
                    message=f"unsupported extension: {suffix}",
                )
            )
            continue

        original_size = path.stat().st_size
        original_dims = ensure_dimensions(path, expected_size=())

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            success, output_path, message = handler(path, tmp_dir)
            if not success:
                results.append(
                    CompressionResult(
                        path=path,
                        original_size=original_size,
                        new_size=original_size,
                        width=original_dims[0],
                        height=original_dims[1],
                        changed=False,
                        tool=tool,
                        message=f"compress failed: {message}",
                    )
                )
                continue

            new_size = output_path.stat().st_size
            if new_size < original_size:
                # Replace original file
                output_path.replace(path)
                new_dims = ensure_dimensions(path, expected_size=original_dims)
                results.append(
                    CompressionResult(
                        path=path,
                        original_size=original_size,
                        new_size=new_size,
                        width=new_dims[0],
                        height=new_dims[1],
                        changed=True,
                        tool=tool,
                        message=message,
                    )
                )
            else:
                results.append(
                    CompressionResult(
                        path=path,
                        original_size=original_size,
                        new_size=original_size,
                        width=original_dims[0],
                        height=original_dims[1],
                        changed=False,
                        tool=tool,
                        message="no gain",
                    )
                )
    return results


def summarise(results: List[CompressionResult]) -> Dict[str, str]:
    total = len(results)
    changed = [r for r in results if r.changed]
    bytes_saved = sum(r.bytes_saved for r in changed)
    png_changed = sum(1 for r in changed if r.tool == "zopflipng")
    jpg_changed = sum(1 for r in changed if r.tool == "jpegtran")
    return {
        "total_images": str(total),
        "compressed_images": str(len(changed)),
        "png_compressed": str(png_changed),
        "jpeg_compressed": str(jpg_changed),
        "bytes_saved": str(bytes_saved),
        "megabytes_saved": f"{bytes_saved / (1024 * 1024):.2f}",
    }


def main(manifest_path: str = "few_shot_image_manifest.json") -> None:
    base_dir = Path(".")
    image_paths = load_manifest(base_dir / manifest_path)
    results = compress_images(image_paths)

    summary = summarise(results)
    report = {
        "summary": summary,
        "results": [
            {
                "path": str(r.path),
                "original_size": r.original_size,
                "new_size": r.new_size,
                "bytes_saved": r.bytes_saved,
                "width": r.width,
                "height": r.height,
                "tool": r.tool,
                "changed": r.changed,
                "message": r.message,
            }
            for r in results
        ],
    }

    report_path = base_dir / "few_shot_image_compression_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("Compression completed.")
    print(f"Processed {summary['total_images']} images.")
    print(f"Compressed {summary['compressed_images']} images.")
    print(
        f"Total bytes saved: {summary['bytes_saved']} (~{summary['megabytes_saved']} MB)."
    )
    print(f"Detailed report: {report_path}")


if __name__ == "__main__":
    main()
