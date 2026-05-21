from __future__ import annotations

# ruff: noqa: E501

import io
import hashlib
import json
import re
import struct
import time
import urllib.request
import zlib
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SIDECAR_ROOT = ROOT / "expanded_captcha_data" / "phase04_2"
CANDIDATES_ROOT = SIDECAR_ROOT / "candidates"
TODAY = "2026-05-21"

OCW_REPO = "OpenCaptchaWorld/Open_CaptchaWorld"
NEXTGEN_REPO = "YaxinLuo/NextGen-CAPTCHAs"
VIPER_ZIP_URL = "https://zenodo.org/records/18191465/files/VIPER_code.zip?download=1"
VIPER_CD_CACHE = Path("/tmp/viper_cd.bin")

IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
OCW_HARD_TYPES = ("Dice_Count", "Click_Order", "Patch_Select", "Geometry_Click")
TARGET_TASK_ORDER = (
    "Dice_Count",
    "Click_Order",
    "Patch_Select",
    "Geometry_Click",
    "Symbol_Count",
    "Relation_Match",
    "Hole_Counting",
)


def _urlopen(url: str, *, headers: dict[str, str] | None = None, timeout: int = 90) -> bytes:
    request = urllib.request.Request(url, headers=headers or {})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network retry guard
            last_error = exc
            if attempt == 3:
                break
            time.sleep(1 + attempt)
    raise RuntimeError(f"download failed: {url}") from last_error


def _download_text(url: str) -> str:
    return _urlopen(url).decode("utf-8")


def _download_binary(url: str) -> bytes:
    return _urlopen(url)


def _range_bytes(url: str, start: int, end: int) -> bytes:
    return _urlopen(url, headers={"Range": f"bytes={start}-{end}"}, timeout=90)


def _hf_raw(repo: str, path: str) -> str:
    return f"https://huggingface.co/datasets/{repo}/resolve/main/{path}?download=true"


def _hf_tree(repo: str, path: str) -> str:
    return f"https://huggingface.co/api/datasets/{repo}/tree/main/{path}"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _clean_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for child in value.values():
            strings.extend(_iter_strings(child))
        return strings
    if isinstance(value, list):
        strings = []
        for child in value:
            strings.extend(_iter_strings(child))
        return strings
    return []


def _referenced_image_files(ground_truth: dict[str, Any]) -> list[str]:
    referenced: set[str] = set()
    for puzzle_id, entry in ground_truth.items():
        if isinstance(puzzle_id, str) and Path(puzzle_id).suffix.lower() in IMAGE_SUFFIXES:
            referenced.add(puzzle_id)
        for text in _iter_strings(entry):
            if Path(text).suffix.lower() in IMAGE_SUFFIXES:
                referenced.add(text)
    return sorted(referenced)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_hf_file(repo: str, source_path: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        return
    destination.write_bytes(_download_binary(_hf_raw(repo, source_path)))


def _stage_ocw_latest_additions(task_type: str) -> dict[str, Any]:
    source_dir = CANDIDATES_ROOT / f"OpenCaptchaWorld_{task_type}_latest_additions"
    _clean_dir(source_dir)

    latest_gt = json.loads(
        _download_text(_hf_raw(OCW_REPO, f"captcha_data/{task_type}/ground_truth.json"))
    )
    local_gt = _read_json(ROOT / "captcha_data" / task_type / "ground_truth.json")

    # The local ground truth has been manually cleaned. For any overlapping puzzle id,
    # keep the local value and do not stage the latest source row.
    new_keys = [key for key in latest_gt if key not in local_gt]
    new_gt = {key: latest_gt[key] for key in new_keys}

    for relative_path in _referenced_image_files(new_gt):
        _download_hf_file(
            OCW_REPO,
            f"captcha_data/{task_type}/{relative_path}",
            source_dir / relative_path,
        )
    local_image_hash_paths: dict[str, list[str]] = {}
    for path in (ROOT / "captcha_data" / task_type).iterdir():
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            local_image_hash_paths.setdefault(_sha256(path), []).append(
                path.relative_to(ROOT).as_posix()
            )
    staged_keys: list[str] = []
    exact_hash_duplicate_keys: list[str] = []
    exact_hash_duplicate_paths_by_key: dict[str, list[str]] = {}
    for key in new_keys:
        staged_image = source_dir / key
        if not staged_image.is_file():
            continue
        staged_keys.append(key)
        local_match_paths = local_image_hash_paths.get(_sha256(staged_image), [])
        if local_match_paths:
            exact_hash_duplicate_keys.append(key)
            exact_hash_duplicate_paths_by_key[key] = local_match_paths

    staged_gt = {key: latest_gt[key] for key in staged_keys}
    _write_json(source_dir / "ground_truth.json", staged_gt)

    candidate_image_paths = [
        (source_dir / key).relative_to(ROOT).as_posix()
        for key in staged_keys
        if (source_dir / key).is_file()
    ]
    increment = len(staged_keys)
    local_count = len(local_gt)
    latest_count = len(latest_gt)
    increase_percent = round((increment / local_count) * 100, 2) if local_count else None

    return {
        "candidate_id": f"phase042-ocw-{task_type.lower().replace('_', '-')}-latest-additions",
        "task_type": task_type,
        "source_kind": "open_source_dataset",
        "source_priority_rank": 1,
        "evidence_role": "preferred_direct_evidence",
        "sample_count_target": increment,
        "candidate_status": "staged_real_external_latest_additions",
        "include_in_candidate_manifest": bool(candidate_image_paths),
        "source_path": source_dir.relative_to(ROOT).as_posix(),
        "candidate_image_paths": candidate_image_paths,
        "source_citation": (
            f"OpenCaptchaWorld/Open_CaptchaWorld Hugging Face dataset, "
            f"captcha_data/{task_type}, main branch, accessed {TODAY}."
        ),
        "source_license": "Apache-2.0 (Hugging Face dataset card).",
        "source_provenance_notes": (
            f"Only latest OpenCaptchaWorld {task_type} puzzle ids absent from the "
            f"local cleaned captcha_data/{task_type}/ground_truth.json are staged."
        ),
        "label_format": "OpenCaptchaWorld ground_truth.json task-specific labels",
        "metadata_alignment_notes": (
            f"Overlapping puzzle ids keep the local cleaned ground truth. "
            f"This staged slice contains {increment} puzzle ids absent from the local "
            f"cleaned ground truth. Exact local image hash matches are retained because "
            f"those puzzle ids were not used in the cleaned ground truth."
        ),
        "answer_format_normalization": (
            "Preserves source ground truth only for newly introduced puzzle ids; "
            "does not overwrite local cleaned labels."
        ),
        "compatibility_status": "ready_for_static_pipeline",
        "limitation_notes": "Incremental latest-addition slice, not a full replacement of the legacy local task type.",
        "adaptive_eligible": True,
        "static_compatibility_notes": "Offline static images with existing task-specific evaluator contract.",
        "increment_from_local_legacy_count": increment,
        "key_new_count": len(new_keys),
        "key_new_count_before_sha_filter": len(new_keys),
        "exact_hash_duplicate_warning_count": len(exact_hash_duplicate_keys),
        "exact_hash_duplicate_warning_keys": exact_hash_duplicate_keys,
        "exact_hash_duplicate_warning_paths_by_key": exact_hash_duplicate_paths_by_key,
        "exact_hash_duplicate_excluded_count": 0,
        "exact_hash_duplicate_excluded_keys": [],
        "local_legacy_count": local_count,
        "latest_source_count": latest_count,
        "dataset_increase_percent_vs_local_legacy": increase_percent,
    }


def _nextgen_tree(category: str) -> list[dict[str, Any]]:
    return json.loads(_download_text(_hf_tree(NEXTGEN_REPO, f"captcha_data/{category}")))


def _nextgen_puzzle_name(index: int, available_files: set[str]) -> str:
    for width in (3, 4):
        name = f"puzzle_{index:0{width}d}.png"
        if name in available_files:
            return name
    raise FileNotFoundError(f"NextGen puzzle image not found for index {index}")


def _stage_nextgen_symbol_count(limit: int = 30) -> dict[str, Any]:
    task_type = "Symbol_Count"
    category = "Occluded_Pattern_Counting"
    source_dir = CANDIDATES_ROOT / "NextGen_Occluded_Pattern_Counting_as_Symbol_Count"
    _clean_dir(source_dir)

    source_gt = json.loads(
        _download_text(_hf_raw(NEXTGEN_REPO, f"captcha_data/{category}/ground_truth.json"))
    )
    available = {
        Path(item["path"]).name
        for item in _nextgen_tree(category)
        if item.get("type") == "file"
    }
    selected_items = list(source_gt.items())[: min(limit, len(source_gt))]

    output_gt: dict[str, Any] = {}
    candidate_image_paths: list[str] = []
    response_schema = '{"answer_type":"number","value":N}'
    for puzzle_id, entry in selected_items:
        match = re.search(r"(\d+)$", puzzle_id)
        if not match:
            raise ValueError(f"cannot derive puzzle index from {puzzle_id}")
        index = int(match.group(1))
        source_image = _nextgen_puzzle_name(index, available)
        destination_image = f"occluded_pattern_counting_{index:04d}.png"
        _download_hf_file(
            NEXTGEN_REPO,
            f"captcha_data/{category}/{source_image}",
            source_dir / destination_image,
        )

        metadata = entry.get("metadata") or {}
        color = str(metadata.get("target1_color", "")).strip()
        shape = str(metadata.get("target1_shape", "")).strip()
        count = int(metadata["target1_count"])
        plural_shape = shape if shape.endswith("s") else f"{shape}s"
        output_gt[destination_image] = {
            "image": destination_image,
            "prompt": (
                f"Count only the {color} {plural_shape} under the grey overlay. "
                f"Return JSON {response_schema}."
            ),
            "count": count,
            "source_category": category,
            "source_puzzle_id": puzzle_id,
            "source_answer": entry.get("answer"),
            "normalization": (
                "Single-target Symbol_Count derived from metadata.target1_count; "
                "the original paired-count target2 is ignored for evaluator compatibility."
            ),
            "metadata": metadata,
        }
        candidate_image_paths.append((source_dir / destination_image).relative_to(ROOT).as_posix())

    _write_json(source_dir / "ground_truth.json", output_gt)
    return {
        "candidate_id": "phase042-nextgen-occluded-pattern-counting-as-symbol-count",
        "task_type": task_type,
        "source_kind": "open_source_dataset",
        "source_priority_rank": 1,
        "evidence_role": "preferred_direct_evidence",
        "sample_count_target": len(selected_items),
        "candidate_status": "staged_real_external_normalized",
        "source_path": source_dir.relative_to(ROOT).as_posix(),
        "candidate_image_paths": candidate_image_paths,
        "source_citation": (
            f"YaxinLuo/NextGen-CAPTCHAs Hugging Face dataset and "
            f"MetaAgentX/NextGen-CAPTCHAs GitHub repository, captcha_data/{category}, "
            f"accessed {TODAY}."
        ),
        "source_license": "Apache-2.0 (Hugging Face dataset card); MIT license observed in GitHub repository.",
        "source_provenance_notes": (
            "Real external NextGen-CAPTCHAs occluded-pattern counting samples "
            "normalized into the existing single-integer Symbol_Count contract."
        ),
        "label_format": "single integer count derived from NextGen metadata.target1_count",
        "metadata_alignment_notes": (
            "Each original paired-count puzzle is converted to a single target by "
            "retaining target1 color, shape, and count."
        ),
        "answer_format_normalization": "Original count1,count2 answer normalized to one integer count for target1 only.",
        "compatibility_status": "ready_for_static_pipeline",
        "limitation_notes": "Single-target normalization is a conservative subset of the original paired-count NextGen task.",
        "adaptive_eligible": True,
        "static_compatibility_notes": "Offline static image with numeric ground truth.",
        "source_category": category,
        "source_category_count": len(source_gt),
    }


def _stage_nextgen_hole_counting(limit: int = 30) -> dict[str, Any]:
    task_type = "Hole_Counting"
    category = "Hole_Counting"
    source_dir = CANDIDATES_ROOT / "NextGen_Hole_Counting"
    _clean_dir(source_dir)

    source_gt = json.loads(
        _download_text(_hf_raw(NEXTGEN_REPO, f"captcha_data/{category}/ground_truth.json"))
    )
    available = {
        Path(item["path"]).name
        for item in _nextgen_tree(category)
        if item.get("type") == "file"
    }
    selected_items = list(source_gt.items())[: min(limit, len(source_gt))]

    output_gt: dict[str, Any] = {}
    candidate_image_paths: list[str] = []
    for puzzle_id, entry in selected_items:
        match = re.search(r"(\d+)$", puzzle_id)
        if not match:
            raise ValueError(f"cannot derive puzzle index from {puzzle_id}")
        index = int(match.group(1))
        destination_image = f"hole_counting_{index:04d}.png"
        cells = entry.get("cells") or []
        grid_size = entry.get("grid_size", [4, 4])
        if not isinstance(cells, list) or len(cells) != int(grid_size[0]) * int(grid_size[1]):
            raise ValueError(f"unexpected Hole_Counting cell list for {puzzle_id}")
        cell_images: list[Image.Image] = []
        for cell_id in cells:
            cell_file = f"{cell_id}.png"
            if cell_file not in available:
                raise FileNotFoundError(f"NextGen Hole_Counting cell image not found: {cell_file}")
            cell_path = source_dir / "_cells" / cell_file
            _download_hf_file(
                NEXTGEN_REPO,
                f"captcha_data/{category}/{cell_file}",
                cell_path,
            )
            cell_images.append(Image.open(cell_path).convert("RGB"))
        cell_width, cell_height = cell_images[0].size
        rows, cols = int(grid_size[0]), int(grid_size[1])
        composite = Image.new("RGB", (cols * cell_width, rows * cell_height), "white")
        for cell_index, cell_image in enumerate(cell_images):
            row, col = divmod(cell_index, cols)
            composite.paste(cell_image, (col * cell_width, row * cell_height))
            cell_image.close()
        composite.save(source_dir / destination_image)
        answer = entry.get("answer") or []
        output_gt[destination_image] = {
            "image": destination_image,
            "prompt": entry.get("prompt", ""),
            "target_holes": entry.get("target_holes"),
            "target_object": f"tiles where the big shape has exactly {entry.get('target_holes')} holes",
            "grid_size": grid_size,
            "correct_patches": answer,
            "answer": answer,
            "input_type": entry.get("input_type", "grid_select"),
            "source_category": category,
            "source_puzzle_id": puzzle_id,
            "normalization": (
                "Composite grid image reconstructed from NextGen cell assets in the "
                "source ground_truth cell order."
            ),
            "metadata": {
                key: value
                for key, value in entry.items()
                if key not in {"prompt", "answer", "cells"}
            },
        }
        candidate_image_paths.append((source_dir / destination_image).relative_to(ROOT).as_posix())

    _write_json(source_dir / "ground_truth.json", output_gt)
    return {
        "candidate_id": "phase042-nextgen-hole-counting",
        "task_type": task_type,
        "source_kind": "open_source_dataset",
        "source_priority_rank": 1,
        "evidence_role": "preferred_direct_evidence",
        "sample_count_target": len(selected_items),
        "candidate_status": "staged_real_external_new_category",
        "source_path": source_dir.relative_to(ROOT).as_posix(),
        "candidate_image_paths": candidate_image_paths,
        "source_citation": (
            f"YaxinLuo/NextGen-CAPTCHAs Hugging Face dataset and "
            f"MetaAgentX/NextGen-CAPTCHAs GitHub repository, captcha_data/{category}, "
            f"accessed {TODAY}."
        ),
        "source_license": "Apache-2.0 (Hugging Face dataset card); MIT license observed in GitHub repository.",
        "source_provenance_notes": (
            "Real external NextGen-CAPTCHAs hole-counting grid-select samples "
            "added as an additional Phase 04.2 new category per user direction."
        ),
        "evidence_origin": "new_category",
        "slice_type": "new_category",
        "task_family": "Counting",
        "label_format": "grid-select indices",
        "metadata_alignment_notes": "NextGen answer indices are normalized to correct_patches for Patch_Select-style scoring.",
        "answer_format_normalization": "Preserves grid-select answer indices as multi_select indices.",
        "compatibility_status": "ready_for_static_pipeline",
        "limitation_notes": "Additional user-requested category beyond the original Phase 04.2 target set.",
        "adaptive_eligible": True,
        "static_compatibility_notes": "Offline static grid-select image with row-major answer indices.",
        "source_category": category,
        "source_category_count": len(source_gt),
    }


def _zip_size(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return int(response.headers["Content-Length"])


def _ensure_viper_cd() -> Path:
    if VIPER_CD_CACHE.is_file() and VIPER_CD_CACHE.stat().st_size > 0:
        return VIPER_CD_CACHE

    size = _zip_size(VIPER_ZIP_URL)
    tail_start = max(0, size - 1024 * 1024)
    tail = _range_bytes(VIPER_ZIP_URL, tail_start, size - 1)
    eocd_sig = b"PK\x05\x06"
    eocd_offset = tail.rfind(eocd_sig)
    if eocd_offset < 0:
        raise ValueError("ZIP EOCD not found in VIPER tail range")
    eocd = tail[eocd_offset : eocd_offset + 22]
    fields = struct.unpack("<4s4H2IH", eocd)
    cd_size = fields[5]
    cd_offset = fields[6]
    cd = _range_bytes(VIPER_ZIP_URL, cd_offset, cd_offset + cd_size - 1)
    VIPER_CD_CACHE.write_bytes(cd)
    return VIPER_CD_CACHE


def _parse_zip_cd(cd_path: Path) -> dict[str, tuple[int, int, int, int]]:
    cd = cd_path.read_bytes()
    pos = 0
    entries: dict[str, tuple[int, int, int, int]] = {}
    while pos < len(cd):
        if cd[pos : pos + 4] != b"PK\x01\x02":
            raise ValueError(f"bad central directory signature at {pos}")
        fields = struct.unpack_from("<4s6H3I5H2I", cd, pos)
        _, _, _, _, method, _, _, _, csize, usize, nlen, xlen, clen, _, _, _, lhoff = fields
        name = cd[pos + 46 : pos + 46 + nlen].decode("utf-8", "replace")
        entries[name] = (method, csize, usize, lhoff)
        pos += 46 + nlen + xlen + clen
    return entries


def _extract_zip_entry_remote(
    entries: dict[str, tuple[int, int, int, int]],
    name: str,
) -> bytes:
    method, csize, usize, lhoff = entries[name]
    block = _range_bytes(
        VIPER_ZIP_URL,
        lhoff,
        lhoff + 30 + len(name.encode("utf-8")) + 2048 + csize,
    )
    if block[:4] != b"PK\x03\x04":
        raise ValueError(f"bad local header for {name}")
    _, _, _, local_method, _, _, _, _, _, nlen, xlen = struct.unpack_from("<4s5H3I2H", block, 0)
    if local_method != method:
        raise ValueError(f"ZIP method mismatch for {name}")
    start = 30 + nlen + xlen
    compressed = block[start : start + csize]
    if len(compressed) != csize:
        raise ValueError(f"incomplete compressed data for {name}")
    if method == 8:
        output = zlib.decompress(compressed, -15)
    elif method == 0:
        output = compressed
    else:
        raise ValueError(f"unsupported ZIP method {method} for {name}")
    if len(output) != usize:
        raise ValueError(f"uncompressed size mismatch for {name}")
    return output


def _load_viper_geetest_metadata(
    entries: dict[str, tuple[int, int, int, int]]
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    questions = json.loads(
        _extract_zip_entry_remote(
            entries,
            "VIPER_code/data_process/Geetest/ques_test.json",
        ).decode("utf-8")
    )
    detections = json.loads(
        _extract_zip_entry_remote(
            entries,
            "VIPER_code/data_process/Geetest/detect_test.json",
        ).decode("utf-8")
    )
    return questions, {int(item["image_id"]): item for item in detections}


def _choose_geetest_rows(
    questions: list[dict[str, Any]],
    detection_by_id: dict[int, dict[str, Any]],
    limit: int = 30,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    relation_pattern = re.compile(
        r"front|behind|left|right|same|consistent|correspond|above|below|"
        r"\u524d|\u540e|\u5de6|\u53f3|\u4e00\u6837|\u4e00\u81f4|\u5bf9\u5e94|\u4e0a|\u4e0b",
        re.IGNORECASE,
    )
    chosen: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for question in questions:
        image_id = int(question["id"])
        detection = detection_by_id.get(image_id)
        if detection is None:
            continue
        objects = detection.get("objs") or []
        answer_id = detection.get("ans_id")
        if answer_id is None or not any(obj.get("obj_id") == answer_id for obj in objects):
            continue
        question_text = f"{question.get('en_ques', '')} {question.get('ques', '')}"
        if not relation_pattern.search(question_text):
            continue
        if len(objects) < 3:
            continue
        chosen.append((question, detection))
        if len(chosen) >= limit:
            return chosen
    raise ValueError(f"only selected {len(chosen)} geetest rows")


def _stage_viper_geetest_relation_match(limit: int = 30) -> dict[str, Any]:
    task_type = "Relation_Match"
    source_dir = CANDIDATES_ROOT / "VIPER_geetest_as_Relation_Match"
    _clean_dir(source_dir)

    entries = _parse_zip_cd(_ensure_viper_cd())
    questions, detection_by_id = _load_viper_geetest_metadata(entries)
    selected = _choose_geetest_rows(questions, detection_by_id, limit=limit)

    output_gt: dict[str, Any] = {}
    candidate_image_paths: list[str] = []
    for question, detection in selected:
        image_id = int(question["id"])
        stem = f"{image_id:06d}"
        source_image = f"VIPER_code/dataset/geetest/images/{stem}.jpg"
        scene_name = f"geetest_{stem}_scene.jpg"
        scene_path = source_dir / scene_name
        if scene_path.is_file() and scene_path.stat().st_size > 0:
            scene_bytes = scene_path.read_bytes()
        else:
            scene_bytes = _extract_zip_entry_remote(entries, source_image)
            scene_path.write_bytes(scene_bytes)
        candidate_image_paths.append(scene_path.relative_to(ROOT).as_posix())

        option_images: list[str] = []
        correct_index: int | None = None
        with Image.open(io.BytesIO(scene_bytes)) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
            for option_index, obj in enumerate(detection.get("objs") or []):
                x, y, w, h = [float(value) for value in obj.get("bbox", [0, 0, 0, 0])]
                pad = 2
                left = max(0, int(x) - pad)
                top = max(0, int(y) - pad)
                right = min(width, int(x + w) + pad)
                bottom = min(height, int(y + h) + pad)
                if right <= left or bottom <= top:
                    continue
                crop_name = f"geetest_{stem}_option_{option_index:02d}.jpg"
                rgb.crop((left, top, right, bottom)).save(source_dir / crop_name, quality=95)
                option_images.append(crop_name)
                if obj.get("obj_id") == detection.get("ans_id"):
                    correct_index = len(option_images) - 1
        if correct_index is None:
            raise ValueError(f"answer object not found for geetest {image_id}")

        english_question = str(question.get("en_ques") or "").strip()
        output_gt[f"geetest_{stem}.json"] = {
            "reference_image": scene_name,
            "option_images": option_images,
            "correct_index": correct_index,
            "prompt": (
                "The first image is the full Geetest reference scene. "
                "The option images are candidate object crops indexed 0..N-1. "
                f"Choose the option crop that answers this prompt: {english_question} "
                "Return JSON {\"answer_type\":\"classify\",\"index\":k} with 0-based index only."
            ),
            "source_dataset": "VIPER_code geetest",
            "source_question_id": image_id,
            "source_question_en": english_question,
            "source_md5": question.get("md5", ""),
            "source_ans_id": detection.get("ans_id"),
            "normalization": (
                "Original click-target CAPTCHA converted to offline reference-scene "
                "plus candidate-crop classification for Relation_Match compatibility."
            ),
        }

    _write_json(source_dir / "ground_truth.json", output_gt)
    return {
        "candidate_id": "phase042-viper-geetest-as-relation-match",
        "task_type": task_type,
        "source_kind": "open_source_dataset",
        "source_priority_rank": 1,
        "evidence_role": "preferred_direct_evidence",
        "sample_count_target": len(selected),
        "candidate_status": "staged_real_external_normalized",
        "source_path": source_dir.relative_to(ROOT).as_posix(),
        "candidate_image_paths": candidate_image_paths,
        "source_citation": (
            f"VIPER_code Zenodo record 18191465, DOI 10.5281/zenodo.18191465, "
            f"geetest dataset, accessed {TODAY}."
        ),
        "source_license": "CC-BY-4.0 (Zenodo record).",
        "source_provenance_notes": (
            "Offline geetest image, question, detection, and answer-id metadata extracted "
            "from the VIPER_code Zenodo artifact; no live CAPTCHA service or browser workflow is used."
        ),
        "label_format": "0-based candidate crop index derived from VIPER detect_test ans_id",
        "metadata_alignment_notes": (
            "Original click-target tasks are normalized into reference-scene plus object-crop "
            "options for the existing Relation_Match classify contract."
        ),
        "answer_format_normalization": "VIPER ans_id mapped to correct_index over deterministic object crop ordering.",
        "compatibility_status": "ready_for_static_pipeline",
        "limitation_notes": "Selective relation-rich subset from geetest, not the full 1000-row dataset.",
        "adaptive_eligible": True,
        "static_compatibility_notes": "Offline static scene plus cropped option images; no live endpoint interaction.",
        "source_category": "geetest",
        "source_category_count": 1000,
    }


def _triage_row(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_type": candidate["task_type"],
        "source_kind": candidate["source_kind"],
        "source_priority_rank": candidate["source_priority_rank"],
        "source_citation": candidate["source_citation"],
        "source_license": candidate["source_license"],
        "source_provenance_notes": candidate["source_provenance_notes"],
        "sample_count_target": candidate["sample_count_target"],
        "fallback_reason": "No GPT Image fallback needed; user selected real external data sources on 2026-05-21.",
        "evidence_role": candidate["evidence_role"],
        "license_status": "reviewed_from_source_metadata_before_staging",
        "style_consistency_notes": candidate["static_compatibility_notes"],
        "candidate_path": (
            candidate["candidate_image_paths"][0]
            if candidate["candidate_image_paths"]
            else candidate["source_path"]
        ),
    }


def stage_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_type in OCW_HARD_TYPES:
        rows.append(_stage_ocw_latest_additions(task_type))
    rows.append(_stage_nextgen_symbol_count(limit=30))
    rows.append(_stage_viper_geetest_relation_match(limit=30))
    rows.append(_stage_nextgen_hole_counting(limit=30))
    return sorted(rows, key=lambda row: TARGET_TASK_ORDER.index(row["task_type"]))


def main() -> int:
    rows = stage_sources()
    candidate_rows = [row for row in rows if row.get("include_in_candidate_manifest", True)]
    _write_json(
        SIDECAR_ROOT / "source_triage.json",
        {
            "schema_version": "cognition.revision.phase042.source_triage.v1",
            "generated_at": f"{TODAY}T00:00:00Z",
            "sidecar_root": "expanded_captcha_data/phase04_2",
            "real_external_first": True,
            "sample_selection_rule": (
                "OCW hard-type rows stage only puzzle ids absent from local cleaned ground_truth; "
                "NextGen and VIPER new categories stage approximately 30 samples, or all samples when fewer exist."
            ),
            "target_task_types": list(TARGET_TASK_ORDER),
            "source_priority": [
                "peer_reviewed_paper_dataset",
                "open_source_dataset",
                "gpt_image_open_captchaworld_style",
            ],
            "user_decision": "Use real external OCW/NextGen/VIPER data; do not generate GPT Image fallback instances.",
            "rows": [_triage_row(row) for row in rows],
        },
    )
    _write_json(
        SIDECAR_ROOT / "candidate_manifest.json",
        {
            "schema_version": "cognition.revision.phase042.candidate_manifest.v1",
            "generated_at": f"{TODAY}T00:00:00Z",
            "sidecar_root": "expanded_captcha_data/phase04_2",
            "candidate_root": "expanded_captcha_data/phase04_2/candidates",
            "real_external_first": True,
            "source_priority": [
                "peer_reviewed_paper_dataset",
                "open_source_dataset",
                "gpt_image_open_captchaworld_style",
            ],
            "user_decision": (
                "Use latest OCW hard-type additions, NextGen Occluded_Pattern_Counting as "
                "Symbol_Count, VIPER geetest as Relation_Match, and NextGen Hole_Counting; "
                "no GPT Image instances."
            ),
            "candidate_rows": candidate_rows,
        },
    )
    _write_json(
        SIDECAR_ROOT / "source_download_manifest.json",
        {
            "schema_version": "cognition.revision.phase042.source_download_manifest.v1",
            "generated_at": f"{TODAY}T00:00:00Z",
            "rows": [
                {
                    "candidate_id": row["candidate_id"],
                    "task_type": row["task_type"],
                    "source_path": row["source_path"],
                    "sample_count": len(row["candidate_image_paths"]),
                    "include_in_candidate_manifest": row.get("include_in_candidate_manifest", True),
                    "source_citation": row["source_citation"],
                    "source_license": row["source_license"],
                    "latest_source_count": row.get("latest_source_count", row.get("source_category_count")),
                    "local_legacy_count": row.get("local_legacy_count"),
                    "increment_from_local_legacy_count": row.get("increment_from_local_legacy_count"),
                    "key_new_count": row.get("key_new_count"),
                    "key_new_count_before_sha_filter": row.get("key_new_count_before_sha_filter"),
                    "exact_hash_duplicate_warning_count": row.get("exact_hash_duplicate_warning_count"),
                    "exact_hash_duplicate_warning_keys": row.get("exact_hash_duplicate_warning_keys"),
                    "exact_hash_duplicate_warning_paths_by_key": row.get("exact_hash_duplicate_warning_paths_by_key"),
                    "exact_hash_duplicate_excluded_count": row.get("exact_hash_duplicate_excluded_count"),
                    "exact_hash_duplicate_excluded_keys": row.get("exact_hash_duplicate_excluded_keys"),
                    "dataset_increase_percent_vs_local_legacy": row.get("dataset_increase_percent_vs_local_legacy"),
                }
                for row in rows
            ],
        },
    )
    print(
        json.dumps(
            {
                "candidate_count": len(candidate_rows),
                "download_record_count": len(rows),
                "samples_by_task_type": {
                    row["task_type"]: len(row["candidate_image_paths"])
                    for row in candidate_rows
                },
                "downloaded_or_checked_by_task_type": {
                    row["task_type"]: len(row["candidate_image_paths"])
                    for row in rows
                },
                "source_download_manifest": (
                    "expanded_captcha_data/phase04_2/source_download_manifest.json"
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
