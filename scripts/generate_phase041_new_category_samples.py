"""Generate prototype Phase 04.1 offline top-up samples for new task categories.

These local scripted samples are not paper-eligible expanded sidecar evidence under
the corrected provenance definition. Use real paper/open-source CAPTCHA samples or
GPT Image Open CaptchaWorld-style generated samples with recorded provenance for
paper-facing Phase 04.1 reruns.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


SIDECAR_ROOT = Path("expanded_captcha_data/phase04_1")
SOURCES_ROOT = SIDECAR_ROOT / "sources"
MANIFEST_PATH = SIDECAR_ROOT / "manifest.json"
SYMBOL_DESCRIPTION = (
    "Offline generated static symbol-count CAPTCHA-style sample for Phase 04.1."
)
RELATION_PROMPT = (
    "Choose the option image that matches the visual relation shown in the reference image."
)
RELATION_DESCRIPTION = (
    "Offline generated static relation-matching CAPTCHA-style sample for Phase 04.1."
)

SYMBOL_COUNT_SPECS = [
    {
        "file": "symbol_count_007.png",
        "target": "teal hexagons",
        "shape": "hexagon",
        "color": (0, 137, 123),
        "count": 5,
        "distractors": [
            ("circle", (200, 200, 200)),
            ("triangle", (244, 167, 66)),
            ("square", (100, 100, 100)),
            ("diamond", (90, 120, 220)),
        ],
    },
    {
        "file": "symbol_count_008.png",
        "target": "yellow triangles",
        "shape": "triangle",
        "color": (245, 198, 66),
        "count": 7,
        "distractors": [
            ("circle", (48, 90, 180)),
            ("square", (120, 120, 120)),
            ("plus", (90, 90, 90)),
        ],
    },
    {
        "file": "symbol_count_009.png",
        "target": "pink circles",
        "shape": "circle",
        "color": (218, 75, 130),
        "count": 4,
        "distractors": [
            ("diamond", (80, 150, 105)),
            ("triangle", (170, 170, 170)),
            ("square", (65, 65, 65)),
            ("star", (245, 175, 55)),
        ],
    },
    {
        "file": "symbol_count_010.png",
        "target": "navy plus signs",
        "shape": "plus",
        "color": (30, 50, 115),
        "count": 6,
        "distractors": [
            ("circle", (160, 160, 160)),
            ("diamond", (215, 135, 60)),
            ("triangle", (95, 150, 90)),
        ],
    },
]

RELATION_MATCH_SPECS = [
    {
        "stem": "relation_match_005",
        "relation": "same shape",
        "correct_index": 2,
        "reference": [("star", (70, 92), (220, 95), (220, 120, 45), (70, 110, 210))],
        "options": [
            (
                "different relation",
                [("circle", (76, 92), (210, 92), (90, 90, 90), (190, 190, 190))],
            ),
            (
                "different relation",
                [("triangle", (78, 92), (214, 92), (70, 150, 110), (70, 150, 110))],
            ),
            ("same shape", [("square", (76, 92), (214, 92), (180, 80, 150), (65, 135, 200))]),
        ],
    },
    {
        "stem": "relation_match_006",
        "relation": "same color",
        "correct_index": 0,
        "reference": [("diamond", (76, 92), (214, 92), (44, 150, 170), (44, 150, 170))],
        "options": [
            ("same color", [("circle", (76, 92), (214, 92), (210, 75, 75), (210, 75, 75))]),
            (
                "different relation",
                [("circle", (76, 92), (214, 92), (210, 75, 75), (70, 120, 220))],
            ),
            (
                "different relation",
                [("square", (76, 92), (214, 92), (90, 90, 90), (200, 200, 200))],
            ),
        ],
    },
    {
        "stem": "relation_match_007",
        "relation": "left larger",
        "correct_index": 1,
        "reference": [("circle_large_left", (76, 92), (214, 92), (80, 130, 210), (210, 125, 65))],
        "options": [
            (
                "different relation",
                [("circle_large_right", (76, 92), (214, 92), (80, 130, 210), (210, 125, 65))],
            ),
            (
                "left larger",
                [("square_large_left", (76, 92), (214, 92), (80, 150, 95), (170, 90, 170))],
            ),
            (
                "different relation",
                [("same_size", (76, 92), (214, 92), (80, 150, 95), (170, 90, 170))],
            ),
        ],
    },
    {
        "stem": "relation_match_008",
        "relation": "right higher",
        "correct_index": 2,
        "reference": [("right_higher", (78, 108), (214, 72), (170, 95, 210), (60, 150, 130))],
        "options": [
            (
                "different relation",
                [("same_height", (78, 92), (214, 92), (170, 95, 210), (60, 150, 130))],
            ),
            (
                "different relation",
                [("left_higher", (78, 72), (214, 108), (170, 95, 210), (60, 150, 130))],
            ),
            (
                "right higher",
                [("right_higher", (78, 108), (214, 72), (210, 100, 80), (55, 115, 200))],
            ),
        ],
    },
    {
        "stem": "relation_match_009",
        "relation": "overlapping",
        "correct_index": 0,
        "reference": [("overlap", (118, 92), (148, 92), (215, 110, 65), (70, 120, 210))],
        "options": [
            ("overlapping", [("overlap", (118, 92), (148, 92), (80, 150, 120), (210, 85, 130))]),
            (
                "different relation",
                [("separated", (82, 92), (214, 92), (80, 150, 120), (210, 85, 130))],
            ),
            (
                "different relation",
                [("touching", (112, 92), (170, 92), (80, 150, 120), (210, 85, 130))],
            ),
        ],
    },
    {
        "stem": "relation_match_010",
        "relation": "different colors",
        "correct_index": 1,
        "reference": [("same_shape", (76, 92), (214, 92), (75, 135, 220), (225, 150, 70))],
        "options": [
            (
                "different relation",
                [("same_color", (76, 92), (214, 92), (120, 120, 120), (120, 120, 120))],
            ),
            (
                "different colors",
                [("same_shape", (76, 92), (214, 92), (80, 145, 95), (190, 85, 155))],
            ),
            (
                "different relation",
                [("same_color", (76, 92), (214, 92), (70, 120, 210), (70, 120, 210))],
            ),
        ],
    },
]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _shape_bbox(center: tuple[int, int], size: int) -> tuple[int, int, int, int]:
    x, y = center
    half = size // 2
    return (x - half, y - half, x + half, y + half)


def _regular_polygon(
    center: tuple[int, int],
    radius: int,
    sides: int,
    *,
    angle_offset: float = 0.0,
) -> list[tuple[float, float]]:
    import math

    cx, cy = center
    return [
        (
            cx + radius * math.cos(angle_offset + 2 * math.pi * index / sides),
            cy + radius * math.sin(angle_offset + 2 * math.pi * index / sides),
        )
        for index in range(sides)
    ]


def _draw_shape(
    draw: ImageDraw.ImageDraw,
    shape: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
    *,
    size: int = 34,
) -> None:
    outline = (20, 20, 20)
    if shape == "circle":
        draw.ellipse(_shape_bbox(center, size), fill=color, outline=outline, width=2)
    elif shape == "square":
        draw.rectangle(_shape_bbox(center, size), fill=color, outline=outline, width=2)
    elif shape == "triangle":
        draw.polygon(
            _regular_polygon(center, size // 2, 3, angle_offset=-1.57), fill=color, outline=outline
        )
    elif shape == "diamond":
        draw.polygon(
            _regular_polygon(center, size // 2, 4, angle_offset=0.78), fill=color, outline=outline
        )
    elif shape == "hexagon":
        draw.polygon(_regular_polygon(center, size // 2, 6), fill=color, outline=outline)
    elif shape == "star":
        import math

        cx, cy = center
        points = []
        for index in range(10):
            radius = size // 2 if index % 2 == 0 else size // 4
            angle = -math.pi / 2 + index * math.pi / 5
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        draw.polygon(points, fill=color, outline=outline)
    elif shape == "plus":
        x, y = center
        arm = max(5, size // 6)
        half = size // 2
        points = [
            (x - arm, y - half),
            (x + arm, y - half),
            (x + arm, y - arm),
            (x + half, y - arm),
            (x + half, y + arm),
            (x + arm, y + arm),
            (x + arm, y + half),
            (x - arm, y + half),
            (x - arm, y + arm),
            (x - half, y + arm),
            (x - half, y - arm),
            (x - arm, y - arm),
        ]
        draw.polygon(points, fill=color, outline=outline)
    else:
        raise ValueError(f"unknown shape: {shape}")


def _draw_symbol_count(spec: dict[str, Any], output_path: Path) -> None:
    image = Image.new("RGB", (360, 240), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 359, 239), outline=(150, 150, 150), width=2)
    draw.text((14, 12), f"Count: {spec['target']}", fill=(25, 25, 25))

    positions = [
        (55, 70),
        (120, 70),
        (185, 70),
        (250, 70),
        (315, 70),
        (87, 128),
        (153, 128),
        (219, 128),
    ]
    for center in positions[: int(spec["count"])]:
        _draw_shape(draw, spec["shape"], center, spec["color"], size=36)

    distractor_positions = [(72, 152), (145, 152), (215, 152), (288, 152)]
    for center, (shape, color) in zip(distractor_positions, spec["distractors"]):
        _draw_shape(draw, shape, center, color, size=36)

    draw.text((14, 209), "Offline generated Phase 04.1 static sample", fill=(90, 90, 90))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _render_relation_pair(
    draw: ImageDraw.ImageDraw,
    pair_spec: tuple[
        str, tuple[int, int], tuple[int, int], tuple[int, int, int], tuple[int, int, int]
    ],
) -> None:
    relation, left, right, left_color, right_color = pair_spec
    if relation == "circle_large_left":
        _draw_shape(draw, "circle", left, left_color, size=54)
        _draw_shape(draw, "circle", right, right_color, size=34)
    elif relation == "circle_large_right":
        _draw_shape(draw, "circle", left, left_color, size=34)
        _draw_shape(draw, "circle", right, right_color, size=54)
    elif relation == "square_large_left":
        _draw_shape(draw, "square", left, left_color, size=54)
        _draw_shape(draw, "square", right, right_color, size=34)
    elif relation == "same_size":
        _draw_shape(draw, "square", left, left_color, size=38)
        _draw_shape(draw, "square", right, right_color, size=38)
    elif relation == "right_higher":
        _draw_shape(draw, "circle", left, left_color, size=38)
        _draw_shape(draw, "triangle", right, right_color, size=38)
    elif relation == "left_higher":
        _draw_shape(draw, "circle", left, left_color, size=38)
        _draw_shape(draw, "triangle", right, right_color, size=38)
    elif relation == "same_height":
        _draw_shape(draw, "circle", left, left_color, size=38)
        _draw_shape(draw, "triangle", right, right_color, size=38)
    elif relation == "overlap":
        _draw_shape(draw, "circle", left, left_color, size=56)
        _draw_shape(draw, "square", right, right_color, size=56)
    elif relation == "separated":
        _draw_shape(draw, "circle", left, left_color, size=42)
        _draw_shape(draw, "square", right, right_color, size=42)
    elif relation == "touching":
        _draw_shape(draw, "circle", left, left_color, size=52)
        _draw_shape(draw, "square", right, right_color, size=52)
    elif relation == "same_shape":
        _draw_shape(draw, "triangle", left, left_color, size=42)
        _draw_shape(draw, "triangle", right, right_color, size=42)
    elif relation == "same_color":
        _draw_shape(draw, "circle", left, left_color, size=42)
        _draw_shape(draw, "diamond", right, right_color, size=42)
    else:
        shape, left_pos, right_pos, left_fill, right_fill = pair_spec
        _draw_shape(draw, shape, left_pos, left_fill, size=42)
        _draw_shape(draw, shape, right_pos, right_fill, size=42)


def _draw_relation_image(
    title: str,
    relation_label: str,
    pair_specs: list[
        tuple[str, tuple[int, int], tuple[int, int], tuple[int, int, int], tuple[int, int, int]]
    ],
    output_path: Path,
) -> None:
    image = Image.new("RGB", (260, 170), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 259, 169), outline=(150, 150, 150), width=2)
    draw.text((12, 12), title, fill=(25, 25, 25))
    for pair_spec in pair_specs:
        _render_relation_pair(draw, pair_spec)
    draw.text((12, 148), relation_label, fill=(80, 80, 80))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _top_up_symbol_count() -> int:
    task_root = SOURCES_ROOT / "Symbol_Count"
    ground_truth_path = task_root / "ground_truth.json"
    ground_truth = _load_json(ground_truth_path)

    for spec in SYMBOL_COUNT_SPECS:
        _draw_symbol_count(spec, task_root / str(spec["file"]))
        ground_truth[str(spec["file"])] = {
            "count": int(spec["count"]),
            "prompt": f"Count the {spec['target']} in the image.",
            "description": SYMBOL_DESCRIPTION,
        }
    _write_json(ground_truth_path, dict(sorted(ground_truth.items())))
    return len(ground_truth)


def _top_up_relation_match() -> int:
    task_root = SOURCES_ROOT / "Relation_Match"
    ground_truth_path = task_root / "ground_truth.json"
    ground_truth = _load_json(ground_truth_path)

    for spec in RELATION_MATCH_SPECS:
        stem = str(spec["stem"])
        reference = f"{stem}_reference.png"
        options = [f"{stem}_option_{index}.png" for index in range(3)]
        _draw_relation_image(
            "Puzzle overview",
            str(spec["relation"]),
            spec["reference"],
            task_root / f"{stem}.png",
        )
        _draw_relation_image(
            "Reference relation",
            str(spec["relation"]),
            spec["reference"],
            task_root / reference,
        )
        for index, (label, pair_specs) in enumerate(spec["options"]):
            _draw_relation_image(
                "Option: matching relation"
                if index == spec["correct_index"]
                else "Option: non-matching relation",
                label,
                pair_specs,
                task_root / options[index],
            )
        ground_truth[f"{stem}.png"] = {
            "reference_image": reference,
            "option_images": options,
            "correct_index": int(spec["correct_index"]),
            "prompt": RELATION_PROMPT,
            "description": RELATION_DESCRIPTION,
        }
    _write_json(ground_truth_path, dict(sorted(ground_truth.items())))
    return len(ground_truth)


def _sync_manifest_counts(counts: dict[str, int]) -> None:
    manifest = _load_json(MANIFEST_PATH)
    rows = manifest.get("rows")
    if not isinstance(rows, list):
        raise ValueError(f"{MANIFEST_PATH} must contain a rows array")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("manifest rows must be objects")
        task_type = row.get("task_type")
        if task_type in counts:
            row["sample_count"] = counts[str(task_type)]
    _write_json(MANIFEST_PATH, manifest)


def main() -> None:
    counts = {
        "Symbol_Count": _top_up_symbol_count(),
        "Relation_Match": _top_up_relation_match(),
    }
    _sync_manifest_counts(counts)
    print(json.dumps({"updated_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
