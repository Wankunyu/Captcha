# %%
# environment needed
# pip install -U pip setuptools wheel
# pip install -U pillow pyyaml openai anthropic google-genai tqdm

# %%
import os, re, io, json, time, base64, argparse, random, pathlib, mimetypes
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

import yaml

import tqdm
try:
    from tqdm.auto import tqdm
except Exception:
    def tqdm(x, **kwargs): return x


import openai
import anthropic

# 导入精简的错误收集器
try:
    from experiments_helper import SimpleErrorCollector, load_tasks_from_ground_truth
    ERROR_COLLECTOR_AVAILABLE = True
except ImportError:
    ERROR_COLLECTOR_AVAILABLE = False
    print("⚠️ experiments_helper 未找到，错误分析功能不可用")


# %%
# 检测相关资源是否存在
import os, glob
print("CWD =", os.getcwd())
print("captcha_data exists?", os.path.isdir("./captcha_data"))
print("secrets.yaml exists?", os.path.exists("./secrets.yaml"))
print("sample type dirs:", glob.glob("./captcha_data/*")[:5])

# %%
# 确认api是否存在
import yaml, json
with open("./secrets.yaml","r",encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
print(json.dumps(cfg, indent=2, ensure_ascii=False))
assert cfg.get("providers",{}).get("openai",{}).get("api_key"), "openai.api_key 缺失！"


# %% [markdown]
# ### 工具：密钥/配置、Prompt覆写、成本估算

# %%
IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
IMAGE_EXTENSIONS = {ext.lower() for ext in IMG_EXTS}
IMAGE_EXTENSIONS = {ext.lower() for ext in IMG_EXTS}

# Reasoning instruction for cognitive process tracing
REASONING_INSTRUCTION = """
For research purposes, please provide a complete trace of your cognitive process when solving this problem. Your response should include:

### Stage 1: Initial Processing
- **Raw Observation**: Describe everything you perceive/understand from the input
- **Attention Focus**: What elements draw your attention first and why
- **Initial Hypotheses**: Your immediate interpretations or assumptions

### Stage 2: Analytical Breakdown
- **Problem Decomposition**: Break down the task into sub-components
- **Feature Extraction**: List all relevant features, patterns, or regularities you identify
- **Uncertainty Mapping**: Explicitly mark any ambiguous or unclear aspects (with confidence levels 0-100%)

### Stage 3: Step-by-Step Reasoning
Please number each reasoning step and include:
- The specific operation or inference being made
- The evidence or logic supporting this step
- Alternative interpretations considered (even if rejected)
- Confidence level for this step
- Any assumptions being made

### Stage 4: Error Analysis and Verification
- **Potential Failure Points**: Where might your reasoning go wrong?
- **Consistency Checks**: How do you verify internal consistency?
- **Alternative Paths**: What other approaches did you consider but not pursue?

### Stage 5: Final Output
- **Candidate Answers**: List all possibilities considered
- **Selection Rationale**: Why you chose the final answer
- **Overall Confidence**: Your certainty level in the final answer

**Important Instructions**:
- Do not skip steps that seem "obvious" - document everything
- Include failed attempts and backtracking
- Show intermediate results even if incorrect
- Think aloud - as if debugging your own thinking
- If you're guessing, explicitly state so and explain why

This detailed trace is for academic research on AI reasoning transparency. Please be as verbose and explicit as possible about your internal process.
"""

def _list_images_in_dir(d: str) -> list[str]:
    if not os.path.isdir(d): 
        return []
    return sorted(
        os.path.join(d, f) for f in os.listdir(d)
        if os.path.splitext(f)[1].lower() in IMG_EXTS
    )

def _maybe_parse_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _stem_glob(type_dir: str, pid: str) -> str | None:
    """以 pid 去掉扩展名后，尝试同名图片（.png/.jpg...）"""
    stem = os.path.splitext(pid)[0]
    for ext in IMG_EXTS:
        cand = os.path.join(type_dir, stem + ext)
        if os.path.isfile(cand):
            return cand
    return None


def load_secrets(path: str) -> dict:
    """
    读取项目内的密钥/配置文件（secrets.yaml 或 secrets.json）。
    """
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到密钥文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f) or {}


def load_prompts(path: Optional[str]) -> Dict[str, str]:
    """
    读取 Prompt 覆写文件（可选，yaml/json）。返回 {任务类型或'default': 覆写文本}
    """
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到 prompts 文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) if path.endswith(".json") else (yaml.safe_load(f) or {})
    # 仅保留字符串项
    return {str(k): str(v) for k, v in (data or {}).items() if isinstance(v, str)}


def estimate_cost(provider: str, model: str, tokens_in: Optional[int], tokens_out: Optional[int], secrets: dict) -> Optional[float]:
    """
    基于 secrets.yaml 的 pricing 区段，按“美元/千 token”估算单题成本。
    """
    try:
        pricing = (secrets.get("pricing") or {}).get(provider, {})
        p = pricing.get(model) or pricing.get(model.lower())
        if not p:
            return None
        def _cost(toks, per_1k):
            if toks is None or per_1k is None: return 0.0
            return (toks / 1000.0) * float(per_1k)
        return round(_cost(tokens_in, p.get("in_per_1k")) + _cost(tokens_out, p.get("out_per_1k")), 6)
    except Exception:
        return None


def extract_json(text: str) -> Optional[dict]:
    """
    轻量 JSON 提取：清理代码块、尝试直接 loads，失败则回退至“外层大括号”截取。
    """
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I|re.M)
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, (dict, list)) else None
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, (dict, list)) else None
        except Exception:
            return None
    return None


def guess_mime(path: str) -> str:
    """
    基于文件扩展名推测 MIME（不读取像素，不转换编码）
    """
    m, _ = mimetypes.guess_type(path)
    if m:
        return m
    ext = os.path.splitext(path.lower())[1]
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
    }.get(ext, "application/octet-stream")

def _is_rect_hit(x: float, y: float, box: dict) -> bool:
    """点是否命中矩形框（含边界）；box: {x,y,width,height} 或 [[x1,y1],[x2,y2]]"""
    if not box:
        return False
    if all(k in box for k in ("x","y","width","height")):
        return (box["x"] <= x <= box["x"] + box["width"] and
                box["y"] <= y <= box["y"] + box["height"])
    if isinstance(box, (list, tuple)) and len(box) == 2:
        (x1,y1),(x2,y2) = box
        return (min(x1,x2) <= x <= max(x1,x2) and
                min(y1,y2) <= y <= max(y1,y2))
    return False

def _point_dist(p: dict, q: dict) -> float:
    """两点欧氏距离；p/q: {"x":..,"y":..}"""
    return ((float(p["x"]) - float(q["x"]))**2 + (float(p["y"]) - float(q["y"]))**2) ** 0.5

def _clean_indices(xs) -> list:
    """索引集合去重/转 int/排序"""
    try:
        return sorted(set(int(i) for i in (xs or [])))
    except Exception:
        return []

def _pair_as_set(pair) -> frozenset:
    """把一对 (i,j) 统一为无序集合，便于比较"""
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        return frozenset([int(pair[0]), int(pair[1])])
    return frozenset()

def _get_first(d: dict, *keys, default=None):
    """从字典里按优先级取第一个存在的键"""
    for k in keys:
        if k in d:
            return d[k]
    return default


def _extract_number(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return float(str(value))
    except Exception:
        return None


def _format_delta(pred: Optional[float], gt: Optional[float]) -> str:
    if pred is None or gt is None:
        return ""
    delta = pred - gt
    sign = "+" if delta > 0 else "" if delta < 0 else ""
    return f" (Δ={sign}{delta:.0f})" if delta != 0 else ""


def _describe_failure(task, parsed, raw: str) -> str:
    task_type = task.type
    gt = task.gt or {}

    if task_type == "Dice_Count":
        gt_sum = _extract_number(gt.get("sum"))
        if not isinstance(parsed, dict):
            return f"未返回结构化 JSON；GT 点数 = {gt_sum}."
        pred_value = _extract_number(parsed.get("value"))
        if pred_value is None:
            return f"缺少有效的 value 字段；GT 点数 = {gt_sum}."
        if parsed.get("answer_type") != "number":
            return f"answer_type 应为 'number'，实际为 {parsed.get('answer_type')!r}；预测值 {pred_value}，GT = {gt_sum}{_format_delta(pred_value, gt_sum)}."
        if gt_sum is None:
            return f"预测值 {pred_value}，无法读取 GT 点数。"
        if pred_value == gt_sum:
            return "预测点数与 GT 一致，但未通过验证，可能是字段或类型不匹配。"
        if pred_value > gt_sum:
            return f"预测点数 {pred_value} 高于 GT {gt_sum}{_format_delta(pred_value, gt_sum)}，说明模型重复计数或误把非顶面算入。"
        return f"预测点数 {pred_value} 低于 GT {gt_sum}{_format_delta(pred_value, gt_sum)}，说明模型遗漏了一些顶面。"

    if task_type == "Click_Order":
        if not isinstance(parsed, dict):
            return "未返回点击序列。"
        pred_pts = parsed.get("points") or []
        if not isinstance(pred_pts, list) or not pred_pts:
            return "points 列表为空或格式错误。"
        gt_pts = gt.get("points_gt") or []
        tol = float(gt.get("tolerance", 40.0))
        messages = []
        min_len = min(len(pred_pts), len(gt_pts))
        for idx in range(min_len):
            p = pred_pts[idx] if isinstance(pred_pts[idx], dict) else None
            q = gt_pts[idx] if isinstance(gt_pts[idx], dict) else None
            if not p or not q:
                messages.append(f"第 {idx+1} 个点击缺少坐标。")
                continue
            dist = _point_dist(p, q)
            if dist > tol:
                messages.append(
                    f"第 {idx+1} 个点击距离目标 {dist:.1f}px (> tolerance {tol}); 预测 ({p.get('x'):.0f},{p.get('y'):.0f}) vs GT ({q.get('x'):.0f},{q.get('y'):.0f})."
                )
        if len(pred_pts) != len(gt_pts):
            messages.append(f"预测点数 {len(pred_pts)} 与 GT {len(gt_pts)} 不一致。")
        if not messages:
            messages.append("点击顺序存在误差，但具体差距未识别，检查原始响应：" + (raw[:120] if raw else "(空)"))
        return " ".join(messages)

    if task_type == "Patch_Select":
        if not isinstance(parsed, dict):
            return "未返回选择索引。"
        pred = set(int(i) for i in (parsed.get("indices") or []))
        gt_indices = set(int(i) for i in (gt.get("indices_gt") or gt.get("correct_patches") or []))
        missing = sorted(gt_indices - pred)
        extra = sorted(pred - gt_indices)
        parts = []
        if missing:
            parts.append(f"缺失 {len(missing)} 个正确索引: {missing[:8]}{'...' if len(missing) > 8 else ''}")
        if extra:
            parts.append(f"多选 {len(extra)} 个错误索引: {extra[:8]}{'...' if len(extra) > 8 else ''}")
        if not parts:
            parts.append("未识别到差异，检查原始响应格式是否符合要求。")
        return "；".join(parts)

    if task_type == "Pick_Area":
        if not isinstance(parsed, dict):
            return "未返回坐标点。"
        pt = parsed.get("point") or {}
        if "x" not in pt or "y" not in pt:
            return "预测点缺少 x/y 坐标。"
        x_pred = float(pt.get("x"))
        y_pred = float(pt.get("y"))
        box = gt.get("area_box")
        if not box:
            return "GT 区域缺失，无法分析。"
        if _is_rect_hit(x_pred, y_pred, box):
            return "预测点落在 GT 区域内，但仍未通过校验，检查 answer_type 或 JSON 结构。"
        # 规范化输出区域范围
        if isinstance(box, dict) and all(k in box for k in ("x","y","width","height")):
            x1, y1 = float(box["x"]), float(box["y"])
            x2, y2 = x1 + float(box["width"]), y1 + float(box["height"])
        elif isinstance(box, (list, tuple)) and len(box) == 2:
            (x1, y1), (x2, y2) = box
            x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        else:
            return "GT 区域格式异常，无法分析。"
        return (
            f"预测点 ({x_pred:.1f},{y_pred:.1f}) 不在 GT 区域内。"
            f"GT 范围 ≈ [{min(x1,x2):.1f},{min(y1,y2):.1f}] 到 [{max(x1,x2):.1f},{max(y1,y2):.1f}] 像素。"
        )

    if task_type in ("Place_Dot", "Geometry_Click", "Misleading_Click"):
        if not isinstance(parsed, dict):
            return "未返回坐标点。"
        pred_pt = parsed.get("point") or {}
        gt_pt = gt.get("target_position") or {}
        tol = float(gt.get("tolerance", 15.0))
        if not ("x" in pred_pt and "y" in pred_pt):
            return "预测点缺少 x/y 坐标。"
        if not ("x" in gt_pt and "y" in gt_pt):
            return "GT 坐标缺失，无法分析。"
        dist = _point_dist(pred_pt, gt_pt)
        return (f"预测坐标 ({pred_pt.get('x'):.1f},{pred_pt.get('y'):.1f}) 距离 GT ({gt_pt.get('x'):.1f},{gt_pt.get('y'):.1f}) 为 {dist:.1f}px，"
                f"超过容差 {tol}px，说明定位偏离目标区域。")

    if task_type == "Image_Matching" or task_type in ("Dart_Count","Coordinates","Connect_Icon","Object_Match"):
        if not isinstance(parsed, dict):
            return "未返回分类结果。"
        idx = parsed.get("index")
        gt_idx = gt.get("correct_index")
        return f"预测 index={idx}，GT={gt_idx}，需检查模型在候选中选择的匹配项是否正确。"

    if task_type in ("Image_Recognition","Select_Animal","Unusual_Detection","Path_Finder"):
        if not isinstance(parsed, dict):
            return "未返回多选结果。"
        pred = sorted(_clean_indices(parsed.get("indices", [])))
        gt_indices = sorted(_clean_indices(gt.get("indices_gt", [])))
        missing = sorted(set(gt_indices) - set(pred))
        extra = sorted(set(pred) - set(gt_indices))
        parts = []
        if missing:
            parts.append(f"缺失 {len(missing)} 个目标: {missing[:8]}{'...' if len(missing)>8 else ''}")
        if extra:
            parts.append(f"多选 {len(extra)} 个: {extra[:8]}{'...' if len(extra)>8 else ''}")
        if not parts:
            parts.append("未识别到具体差异，可能是 JSON 结构不合规。")
        return "；".join(parts)

    # 默认说明
    raw_preview = (raw[:120] + "...") if raw and len(raw) > 120 else (raw or "")
    return f"任务类型 {task_type} 未提供专用分析，请检查原始响应: {raw_preview}"


# %% [markdown]
# ### CaptchaWorld图像缓存（零转换版）：缓存原始字节与其 base64

# %%
class ImageCache:
    """
    原图不做任何转换/重编码：
    - 直接读取文件原始字节并缓存
    - base64 也缓存，避免重复编码
    - LRU 淘汰，内存可控
    """
    def __init__(self, max_items: int = 512):
        self.max_items = max_items
        self._order: List[str] = []
        self._bytes: Dict[str, bytes] = {}
        self._b64: Dict[str, str] = {}

    def _touch(self, k: str):
        if k in self._order:
            self._order.remove(k)
        self._order.append(k)
        while len(self._order) > self.max_items:
            old = self._order.pop(0)
            self._bytes.pop(old, None)
            self._b64.pop(old, None)

    def get_bytes(self, path: str) -> bytes:
        """
        返回原始文件字节（不做任何图像学处理）
        """
        if path in self._bytes:
            self._touch(path)
            return self._bytes[path]
        with open(path, "rb") as f:
            data = f.read()
        self._bytes[path] = data
        self._touch(path)
        return data

    def get_b64(self, path: str) -> str:
        """
        返回原始文件字节的 base64 文本（不含 data: 前缀）
        """
        if path in self._b64:
            self._touch(path)
            return self._b64[path]
        data = self.get_bytes(path)
        b64 = base64.b64encode(data).decode("utf-8")
        self._b64[path] = b64
        self._touch(path)
        return b64


IMG_CACHE = ImageCache(max_items=512)

# %% [markdown]
# ### API Provider Module

# %%
class ModelProvider:
    """
    Provider 抽象基类：定义统一的 infer 接口。
    """
    def __init__(self, model:str, api_key:str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.timeout = float(kwargs.get("timeout_sec", 120.0))
        self.thinking_enabled = bool(kwargs.get("thinking_enabled", False))
        self.thinking_options = kwargs.get("thinking_options") or {}

    def infer(self, prompt:str, images:List[str], json_schema:Dict[str, Any],
              stream:bool=True) -> Tuple[str, Optional[Dict[str,Any]], Dict[str,Any]]:
        raise NotImplementedError


# %% [markdown]
# #### OpenAI Provider

# %%
class OpenAIProvider(ModelProvider):
    """
    OpenAI Provider supporting GPT-5 chat (Chat Completions) and GPT-5 reasoning
    models (Responses API) with strict JSON outputs.
    """

    CHAT_MODELS = {"gpt-5-chat-latest"}
    REASONING_MODELS = {"gpt-5"}

    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise RuntimeError("OpenAI: 请在 secrets.yaml 中配置 api_key。")
        from openai import OpenAI

        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)

        normalized = model.lower()
        if normalized in self.CHAT_MODELS:
            self.is_chat_family = True
            self.is_reasoning_family = False
        elif normalized in self.REASONING_MODELS:
            self.is_chat_family = False
            self.is_reasoning_family = True
        else:
            raise RuntimeError(
                f"OpenAIProvider: 不支持的模型 {model}。当前仅支持 gpt-5-chat-latest 与 gpt-5 (reasoning 模型)。"
            )

        # Default effort aligns with GPT-5 high reasoning configuration
        self.reasoning_effort = self.thinking_options.get("effort", "high")
        self.text_verbosity = self.thinking_options.get("verbosity", "medium")
        self.use_strict_schema = bool(
            kwargs.get("strict_json_schema")
            or self.thinking_options.get("strict_json_schema", False)
        )

    # ---------- helper builders ----------

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a vision agent. Output ONLY a JSON object that strictly matches the given schema. "
            "If the schema contains optional field 'reasoning', you MUST fill it following the detailed cognitive tracing format provided."
        )

    @staticmethod
    def _chat_image_block(path: str) -> Dict[str, Any]:
        mime = guess_mime(path)
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{IMG_CACHE.get_b64(path)}",
                "detail": "high",
            },
        }

    @staticmethod
    def _responses_image_block(path: str) -> Dict[str, Any]:
        mime = guess_mime(path)
        return {
            "type": "input_image",
            "image_url": f"data:{mime};base64,{IMG_CACHE.get_b64(path)}",
        }

    @staticmethod
    def _safe_get(obj: Any, attr: str, default: Any = None) -> Any:
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    def _build_chat_messages(
        self,
        prompt: str,
        images: List[str],
        few_shot_examples: Optional[List],
        schema_text: str,
        reasoning_note: str,
    ) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []

        if few_shot_examples:
            for example_images, example_text in few_shot_examples:
                for img_path in example_images:
                    if os.path.exists(img_path):
                        content.append(self._chat_image_block(img_path))
                content.append({"type": "text", "text": example_text})

        for img_path in images:
            if os.path.exists(img_path):
                content.append(self._chat_image_block(img_path))

        final_prompt = (
            "Now solve this new problem:\n\n" + prompt
            if few_shot_examples
            else prompt
        )
        text_block = (
            final_prompt
            + "\n\nSchema:\n"
            + schema_text
            + (f"\n\n{reasoning_note}" if reasoning_note else "")
        )
        content.append({"type": "text", "text": text_block})

        return [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": content},
        ]

    def _build_responses_input(
        self,
        prompt: str,
        images: List[str],
        few_shot_examples: Optional[List],
        schema_text: str,
        reasoning_note: str,
    ) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = [
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": self._system_prompt()}],
            }
        ]

        user_content: List[Dict[str, Any]] = []

        if few_shot_examples:
            for example_images, example_text in few_shot_examples:
                for img_path in example_images:
                    if os.path.exists(img_path):
                        user_content.append(self._responses_image_block(img_path))
                user_content.append({"type": "input_text", "text": example_text})

        for img_path in images:
            if os.path.exists(img_path):
                user_content.append(self._responses_image_block(img_path))

        final_prompt = (
            "Now solve this new problem:\n\n" + prompt
            if few_shot_examples
            else prompt
        )
        text_block = (
            final_prompt
            + "\n\nSchema:\n"
            + schema_text
            + (f"\n\n{reasoning_note}" if reasoning_note else "")
        )
        user_content.append({"type": "input_text", "text": text_block})

        payload.append({"role": "user", "content": user_content})
        return payload

    # ---------- main entry ----------

    def infer(
        self,
        prompt: str,
        images: List[str],
        json_schema: Dict[str, Any],
        stream: bool = True,
        few_shot_examples: Optional[List] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
        schema_hint = json.dumps(json_schema, ensure_ascii=False)
        has_reasoning = "reasoning" in json_schema.get("properties", {})
        reasoning_note = REASONING_INSTRUCTION if has_reasoning else ""

        start = time.perf_counter()
        ttft_ms: Optional[float] = None
        tokens_in = tokens_out = None

        try:
            if self.is_chat_family:
                messages = self._build_chat_messages(
                    prompt, images, few_shot_examples, schema_hint, reasoning_note
                )
                raw, tokens_in, tokens_out, ttft_ms = self._infer_chat(messages, stream)
            else:
                responses_input = self._build_responses_input(
                    prompt, images, few_shot_examples, schema_hint, reasoning_note
                )
                raw, tokens_in, tokens_out, ttft_ms = self._infer_responses(
                    responses_input, json_schema, stream
                )
        except Exception as e:
            raw = f"__ERROR__: {type(e).__name__}: {e}"
            ttft_ms = ttft_ms or (time.perf_counter() - start) * 1000.0

        e2e_ms = (time.perf_counter() - start) * 1000.0
        parsed = extract_json(raw)
        meta = dict(
            ttft_ms=ttft_ms or e2e_ms,
            e2e_ms=e2e_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=None,
        )
        return raw, parsed, meta

    # ---------- chat branch ----------

    def _infer_chat(
        self, messages: List[Dict[str, Any]], stream: bool
    ) -> Tuple[str, Optional[int], Optional[int], Optional[float]]:
        response_format = {"type": "json_object"}
        start = time.perf_counter()
        ttft_ms: Optional[float] = None
        tokens_in = tokens_out = None

        if stream:
            chunks: List[str] = []
            for event in self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=0,
                stream=True,
            ):
                delta = event.choices[0].delta.content if event.choices else None
                if delta:
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - start) * 1000.0
                    chunks.append(delta)
            raw = "".join(chunks)
        else:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=0,
            )
            raw = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None)
            if usage:
                tokens_in = getattr(usage, "prompt_tokens", None)
                tokens_out = getattr(usage, "completion_tokens", None)
            ttft_ms = (time.perf_counter() - start) * 1000.0

        return raw, tokens_in, tokens_out, ttft_ms

    # ---------- reasoning branch (Responses API) ----------

    def _infer_responses(
        self,
        responses_input: List[Dict[str, Any]],
        json_schema: Dict[str, Any],
        stream: bool,
    ) -> Tuple[str, Optional[int], Optional[int], Optional[float]]:
        request_body: Dict[str, Any] = {
            "model": self.model,
            "input": responses_input,
            "text": {"verbosity": self.text_verbosity},
        }

        if self.thinking_enabled:
            effort = self.thinking_options.get("effort", self.reasoning_effort)
            request_body["reasoning"] = {"effort": effort}

        if self.use_strict_schema:
            request_body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "ExtractionSchema",
                    "schema": json_schema,
                    "strict": True,
                },
            }

        start = time.perf_counter()
        ttft_ms: Optional[float] = None
        tokens_in = tokens_out = None

        if stream:
            chunks: List[str] = []
            for event in self.client.responses.create(stream=True, **request_body):
                event_type = self._safe_get(event, "type")
                if event_type == "response.output_text.delta":
                    delta = self._safe_get(event, "delta")
                    if delta:
                        if ttft_ms is None:
                            ttft_ms = (time.perf_counter() - start) * 1000.0
                        chunks.append(delta)
                elif event_type == "response.completed":
                    resp_obj = self._safe_get(event, "response")
                    if resp_obj:
                        usage = self._safe_get(resp_obj, "usage")
                        if usage:
                            tokens_in = self._safe_get(usage, "input_tokens")
                            tokens_out = self._safe_get(usage, "output_tokens")
            raw = "".join(chunks)
        else:
            resp = self.client.responses.create(**request_body)
            output_chunks: List[str] = []
            outputs = self._safe_get(resp, "output")
            if outputs:
                for item in outputs:
                    content_list = self._safe_get(item, "content")
                    if not content_list:
                        continue
                    for content in content_list:
                        ctype = self._safe_get(content, "type")
                        if ctype == "output_text":
                            text = self._safe_get(content, "text")
                            if text:
                                output_chunks.append(text)
            raw = "".join(output_chunks)
            usage = self._safe_get(resp, "usage")
            if usage:
                tokens_in = self._safe_get(usage, "input_tokens")
                tokens_out = self._safe_get(usage, "output_tokens")
            ttft_ms = (time.perf_counter() - start) * 1000.0

        return raw, tokens_in, tokens_out, ttft_ms

# %% [markdown]
# #### Anthropic Provider

# %%
class AnthropicProvider(ModelProvider):
    """
    Anthropic（Claude）：使用 messages.create + json_schema response_format。
    图片以“原始字节的 base64 + MIME”传入，不做转换。
    """
    def __init__(self, model:str, api_key:str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise RuntimeError("Anthropic: 请在 secrets.yaml 中配置 api_key。")
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self._thinking_payload = None
        if self.thinking_enabled:
            try:
                budget = int(self.thinking_options.get("budget_tokens", 1024))
            except Exception:
                budget = 1024
            thinking_type = self.thinking_options.get("type", "structured")
            self._thinking_payload = {"type": thinking_type, "budget_tokens": budget}

    @staticmethod
    def _img_part(path:str)->dict:
        b64 = IMG_CACHE.get_b64(path)
        mime = guess_mime(path)
        return {"type":"image","source":{"type":"base64","media_type":mime,"data":b64}}

    def infer(self, prompt:str, images:List[str], json_schema:Dict[str, Any],
              stream:bool=True, few_shot_examples:Optional[List]=None)->Tuple[str, Optional[Dict[str,Any]], Dict[str,Any]]:
        # Check if reasoning field is in schema
        has_reasoning = "reasoning" in json_schema.get("properties", {})
        reasoning_note = REASONING_INSTRUCTION if has_reasoning else ""

        blocks = []

        # 1. Add few-shot examples first (if any)
        if few_shot_examples:
            for example_images, example_text in few_shot_examples:
                # Add example images
                for img_path in example_images:
                    if os.path.exists(img_path):
                        blocks.append(self._img_part(img_path))
                # Add example answer text
                blocks.append({"type":"text","text": example_text})

        # 2. Add test images
        for p in images:
            blocks.append(self._img_part(p))

        # 3. Add test prompt (with prefix if few-shot is used)
        if few_shot_examples:
            final_prompt = "Now solve this new problem:\n\n" + prompt
        else:
            final_prompt = prompt

        blocks.append({"type":"text","text": (
            final_prompt +
            "\nReturn ONLY valid JSON per schema." +
            (f"\n\n{reasoning_note}" if reasoning_note else "")
        )})

        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "ocw_schema","schema": json_schema,"strict": True}
        }

        start = time.perf_counter()
        tokens_in = tokens_out = None
        try:
            call_kwargs = dict(
                model=self.model,
                max_tokens=2048,
                temperature=0,
                messages=[{"role":"user","content":blocks}],
                system="Output ONLY a JSON object that strictly matches the schema.",
                response_format=response_format,
            )
            if self._thinking_payload:
                call_kwargs["thinking"] = self._thinking_payload
            resp = self.client.messages.create(**call_kwargs)
            raw = ""
            for c in (resp.content or []):
                if getattr(c, "type", "") == "text":
                    raw += c.text or ""
            usage = getattr(resp, "usage", None)
            if usage:
                tokens_in = getattr(usage, "input_tokens", None)
                tokens_out = getattr(usage, "output_tokens", None)
        except Exception as e:
            raw = f'__ERROR__: {type(e).__name__}: {e}'
        e2e = (time.perf_counter() - start) * 1000.0
        parsed = extract_json(raw)
        meta = dict(ttft_ms=e2e, e2e_ms=e2e, tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=None)
        return raw, parsed, meta

# %% [markdown]
# #### Gemini Provider

# %%
class GeminiProvider(ModelProvider):
    """
    Gemini Provider（始终内联原始图像字节，不使用 File API）
    - 不做任何图像转换/重编码：直接读取磁盘原始字节。
    - parts 结构为 [ text, {"mime_type":..., "data": <raw bytes>}, ... ]。
    - 显式设置 request_options.timeout，避免卡死。
    """
    def __init__(self, model:str, api_key:str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise RuntimeError("Gemini: 请在 secrets.yaml 中配置 api_key。")

        from google import genai
        from google.genai import types as genai_types

        client_kwargs = {}
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        self.client = genai.Client(**client_kwargs)
        self.genai_types = genai_types

    def infer(self, prompt:str, images:List[str], json_schema:Dict[str, Any],
              stream:bool=True, few_shot_examples:Optional[List]=None) -> Tuple[str, Optional[Dict[str,Any]], Dict[str,Any]]:
        """
        - 直接内联原始字节（零转换）；
        - Gemini 在多数地区对非流式的响应延时更稳定，这里不使用 stream。
        - 支持 few-shot learning
        """
        # Check if reasoning field is in schema
        has_reasoning = "reasoning" in json_schema.get("properties", {})
        reasoning_note = REASONING_INSTRUCTION if has_reasoning else ""

        user_parts: List[Any] = []

        # 1. Add few-shot examples first (if any)
        if few_shot_examples:
            for example_images, example_text in few_shot_examples:
                # Add example images
                for img_path in example_images:
                    if os.path.exists(img_path):
                        user_parts.append(
                            self.genai_types.Part.from_bytes(
                                data=IMG_CACHE.get_bytes(img_path),
                                mime_type=guess_mime(img_path)
                            )
                        )
                # Add example answer text
                user_parts.append(
                    self.genai_types.Part.from_text(text=example_text)
                )

        # 2. Add test images
        for p in images:
            user_parts.append(
                self.genai_types.Part.from_bytes(
                    data=IMG_CACHE.get_bytes(p), mime_type=guess_mime(p)
                )
            )

        # 3. Add test prompt (with prefix if few-shot is used)
        if few_shot_examples:
            final_prompt = "Now solve this new problem:\n\n" + prompt
        else:
            final_prompt = prompt

        user_parts.append(
            self.genai_types.Part.from_text(
                text=(
                    final_prompt +
                    "\n\nReturn ONLY valid JSON per schema:\n" + json.dumps(json_schema, ensure_ascii=False) +
                    (f"\n\n{reasoning_note}" if reasoning_note else "")
                )
            )
        )

        content = self.genai_types.Content(role="user", parts=user_parts)

        schema_obj: Any = json_schema
        try:
            schema_obj = self.genai_types.Schema(**json_schema)
        except Exception:
            pass

        config: Dict[str, Any] = {
            "temperature": 0,
            "response_mime_type": "application/json",
            "response_schema": schema_obj,
        }
        if self.thinking_enabled:
            try:
                budget = self.thinking_options.get("thinking_budget")
                if budget is None:
                    mode = self.thinking_options.get("mode")
                    if mode == "dynamic":
                        budget = -1
                    elif mode == "disabled":
                        budget = 0
                    else:
                        budget = 1024

                config["thinking_config"] = self.genai_types.ThinkingConfig(
                    thinking_budget=int(budget)
                )
            except Exception as exc:
                print(f"[WARN] Gemini thinking_config unavailable: {exc}")

        # 调用（显式超时，避免阻塞）
        start = time.perf_counter()
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config=config
            )
            raw = getattr(resp, "text", "") or ""
            parsed = getattr(resp, "parsed", None)
            if parsed is None:
                parsed = extract_json(raw)
            usage = getattr(resp, "usage_metadata", None)
            if usage:
                tokens_in = (getattr(usage, "prompt_token_count", None)
                             or getattr(usage, "input_token_count", None)
                             or getattr(usage, "input_tokens", None))
                tokens_out = (getattr(usage, "candidates_token_count", None)
                              or getattr(usage, "output_token_count", None)
                              or getattr(usage, "output_tokens", None))
            else:
                tokens_in = tokens_out = None
        except Exception as e:
            raw = f'__ERROR__: {type(e).__name__}: {e}'
            parsed = None
            tokens_in = tokens_out = None

        e2e = (time.perf_counter() - start) * 1000.0
        if isinstance(raw, str) and raw.startswith('__ERROR__'):
            print(f'[ERROR][Gemini] {raw}')
        meta = dict(ttft_ms=e2e, e2e_ms=e2e, tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=None)
        return raw, parsed, meta


# %%
# (Legacy Gemini File API helper removed; refer to historical commits if needed.)

# %% [markdown]
# #### Fireworks AI Provider

# %%
class FireworksProvider(ModelProvider):
    """
    Fireworks AI Provider: OpenAI-compatible API with JSON Schema support.
    Supports vision-language models like Qwen3-VL-235B.

    Base URL: https://api.fireworks.ai/inference/v1
    Model format: accounts/fireworks/models/{model_name}
    """
    def __init__(self, model:str, api_key:str, base_url:str=None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        if not self.api_key:
            raise RuntimeError("Fireworks: 请在 secrets.yaml 中配置 api_key。")
        from openai import OpenAI
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url or "https://api.fireworks.ai/inference/v1",
            timeout=self.timeout
        )

    def infer(self, prompt:str, images:List[str], json_schema:Dict[str, Any],
              stream:bool=True, few_shot_examples:Optional[List]=None)->Tuple[str, Optional[Dict[str,Any]], Dict[str,Any]]:
        """
        Fireworks inference with JSON Schema support.

        Supports:
        - Vision input (up to 30 images, max 10MB total base64)
        - JSON Schema structured output
        - Few-shot examples
        """
        # Check if reasoning field is in schema
        has_reasoning = "reasoning" in json_schema.get("properties", {})
        reasoning_note = REASONING_INSTRUCTION if has_reasoning else ""

        content = []

        # 1. Add few-shot examples first (if any)
        if few_shot_examples:
            for example_images, example_text in few_shot_examples:
                # Add example images
                for img_path in example_images:
                    if os.path.exists(img_path):
                        mime = guess_mime(img_path)
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{IMG_CACHE.get_b64(img_path)}",
                                "detail": "high"
                            }
                        })
                # Add example answer text
                content.append({"type": "text", "text": example_text})
            # Add separator for test problem
            content.append({"type": "text", "text": "\n\nNow solve this new problem:\n\n"})

        # 2. Add test prompt text
        content.append({
            "type": "text",
            "text": (
                prompt +
                "\nReturn ONLY valid JSON per schema." +
                (f"\n\n{reasoning_note}" if reasoning_note else "")
            )
        })

        # 3. Add test images
        for p in images:
            mime = guess_mime(p)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{IMG_CACHE.get_b64(p)}",
                    "detail": "high"
                }
            })

        msgs = [
            {"role": "system", "content": "Output ONLY a JSON object that strictly matches the schema."},
            {"role": "user", "content": content}
        ]

        if self.thinking_enabled:
            print("[WARN] Fireworks provider: thinking flag is not explicitly supported; model may ignore.")

        # Prepare response_format with JSON Schema
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "captcha_response",
                "schema": json_schema,
                "strict": True  # Fireworks supports strict mode
            }
        }

        start = time.perf_counter()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=0,
                response_format=response_format,
            )
            raw = resp.choices[0].message.content or ""
            tokens_in = getattr(getattr(resp, "usage", None), "prompt_tokens", None)
            tokens_out = getattr(getattr(resp, "usage", None), "completion_tokens", None)
        except Exception as e:
            raw, tokens_in, tokens_out = f'__ERROR__: {type(e).__name__}: {e}', None, None

        e2e = (time.perf_counter() - start) * 1000.0
        parsed = extract_json(raw)
        meta = dict(ttft_ms=e2e, e2e_ms=e2e, tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=None)
        return raw, parsed, meta

# %% [markdown]
# #### Provider工厂

# %%
def make_provider(name:str, model:str, secrets:dict, timeout_sec:float,
                     thinking_enabled: bool = False,
                     thinking_options: Optional[Dict[str, Any]] = None) -> ModelProvider:
    """
    根据名称创建具体 Provider 实例，并从 secrets 中注入 api_key/base_url。
    参数：
        name: provider 名称（openai/anthropic/gemini/fireworks）。
        model: 模型名称。
        secrets: 配置字典（load_secrets 返回）。
        timeout_sec: 超时秒数。
    返回：
        ModelProvider 子类实例。
    异常：
        ValueError: 未知 provider。
    """
    name_l = name.lower()
    prov_cfg = (secrets.get("providers") or {}).get(name_l, {})
    api_key = prov_cfg.get("api_key")

    merged_thinking: Dict[str, Any] = {}
    prov_thinking = prov_cfg.get("thinking")
    if isinstance(prov_thinking, dict):
        merged_thinking.update(prov_thinking)
    if isinstance(thinking_options, dict):
        merged_thinking.update(thinking_options)
    enable_flag = thinking_enabled or bool(merged_thinking)

    common_kwargs = dict(
        timeout_sec=timeout_sec,
        thinking_enabled=enable_flag,
        thinking_options=merged_thinking
    )

    if name_l == "openai":
        return OpenAIProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "anthropic":
        return AnthropicProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "gemini":
        return GeminiProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "fireworks":
        return FireworksProvider(model=model, api_key=api_key, base_url=prov_cfg.get("base_url"), **common_kwargs)
    raise ValueError(f"未知 provider: {name}。支持的 providers: openai, anthropic, gemini, fireworks")



# %% [markdown]
# ### 数据集与任务构建

# %%
@dataclass
class TaskItem:
    """
    任务条目：
    - type: 任务类型名（目录名）
    - puzzle_id: 题目文件名或标识
    - prompt: 文本指令（已套用覆写/前后缀）
    - images: 输入图像绝对路径列表（原图）
    - gt: Ground Truth（用于评测）
    """
    type: str
    puzzle_id: str
    prompt: str
    images: List[str]
    gt: Dict[str, Any]


SUPPORTED_TYPES = {
    # 静态化的五类
    "Dice_Count",
    "Geometry_Click",
    "Image_Matching",
    "Patch_Select",
    "Place_Dot",
    # 无交互或已静态化
    "Bingo",
    "Click_Order",
    "Dart_Count",
    "Image_Recognition",
    "Misleading_Click",
    "Object_Match",
    "Path_Finder",
    "Pick_Area",
    "Select_Animal",
    "Unusual_Detection",
    "Coordinates",
    "Connect_Icon",
    "Rotation_Match",
}

TYPE_REQUIRE_PER_ITEM = {"Geometry_Click", "Image_Recognition", "Misleading_Click",
                         "Select_Animal","Patch_Select","Bingo", 
                         "Click_Order", "Connect_Icon", "Coordinates", "Dice_Count",
                        "Dart_Count", "Image_Matching", "Object_Match", "Pick_Area",
                        "Place_Dot", "Rotation_Match", "Unusual_Detection", "Path_Finder"}

# 明确「不要用 per-item（伪 per-item）」的类型：一律忽略题面文案，按类型/默认模板走
TYPE_IGNORE_PER_ITEM = {}
# 例如若你确认 Image_Matching/Coordinates 的 GT 文案完全同质，就填：
# TYPE_IGNORE_PER_ITEM = {"Image_Matching", "Coordinates"}


# —— 细粒度到题号（按需用，不用就留空）——
# 强制保留某些具体题目的 per-item 文案
ID_REQUIRE_PER_ITEM = {
    # "Geometry_Click": {"puzzle_0001.jpg", "foo_023.jpg"},
}
# 强制忽略某些具体题目的 per-item 文案
ID_IGNORE_PER_ITEM = {
    # "Image_Recognition": {"weird_007.jpg"},
}


def _is_git_lfs_pointer(text: str) -> bool:
    return text.strip().startswith("version https://git-lfs.github.com/spec/v1")


def load_ground_truth(type_dir: str) -> Dict[str, Any]:
    """
    读取某类任务的 ground_truth.json（拒绝 LFS 指针）。
    """
    gt_path = os.path.join(type_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"ground_truth.json 不存在: {gt_path}")
    with open(gt_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if _is_git_lfs_pointer(raw):
        raise RuntimeError(f"{gt_path} 是 Git LFS 指针。请确保你已拉取真实 JSON 文件。")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 ground_truth.json 失败: {gt_path} - {e}")



def _load_prompts_yaml(path: Optional[str]) -> dict:
    """向后兼容：prompts.yaml 既可以是 {type: str} 的老格式，也可以是新结构化格式。"""
    if not path:
        return {}
    import yaml, io
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # 老格式：直接 {type: "text"}，包一层
    if data and "types" not in data and "default" not in data and "by_id" not in data:
        data = {"version": 0, "types": data}
    # 规范字段
    data.setdefault("default", {})
    data.setdefault("types", {})
    data.setdefault("templates", {})
    data.setdefault("by_id", {})
    return data

def load_few_shot_examples(few_shot_file: str = "./few_shot_examples.yaml") -> Dict[str, List[Dict]]:
    """
    加载 few-shot 示例配置

    Args:
        few_shot_file: few-shot 配置文件路径

    Returns:
        字典，key 为任务类型，value 为示例列表
    """
    if not few_shot_file or not os.path.exists(few_shot_file):
        return {}

    with open(few_shot_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config if config else {}


def _collect_image_paths(base_dir: pathlib.Path, name: str) -> List[str]:
    """
    Resolve image references for few-shot assets. Supports direct files and directories.
    """
    if not name:
        return []

    paths: List[str] = []
    target = base_dir / name

    def add_from_path(path: pathlib.Path) -> None:
        if path.is_dir():
            for file in sorted(path.iterdir()):
                if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
                    paths.append(str(file))
        elif path.is_file():
            paths.append(str(path))

    if target.exists():
        add_from_path(target)
    else:
        stem = pathlib.Path(name).stem
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            candidate = base_dir / f"{stem}{ext}"
            if candidate.exists():
                add_from_path(candidate)
                break

    return paths

def build_few_shot_content(
    task_type: str,
    few_shot_examples: Dict,
    dataset_root: Optional[str] = None,
    few_shot_assets_root: Optional[pathlib.Path] = None
) -> List:
    """
    构建 few-shot 示例内容（图片路径列表 + 简洁答案文本）

    注意：答案数据现在从 few_shot_answers.py 中读取（硬编码），
    不再依赖 ground_truth.json，避免文件名变更导致的匹配问题。

    Args:
        task_type: 任务类型
        few_shot_examples: few-shot 配置字典（仅用于指定使用哪些示例）
        dataset_root: 数据集根目录
        few_shot_assets_root: few-shot 资源根目录

    Returns:
        示例内容列表: [(images_list, answer_text), ...]
    """
    # 导入硬编码的答案数据
    try:
        from few_shot_answers import get_all_examples
    except ImportError:
        print(f"⚠️ 警告：无法导入 few_shot_answers，few-shot 功能不可用")
        return []

    if task_type not in few_shot_examples:
        return []

    examples_data = few_shot_examples[task_type].get("examples", [])
    if not examples_data:
        return []

    # 从硬编码答案中获取该任务类型的所有示例
    hardcoded_examples = get_all_examples(task_type)
    if not hardcoded_examples:
        # 如果没有硬编码答案，回退到原有逻辑（从 YAML 读取）
        print(f"⚠️ 警告：{task_type} 在 few_shot_answers.py 中没有硬编码答案，回退到 YAML")
        hardcoded_examples = examples_data

    # 确定资源根目录
    FEW_SHOT_ASSETS_ROOT = pathlib.Path(os.environ.get("FEW_SHOT_ASSETS_ROOT", "./few_shot_assets")).resolve()
    assets_root = pathlib.Path(few_shot_assets_root or FEW_SHOT_ASSETS_ROOT)
    task_dir_name = task_type.split('(')[0].strip()
    type_dir = assets_root / task_dir_name
    if not type_dir.exists() and dataset_root:
        # 兼容旧数据结构，回退到原始数据集路径
        type_dir = pathlib.Path(dataset_root) / task_dir_name
    result = []

    for i, yaml_example in enumerate(examples_data, 1):
        # 从 YAML 中获取文件名
        filename = yaml_example.get("filename")
        if not filename:
            continue

        # 从硬编码答案中查找匹配的答案数据
        example = None
        for hc_ex in hardcoded_examples:
            if hc_ex.get("filename") == filename:
                example = hc_ex
                break

        # 如果没找到硬编码答案，使用 YAML 中的数据
        if example is None:
            example = yaml_example

        images: List[str] = []
        seen: set[str] = set()

        # 某些任务类型的 filename 只是 puzzle ID，不对应真实图片文件
        # 这些任务类型使用 reference_image 和 option_images 作为实际图片
        puzzle_id_only_tasks = ["Dart_Count", "Connect_icon", "Coordinates", "Rotation_Match", "Object_Match"]

        # 主图片（仅对非 puzzle_id_only 任务加载）
        if filename and task_type not in puzzle_id_only_tasks:
            for path in _collect_image_paths(type_dir, filename):
                if path not in seen:
                    images.append(path)
                    seen.add(path)

        # 处理可能的第二张、第三张图片
        # 不同任务类型使用不同的字段名：
        # - Click_Order: order_image
        # - Connect_icon, Coordinates, Dart_Count, Image_Matching, Object_Match, Path_Finder: reference_image
        # - Rotation_Match: reference_image, object_base_image
        # - Slide_Puzzle: component_image
        additional_image_fields = [
            "order_image",           # Click_Order
            "reference_image",       # Connect_icon, Coordinates, Dart_Count, Image_Matching, Object_Match, Path_Finder, Rotation_Match
            "object_base_image",     # Rotation_Match
            "component_image"        # Slide_Puzzle
        ]

        for field in additional_image_fields:
            if field in example:
                img_value = example[field]
                if isinstance(img_value, str):
                    for path in _collect_image_paths(type_dir, img_value):
                        if path not in seen:
                            images.append(path)
                            seen.add(path)

        # 处理选择题的选项图片（options 或 option_images）
        # Connect_icon, Path_Finder: options
        # Coordinates, Dart_Count, Image_Matching, Object_Match: option_images
        option_field = None
        if "options" in example:
            option_field = "options"
        elif "option_images" in example:
            option_field = "option_images"

        if option_field:
            option_list = example[option_field]
            if isinstance(option_list, list):
                for option_img in option_list:
                    if isinstance(option_img, str):
                        for path in _collect_image_paths(type_dir, option_img):
                            if path not in seen:
                                images.append(path)
                                seen.add(path)

        # 构建简洁的答案文本（从硬编码数据中读取）
        answer = example.get("answer")
        if answer is not None:
            answer_text = f"Example {i}: {json.dumps(answer, ensure_ascii=False)}"
        else:
            answer_text = f"Example {i}: (no answer available)"

        if images:
            result.append((images, answer_text))

    return result

def _resolve_prompt_cfg(cfg: dict, task_type: str, puzzle_id: str) -> dict:
    """
    根据类型与题目ID解析配置：
    优先级：by_id 覆盖 > types[task_type] > default
    返回 dict: {"mode": "merge|replace|auto|gt", "rules": str|None, "template": str|None, "override": str|None}
    """
    by_id = cfg.get("by_id", {})
    # 支持两种键： "Type/ID" 或在 by_id[Type] 下的 {ID: text}
    override = by_id.get(f"{task_type}/{puzzle_id}") or \
               (isinstance(by_id.get(task_type), dict) and by_id[task_type].get(puzzle_id))

    tcfg = cfg.get("types", {}).get(task_type, {})
    dcfg = cfg.get("default", {})
    # 兼容老格式：types[task_type] 可能是字符串（即 replace 文本）
    if isinstance(tcfg, str):
        return {"mode": "replace", "rules": None, "template": None, "override": tcfg}

    mode = tcfg.get("mode") or dcfg.get("mode") or "merge"
    rules = tcfg.get("rules") or dcfg.get("rules")
    template = cfg.get("templates", {}).get(task_type) or cfg.get("templates", {}).get("default")

    return {"mode": mode, "rules": rules, "template": template, "override": override}

def _render_template(template: str, context: dict) -> str:
    """极简模板：支持 {{gt_prompt}}, {{type}}, {{pid}} 三个占位符；避免 format 大括号冲突。"""
    if not template:
        return ""
    out = template.replace("{{gt_prompt}}", context.get("gt_prompt", ""))
    out = out.replace("{{type}}", context.get("type", ""))
    out = out.replace("{{pid}}", context.get("pid", ""))
    return out

def _choose_prompt(entry: dict,
                   task_type: str,
                   puzzle_id: str,
                   default_prompt: str,
                   prompts_cfg: dict,           # 结构化 prompts（_load_prompts_yaml 的返回）
                   prefix: str,
                   suffix: str,
                   mode: str = "auto",
                   prompt_cfg: dict | None = None,
                   **_compat                   # ← 新增：吸收旧参数（如 overrides=...）
                   ) -> str:
    """
    最终 prompt 选择（支持 gt/opt/merge/auto + 结构化 prompts.yaml + 手工策略开关）
    - 兼容：老的扁平 overrides（{Type: "text", "default": "text", "Type:ID": "text"}）
    """
    cfg = prompt_cfg if prompt_cfg is not None else (prompts_cfg or {})

    # 1) per-item 原文
    base_raw = (entry.get("prompt") or entry.get("question") or entry.get("instruction") or "").strip()

    # 2) GT 模式【完全不受“忽略 per-item”策略影响】；其余模式再看你的手工策略
    if mode == "gt":
        use_per_item = bool(base_raw)
        base = base_raw
    else:
        def _should_use_per_item(t: str, pid: str, raw: str) -> bool:
            if pid in ID_REQUIRE_PER_ITEM.get(t, set()): return True
            if pid in ID_IGNORE_PER_ITEM.get(t, set()): return False
            if t in TYPE_REQUIRE_PER_ITEM: return True
            if t in TYPE_IGNORE_PER_ITEM: return False
            return bool(raw)
        use_per_item = _should_use_per_item(task_type, puzzle_id, base_raw)
        base = base_raw if use_per_item else ""

    # 3) 结构化解析（by_id/types/default/templates/mode）
    resolved = _resolve_prompt_cfg(cfg, task_type, puzzle_id) if cfg else {}
    cfg_mode = (resolved.get("mode") or "merge")
    if cfg_mode == "replace":
        cfg_mode = "opt"
    rules_text = (resolved.get("rules") or "").strip() or None
    override_text = (resolved.get("override") or "").strip() or None
    template_text = (resolved.get("template") or "").strip() or None

    # 4) 兼容旧式“扁平 overrides”参数（若存在就按旧语义参与）
    flat = _compat.get("overrides")
    flat_by_id = flat_type = flat_def = None
    if isinstance(flat, dict):
        flat_by_id = flat.get(f"{task_type}:{puzzle_id}") or flat.get(f"{task_type}/{puzzle_id}")
        flat_type  = flat.get(task_type)
        flat_def   = flat.get("default")

    # 5) 生效模式
    if mode in ("gt","merge","opt"):
        effective_mode = mode
    else:  # auto
        effective_mode = "merge" if use_per_item else "opt"

    # 6) 组装正文
    if effective_mode == "gt":
        p = base if base else default_prompt

    elif effective_mode == "opt":
        # 优先级：structured override > flat(by_id/type/default) > template > rules > base/default
        if override_text:
            p = override_text
        elif flat_by_id or flat_type or flat_def:
            p = flat_by_id or flat_type or flat_def
        elif template_text:
            p = _render_template(template_text, {"gt_prompt": base or default_prompt, "type": task_type, "pid": puzzle_id})
        elif rules_text:
            p = rules_text
        else:
            p = base or default_prompt

    else:  # merge
        core = base or default_prompt
        extras = []
        if template_text:
            extras.append(_render_template(template_text, {"gt_prompt": core, "type": task_type, "pid": puzzle_id}))
        if override_text:
            extras.append(override_text)
        if rules_text:
            extras.append(rules_text)
        # 扁平 overrides 放最后（作为补充说明）
        for x in (flat_by_id, flat_type, flat_def):
            if x: extras.append(x)
        p = core + (("\n\n" + "\n\n".join(extras)) if extras else "")

    # 7) 前后缀
    if prefix:
        p = f"{prefix}\n{p}"
    if suffix:
        p = f"{p}\n{suffix}"
    return p





def build_tasks(
    dataset_root: str,
    types: List[str],
    max_per_type: int = None,
    prompts_cfg: dict | None = None,
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    prompt_mode: str = "auto", # ← "gt"|"opt"|"merge"|"auto"
    exclude_examples: Optional[Dict[str, List[str]]] = None
) -> List[TaskItem]:
    prompts_cfg = prompts_cfg or {}
    exclude_examples = exclude_examples or {}
    tasks: List[TaskItem] = []
    for t in types:
        if t not in SUPPORTED_TYPES:
            print(f"[跳过] 暂未支持的类型: {t}")
            continue
        type_dir = os.path.join(dataset_root, t)
        try:
            gt = load_ground_truth(type_dir)
        except Exception as e:
            print(f"[跳过] 读取 GT 失败 {t}: {e}")
            continue

        puzzle_ids = list(gt.keys())

        # 过滤掉用作 few-shot 示例的样本
        excluded_files = exclude_examples.get(t, [])
        if excluded_files:
            excluded_set = set(excluded_files)
            excluded_stems = {os.path.splitext(name)[0] for name in excluded_files}
            puzzle_ids = [
                pid for pid in puzzle_ids
                if pid not in excluded_set and os.path.splitext(pid)[0] not in excluded_stems
            ]

        random.shuffle(puzzle_ids)
        if max_per_type:
            puzzle_ids = puzzle_ids[:max_per_type]

        for pid in puzzle_ids:
            entry = gt[pid]

            # === 静态的5类 ===
            if t == "Dice_Count":
                default_prompt = ("Count ONLY the pips visible on the TOP faces of all dice. "
                                  "Do NOT count side/hidden faces or reflections. "
                                  "Return JSON {\"answer_type\":\"number\",\"value\":N}.")
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img): 
                    print(f"[跳过] 文件不存在: {img}"); 
                    continue
                tasks.append(TaskItem(t, pid, prompt, [img], {"sum": entry.get("sum")}))

            elif t == "Geometry_Click":
                # 1) 基于 GT 的 type 生成清晰的默认提示语（若该题有 per-item prompt/_choose_prompt 会优先用 per-item）
                target_type = str((entry.get("answer") or {}).get("type") or "").strip()
                if target_type.lower().startswith("letter "):
                    obj = target_type.split(" ", 1)[1].strip() or "target letter"
                    semantic = f"Click the CENTER of letter '{obj}'."
                elif target_type:
                    semantic = f"Click the CENTER of the target {target_type}."
                else:
                    semantic = "Click the CENTER of the specified geometric target."

                default_prompt = (
                    f"{semantic}\n"
                    "Return ONLY JSON {\"answer_type\":\"single_point\",\"point\":{\"x\":...,\"y\":...}} (pixels)."
                )

                # 2) 选择最终 prompt（支持 gt/opt/merge/auto + by-id 覆盖）
                prompt = _choose_prompt(
                    entry=entry,                 # 题目级 GT（含 per-item 'prompt'）
                    task_type=t,                 # "Geometry_Click"
                    puzzle_id=pid,               # 文件名，如 dingxiang_000001.jpg
                    default_prompt=default_prompt,
                    prompts_cfg=prompts_cfg or {},       
                    prefix=prompt_prefix,
                    suffix=prompt_suffix,
                    mode=prompt_mode
                )

                # 3) 图片路径与存在性
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue

                # 4) 规范化 bbox：从 answer.area=[[x0,y0],[x1,y1]] 提取为 [xmin,ymin,xmax,ymax]
                ans = entry.get("answer") or {}
                area = ans.get("area")
                bbox = None
                if (isinstance(area, (list, tuple)) and len(area) == 2
                    and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in area)):
                    (x0, y0), (x1, y1) = area
                    x0, x1 = (x0, x1) if x0 <= x1 else (x1, x0)
                    y0, y1 = (y0, y1) if y0 <= y1 else (y1, y0)
                    bbox = [float(x0), float(y0), float(x1), float(y1)]
                else:
                    print(f"[跳过] {t}/{pid} 非法 area 格式：{area}")
                    continue

                # 5) 写入任务（统一用矩形基线判定；shape 仅做记录/调试）
                shape = target_type or "region"
                tasks.append(
                    TaskItem(t, pid, prompt, [img], {"bbox": bbox, "shape": shape})
                )


            elif t == "Image_Matching":
                ref = entry.get("reference_image")
                options = entry.get("option_images", [])
                if not ref or not options:
                    print(f"[跳过] {t}/{pid} 缺 reference/option_images")
                    continue
                default_prompt = (
                    "The FIRST image is the REFERENCE, followed by OPTION images indexed 0..N-1 in order. "
                    "Return JSON {\"answer_type\":\"classify\",\"index\":k} with 0-based index only."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                
                img_ref = os.path.join(type_dir, ref)
                imgs_opt = [os.path.join(type_dir, p) for p in options]
                ok = True
                for p in [img_ref]+imgs_opt:
                    if not os.path.isfile(p): 
                        print(f"[跳过] 文件不存在: {p}"); 
                        ok=False; break
                if not ok: 
                    continue
                tasks.append(TaskItem(t, pid, prompt, [img_ref] + imgs_opt,
                                      {"correct_index": entry.get("correct_option_index", entry.get("correct_index", 0)),
                                       "num_options": len(options)}))

            elif t == "Patch_Select":
                # 1) 读取图片路径与存在性
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue

                # 2) 基础信息：目标对象 + 网格尺寸
                target = entry.get("target_object") or "the target object"
                gs = entry.get("grid_size", [5, 5])
                if not (isinstance(gs, (list, tuple)) and len(gs) == 2):
                    gs = [5, 5]
                R, C = int(gs[0]), int(gs[1])

                # 3) 默认提示：明确网格尺寸与索引规则（0-based、row-major）
                default_prompt = (
                    f"The image already shows a {R}x{C} grid.\n"
                    f"Select ALL cells that contain the target: {target}.\n"
                    f"Indexing is 0-based and row-major: cell_index = r*{C} + c.\n"
                    "Return JSON {\"answer_type\":\"multi_select\",\"indices\":[...]} "
                    "with unique, sorted indices only. No explanations."
                )

                # 4) 选择最终 prompt（支持 gt/opt/merge/auto + by-id 覆盖）
                prompt = _choose_prompt(
                    entry=entry,
                    task_type=t,
                    puzzle_id=pid,
                    default_prompt=default_prompt,
                    prompts_cfg=prompts_cfg or {},
                    prefix=prompt_prefix,
                    suffix=prompt_suffix,
                    mode=prompt_mode
                )

                # 5) 兼容字段名：correct_patches / correct_selections
                indices_gt = entry.get("correct_patches")
                if indices_gt is None:
                    indices_gt = entry.get("correct_selections", [])
                if not isinstance(indices_gt, list):
                    indices_gt = []

                # 6) 写入任务（保留 grid_size 便于调试）
                tasks.append(
                    TaskItem(
                        t, pid, prompt, [img],
                        {"grid_size": [R, C], "correct_patches": indices_gt}
                    )
                )


            elif t == "Place_Dot":
                # 给模型的默认提示（如果该题没有 per-item 文本）
                default_prompt = (
                    "Place a dot at the target position and return the CENTER point "
                    "as JSON {\"answer_type\":\"single_point\",\"point\":{\"x\":..,\"y\":..}} in pixels."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt,
                                        prompts_cfg or {}, prompt_prefix, prompt_suffix,
                                        mode=prompt_mode)

                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue

                # --- 兼容两种 GT 写法 ---
                # 1) target_position: [x, y]
                # 2) target_position: {"x": x, "y": y}
                tp = entry.get("target_position")
                if isinstance(tp, dict) and "x" in tp and "y" in tp:
                    gx, gy = float(tp["x"]), float(tp["y"])
                    tp_norm = {"x": gx, "y": gy}
                elif isinstance(tp, (list, tuple)) and len(tp) == 2:
                    gx, gy = float(tp[0]), float(tp[1])
                    tp_norm = {"x": gx, "y": gy}
                else:
                    print(f"[跳过] {t}/{pid} 非法 target_position：{tp!r}")
                    continue

                tol = float(entry.get("tolerance", 15.0))  # 没写就给默认值

                # 把规范后的坐标与容差存到 meta，评测时直接用
                tasks.append(
                    TaskItem(t, pid, prompt, [img], {
                        "target_position": tp_norm,   # 统一成 {"x":..,"y":..}
                        "tolerance": tol
                    })
                )


            # === 可以静态化的13类 ===
            elif t in ("Select_Animal","Unusual_Detection"):
                # 多选网格类（或 Path_Finder 的多选变体）
                default_prompt = (
                    "Select ALL grid cells (0-based, row-major) that satisfy the condition. "
                    "Return JSON {\"answer_type\":\"multi_select\",\"indices\":[...]}."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue
                # 兼容多个字段名
                indices_gt = _get_first(entry, "correct_selections", "correct_patches", "answer", default=[])
                tasks.append(TaskItem(t, pid, prompt, [img], {"indices_gt": indices_gt}))

            elif t == "Path_Finder":
                # 若有 ref+options → classify；否则退化为网格多选（少见）
                default_prompt_cls = (
                    "Choose the option depicting the same physical location as the reference."
                    " Return JSON {\"answer_type\":\"classify\",\"index\":k} (0-based)."
                )
                default_prompt_multi = (
                    "Select ALL grid cells (0-based, row-major) that match the reference view."
                    " Return JSON {\"answer_type\":\"multi_select\",\"indices\":[...]}"
                )
                has_ref_opts = bool(entry.get("reference_image")) and bool(entry.get("option_images"))

                default_prompt = default_prompt_cls if has_ref_opts else default_prompt_multi
                prompt = _choose_prompt(entry, t, pid, default_prompt,
                                        prompts_cfg or {}, prompt_prefix, prompt_suffix,
                                        mode=prompt_mode)

                if has_ref_opts:
                    ref = os.path.join(type_dir, entry["reference_image"])
                    opts = [os.path.join(type_dir, p) for p in entry["option_images"]]
                    if not (os.path.isfile(ref) and all(os.path.isfile(p) for p in opts)):
                        print(f"[跳过] {t}/{pid} 缺图像文件")
                        continue
                    corr = int(_get_first(entry, "correct_option_index","correct_index","answer", default=0))
                    tasks.append(TaskItem(t, pid, prompt, [ref]+opts, {"correct_index": corr}))
                else:
                    img = os.path.join(type_dir, pid)
                    if not os.path.isfile(img):
                        print(f"[跳过] 文件不存在: {img}")
                        continue
                    indices_gt = _get_first(entry, "correct_selections", "correct_patches", "answer", default=[])
                    tasks.append(TaskItem(t, pid, prompt, [img], {"indices_gt": indices_gt}))


            elif t in ("Dart_Count","Coordinates","Object_Match"):
                # 静态化为分类题（参考 + 选项），或单图但 GT 给了正确索引
                default_prompt = (
                    "Choose the correct option and return JSON {\"answer_type\":\"classify\",\"index\":k} (0-based)."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                # 优先读取 reference + options；若没有，就只发单图
                ref = entry.get("reference_image")
                options = entry.get("option_images", [])
                imgs: List[str] = []
                if ref and options:
                    img_ref = os.path.join(type_dir, ref)
                    imgs_opt = [os.path.join(type_dir, p) for p in options]
                    ok = os.path.isfile(img_ref) and all(os.path.isfile(p) for p in imgs_opt)
                    if not ok:
                        print(f"[跳过] {t}/{pid} 缺图像文件")
                        continue
                    imgs = [img_ref] + imgs_opt
                else:
                    single = os.path.join(type_dir, pid)
                    if not os.path.isfile(single):
                        print(f"[跳过] 文件不存在: {single}")
                        continue
                    imgs = [single]
                correct_idx = _get_first(entry, "correct_option_index","correct_index","answer", default=0)
                tasks.append(TaskItem(t, pid, prompt, imgs, {"correct_index": int(correct_idx)}))

            elif t == "Pick_Area":
                default_prompt = (
                    "Return a single point (pixel coordinates) that lies INSIDE the target area. "
                    "JSON only: {\"answer_type\":\"single_point\",\"point\":{\"x\":..,\"y\":..}}."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue
                area = _get_first(entry, "area", "answer", default=None)
                if isinstance(area, dict) and "area" in area:
                    area = area["area"]
                if area is None:
                    print(f"[跳过] {t}/{pid} 缺 area")
                    continue
                tasks.append(TaskItem(t, pid, prompt, [img], {"area_box": area}))

            elif t == "Click_Order":
                default_prompt = (
                    "If provided, use the reference image to follow the required sequence. "
                    "Click the targets IN ORDER and return JSON "
                    "{\"answer_type\":\"click_order\",\"points\":[{\"x\":..,\"y\":..}, ...]} (pixels)."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                puzzle_img = os.path.join(type_dir, pid)
                if not os.path.isfile(puzzle_img):
                    print(f"[跳过] 文件不存在: {puzzle_img}")
                    continue
                images: List[str] = []
                order_img_name = entry.get("order_image") or entry.get("reference_image") or entry.get("order")
                if order_img_name:
                    order_img_path = os.path.join(type_dir, order_img_name)
                    if os.path.isfile(order_img_path):
                        images.append(order_img_path)
                    else:
                        print(f"[警告] {t}/{pid} 缺 order_image: {order_img_path}")
                images.append(puzzle_img)
                pts = _get_first(entry, "answer", "points", default=[])
                tol = float(_get_first(entry, "tolerance", "tol_px", default=40.0))
                # 归一化成 [{"x":..,"y":..}, ...]
                points_gt = []
                for p in pts:
                    if isinstance(p, dict) and "x" in p and "y" in p:
                        points_gt.append({"x":float(p["x"]), "y":float(p["y"])})
                    elif isinstance(p, (list,tuple)) and len(p)==2:
                        points_gt.append({"x":float(p[0]), "y":float(p[1])})
                if not points_gt:
                    print(f"[跳过] {t}/{pid} 缺点列")
                    continue
                tasks.append(TaskItem(t, pid, prompt, images, {"points_gt": points_gt, "tolerance": tol}))

            elif t == "Bingo":
                default_prompt = (
                    "Return exactly two cell indices to swap as JSON "
                    "{\"answer_type\":\"swap\",\"pair\":[i,j]} (0-based)."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue
                # GT: 列出所有可行的交换对
                swap_pairs = _get_first(entry, "answer", "swap_pairs", default=[])
                # 规范化为 [(i,j), ...]
                norm_pairs = []
                for p in swap_pairs:
                    if isinstance(p, (list,tuple)) and len(p)==2:
                        norm_pairs.append([int(p[0]), int(p[1])])
                    elif isinstance(p, dict) and "i" in p and "j" in p:
                        norm_pairs.append([int(p["i"]), int(p["j"])])
                if not norm_pairs:
                    print(f"[跳过] {t}/{pid} 缺 swap_pairs")
                    continue
                tasks.append(TaskItem(t, pid, prompt, [img], {"swap_pairs": norm_pairs}))


            elif t == "Misleading_Click":
                default_prompt = (
                    "Return a SAFE click point INSIDE the image and OUTSIDE the forbidden area. "
                    "JSON only: {\"answer_type\":\"single_point\",\"point\":{\"x\":..,\"y\":..}}."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)
                img = os.path.join(type_dir, pid)
                if not os.path.isfile(img):
                    print(f"[跳过] 文件不存在: {img}")
                    continue
                avoid = _get_first(entry, "avoid_area","forbid_area","answer", default=None)
                # 读取图片尺寸以做“点在图内”的硬性检查
                try:
                    from PIL import Image
                    with Image.open(img) as im:
                        w,h = im.size
                except Exception:
                    print(f"[跳过] {t}/{pid} 读取尺寸失败")
                    continue
                tasks.append(TaskItem(t, pid, prompt, [img], {"avoid_area": avoid, "image_size": (w,h)}))

            elif t == "Image_Recognition":
                default_prompt = (
                    "Select ALL grid cells (0-based, row-major) that satisfy the condition. "
                    "Return JSON {\"answer_type\":\"multi_select\",\"indices\":[...]}."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)

                # 路径：优先使用 subfolder（或 images_dir）；文件名来自 images 数组
                sub = entry.get("subfolder") or entry.get("images_dir") or ""
                base_dir = os.path.join(type_dir, sub) if sub else type_dir

                names = entry.get("images") or []  # 形如 ["1.jpg", ..., "9.jpg"]
                if names:
                    imgs = [os.path.join(base_dir, n) for n in names]
                else:
                    # 兜底：如果声明了子目录但没给 images 列表，就直接枚举该目录下的图片
                    imgs = _list_images_in_dir(base_dir)

                # 过滤出真正存在的文件，至少需要 9 张（九宫格）
                imgs = [p for p in imgs if os.path.isfile(p)]
                if len(imgs) < 9:
                    print(f"[跳过] {t}/{pid} 缺图像文件：解析到 {len(imgs)} 张（需 ≥9）")
                    continue
                imgs = imgs[:9]  # 多于 9 张时取前 9

                indices_gt = _get_first(entry, "correct_selections", "correct_patches", "answer", default=[])
                tasks.append(TaskItem(t, pid, prompt, imgs, {"indices_gt": indices_gt}))


            elif t == "Connect_Icon":
                default_prompt = (
                    "Choose the correct option and return JSON {\"answer_type\":\"classify\",\"index\":k} (0-based)."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)

                # GT 明确给了字段：reference_image + options
                ref_name = entry.get("reference_image") or entry.get("reference")
                opt_names = entry.get("options") or entry.get("option_images") or entry.get("candidates")

                if not (ref_name and isinstance(opt_names, list) and opt_names):
                    print(f"[跳过] {t}/{pid} 缺 reference_image/options")
                    continue

                img_ref = os.path.join(type_dir, ref_name)
                imgs_opt = [os.path.join(type_dir, n) for n in opt_names]

                if not (os.path.isfile(img_ref) and all(os.path.isfile(p) for p in imgs_opt)):
                    print(f"[跳过] {t}/{pid} 缺图像文件（reference 或 options 不存在）")
                    continue

                correct_idx = int(_get_first(entry, "correct_option", "correct_option_index", "answer", default=0))
                tasks.append(TaskItem(t, pid, prompt, [img_ref] + imgs_opt, {"correct_index": correct_idx}))


            elif t == "Rotation_Match":
                default_prompt = (
                    "Return the rotation angle (degrees) that best aligns the object. "
                    "JSON only: {\"answer_type\":\"rotation\",\"angle\":...}."
                )
                prompt = _choose_prompt(entry, t, pid, default_prompt, prompts_cfg or {}, prompt_prefix, prompt_suffix, mode=prompt_mode)

                ref_name = entry.get("reference_image") or entry.get("reference")
                obj_name = entry.get("object_base_image") or entry.get("object_image") or entry.get("image") or entry.get("img")

                if not (ref_name and obj_name):
                    print(f"[跳过] {t}/{pid} 缺 reference_image/object_base_image")
                    continue

                img_ref = os.path.join(type_dir, ref_name)  # 例如 direction_3.jpg
                img_obj = os.path.join(type_dir, obj_name)  # 例如 cat.jpg / sad_cat.jpg 及其若干角度样例

                if not (os.path.isfile(img_ref) and os.path.isfile(img_obj)):
                    print(f"[跳过] {t}/{pid} 缺图像文件（reference 或 object 不存在）")
                    continue

                # 角度与容差（GT 有统一字段）
                ang = float(_get_first(entry, "correct_angle", "answer", "target_angle_deg", default=0.0))
                ang_tol = float(_get_first(entry, "angle_tol_deg", "tolerance_deg", default=5.0))

                # 给模型的输入：两张图（方向参考 + 对象），输出目标角度
                tasks.append(TaskItem(t, pid, prompt, [img_ref, img_obj],
                                    {"correct_angle": ang, "angle_tol_deg": ang_tol}))


            
            
            else:
                # 未覆盖到的类型
                print(f"[跳过] 暂无构建逻辑: {t}/{pid}")
                continue

    return tasks



# %% [markdown]
# ### 评测：Pass@1 与 JSON Schema

# %%

def _clean_indices(xs):
    """把 indices 归一到升序、去重的 int 列表；传入 None/空时返回 []。"""
    out = []
    for v in (xs or []):
        try:
            out.append(int(v))
        except Exception:
            continue
    return sorted(set(out))


def evaluate_pass1(task:TaskItem, parsed:Optional[Dict[str,Any]])->bool:
    if parsed is None:
        return False
    t = task.type
    gt = task.gt
    try:
        # === 纯静态的5类 ===
        if t == "Dice_Count":
            return parsed.get("answer_type")=="number" and int(parsed.get("value")) == int(gt["sum"])
        
        if task.type == "Geometry_Click":
            try:
                x = float(parsed["point"]["x"]); y = float(parsed["point"]["y"])
            except Exception:
                return False
            bbox = gt.get("bbox")
            if not (isinstance(bbox, (list,tuple)) and len(bbox)==4):
                return False
            x0,y0,x1,y1 = map(float, bbox)
            return (x0 <= x <= x1) and (y0 <= y <= y1)

        if t == "Image_Matching":
            return parsed.get("answer_type")=="classify" and int(parsed.get("index")) == int(gt["correct_index"])
        
        if t == "Patch_Select":
            pred = sorted(set(int(i) for i in parsed.get("indices", [])))
            gold = sorted(set(int(i) for i in gt.get("correct_patches",[])))
            return pred == gold
        
        if task.type == "Place_Dot":
            # 期望模型输出: {"answer_type":"single_point","point":{"x":..,"y":..}}
            try:
                pt = parsed["point"]
                x_pred, y_pred = float(pt["x"]), float(pt["y"])
            except Exception:
                return False

            # --- 从 meta 取 GT（build 阶段已统一为 {"x":..,"y":..}）---
            tp = gt.get("target_position")
            tol = float(gt.get("tolerance", 15.0))

            gx = gy = None
            if isinstance(tp, dict) and "x" in tp and "y" in tp:
                gx, gy = float(tp["x"]), float(tp["y"])
            elif isinstance(tp, (list, tuple)) and len(tp) == 2:
                # 依然兼容万一 meta 里是数组的情况
                gx, gy = float(tp[0]), float(tp[1])

            if gx is None or gy is None:
                return False

            # 欧氏距离（用平方避免开方）
            dx, dy = x_pred - gx, y_pred - gy
            return (dx*dx + dy*dy) <= (tol * tol)

        # === 静态化的13类 ===
        if t in ("Image_Recognition","Select_Animal","Unusual_Detection","Path_Finder"):
            pred = _clean_indices(parsed.get("indices", []))
            gold = _clean_indices(gt.get("indices_gt", []))
            return pred == gold

        if t in ("Dart_Count","Coordinates","Connect_Icon","Object_Match"):
            return parsed.get("answer_type")=="classify" and int(parsed.get("index")) == int(gt["correct_index"])

        if t == "Pick_Area":
            pt = parsed.get("point") or {}
            x,y = float(pt.get("x")), float(pt.get("y"))
            area = gt.get("area_box")  # [[x1,y1],[x2,y2]] 或 {x,y,w,h}
            return _is_rect_hit(x,y,area)

        if t == "Click_Order":
            pts_pred = list(parsed.get("points") or [])
            pts_gt   = list(gt.get("points_gt") or [])
            if len(pts_pred) != len(pts_gt) or len(pts_gt) == 0:
                return False
            tol = float(gt.get("tolerance", 40.0))
            for p,q in zip(pts_pred, pts_gt):
                if not (("x" in p and "y" in p) and ("x" in q and "y" in q)):
                    return False
                if _point_dist(p,q) > tol:
                    return False
            return True

        if t == "Bingo":
            pair = parsed.get("pair") or []
            if not (isinstance(pair, (list,tuple)) and len(pair)==2):
                return False
            pred = _pair_as_set(pair)
            gold_pairs = [ _pair_as_set(p) for p in (gt.get("swap_pairs") or []) ]
            return pred in gold_pairs

        if t == "Rotation_Match":
            if parsed.get("answer_type")!="rotation":
                return False
            ang_pred = float(parsed.get("angle"))
            ang_gt   = float(gt.get("correct_angle"))
            tol = float(gt.get("angle_tol_deg", 5.0))
            # 归一到 [-180,180) 再比较（可选）
            diff = abs(((ang_pred - ang_gt + 180) % 360) - 180)
            return diff <= tol

        if t == "Misleading_Click":
            # 1) 在图内
            pt = parsed.get("point") or {}
            x,y = float(pt.get("x")), float(pt.get("y"))
            w,h = gt.get("image_size",(None,None))
            if w is None or h is None:
                return False  # 理论上不会；build_tasks 已写入
            if not (0 <= x < w and 0 <= y < h):
                return False
            # 2) 不在禁止区
            avoid = gt.get("avoid_area")
            if avoid:
                if _is_rect_hit(x,y,avoid):
                    return False
            return True
    except Exception:
        return False
    return False


def _with_reasoning(schema: Dict[str, Any], *, include_reasoning: bool) -> Dict[str, Any]:
    """在现有 schema 上追加可选 reasoning 字段（详细推理过程）。"""
    try:
        if include_reasoning:
            props = schema.setdefault("properties", {})
            if "reasoning" not in props:
                # 增加到 8192 以支持详细的 5 阶段认知追踪
                props["reasoning"] = {"type": "string", "maxLength": 8192}
        return schema
    except Exception:
        return schema


def build_json_schema(task_type:str, *, include_reasoning: bool = False)->Dict[str,Any]:
    # === 纯静态的五类 ===
    if task_type == "Dice_Count":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["number"]},
                                              "value":{"type":"integer"}},
                "required":["answer_type","value"]}, include_reasoning=include_reasoning)
    if task_type in ("Geometry_Click","Place_Dot"):
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["single_point"]},
                                              "point":{"type":"object",
                                                       "properties":{"x":{"type":"number"},"y":{"type":"number"}},
                                                       "required":["x","y"]}},
                "required":["answer_type","point"]}, include_reasoning=include_reasoning)
    if task_type == "Image_Matching":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["classify"]},
                                              "index":{"type":"integer"}},
                "required":["answer_type","index"]}, include_reasoning=include_reasoning)
    if task_type == "Patch_Select":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["multi_select"]},
                                              "indices":{"type":"array","items":{"type":"integer"}}},
                "required":["answer_type","indices"]}, include_reasoning=include_reasoning)

    # === 静态化13类 ===
    if task_type in ("Image_Recognition","Select_Animal","Unusual_Detection","Path_Finder"):
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["multi_select"]},
                                              "indices":{"type":"array","items":{"type":"integer"}}},
                "required":["answer_type","indices"]}, include_reasoning=include_reasoning)

    if task_type in ("Dart_Count","Coordinates","Connect_Icon","Object_Match"):
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["classify"]},
                                              "index":{"type":"integer"}},
                "required":["answer_type","index"]}, include_reasoning=include_reasoning)

    if task_type == "Pick_Area":
        # 采用"点内判定"，最稳健
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["single_point"]},
                                              "point":{"type":"object",
                                                       "properties":{"x":{"type":"number"},"y":{"type":"number"}},
                                                       "required":["x","y"]}},
                "required":["answer_type","point"]}, include_reasoning=include_reasoning)

    if task_type == "Click_Order":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["click_order"]},
                                              "points":{"type":"array",
                                                        "items":{"type":"object",
                                                                 "properties":{"x":{"type":"number"},"y":{"type":"number"}},
                                                                 "required":["x","y"]}}},
                "required":["answer_type","points"]}, include_reasoning=include_reasoning)

    if task_type == "Bingo":
        # 返回一次交换的两个格子索引（九宫格等）
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["swap"]},
                                              "pair":{"type":"array","minItems":2,"maxItems":2,
                                                      "items":{"type":"integer"}}},
                "required":["answer_type","pair"]}, include_reasoning=include_reasoning)

    if task_type == "Rotation_Match":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["rotation"]},
                                              "angle":{"type":"number"}},
                "required":["answer_type","angle"]}, include_reasoning=include_reasoning)

    if task_type == "Misleading_Click":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["single_point"]},
                                              "point":{"type":"object",
                                                       "properties":{"x":{"type":"number"},"y":{"type":"number"}},
                                                       "required":["x","y"]}},
                "required":["answer_type","point"]}, include_reasoning=include_reasoning)

    # fallback
    return _with_reasoning({"type":"object"}, include_reasoning=include_reasoning)


# %% [markdown]
# ### 评测入口

# %%
def run_eval(
    dataset_root: str,
    types: List[str],
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    max_per_type: int = 15,
    out_csv: str = "results.csv",
    secrets_file: str = "./secrets.yaml",
    stream: bool = True,
    estimate_cost_flag: bool = False,  # 兼容旧参数，不使用
    timeout_sec: float = 600.0,
    seed: int = 1234,
    prompts_file: Optional[str] = None,
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    prompt_mode: str = "auto",
    summary_csv: Optional[str] = None,
    thinking: bool = False,
    thinking_options: Optional[Dict[str, Any]] = None,
    collect_tokens: bool = False,
    token_log_path: Optional[str] = None,
    token_summary_path: Optional[str] = None,
    experiment_name: Optional[str] = None,
    collect_errors: bool = False,
    error_analysis_dir: Optional[str] = None,
    error_experiment_name: Optional[str] = None,
    collect_reasoning: bool = False,
    few_shot_config: Optional[Dict] = None,
    few_shot_file: str = "./few_shot_examples.yaml",
    few_shot_assets_root: str = "./few_shot_assets",
) -> Dict[str, Any]:
    """
    实验一：仅输出【每类一行】的聚合结果到 out_csv；
    控制台仍打印每类与总体摘要。不再写每题一行。
    支持 few-shot learning。
    """
    secrets = load_secrets(secrets_file)
    random.seed(seed)

    # 结构化加载 prompts.yaml（支持 merge/replace/by_id/template）
    prompts_cfg = _load_prompts_yaml(prompts_file) if prompts_file else {}

    if thinking_options is not None and not isinstance(thinking_options, dict):
        raise TypeError("thinking_options 必须是 dict 或 None")

    # Few-shot 集成逻辑
    few_shot_examples_db = None
    exclude_examples = None
    few_shot_enabled = few_shot_config and few_shot_config.get("enabled", False)

    if few_shot_enabled:
        print(f"[INFO] Few-shot learning enabled")
        # 加载 few-shot 示例配置
        few_shot_examples_db = load_few_shot_examples(few_shot_file)

        if few_shot_examples_db:
            # 构建排除列表（避免示例样本被测试）
            exclude_examples = {}
            for task_type in types:
                if task_type in few_shot_examples_db:
                    examples = few_shot_examples_db[task_type].get("examples", [])
                    excluded_files = [ex.get("filename") for ex in examples if ex.get("filename")]
                    if excluded_files:
                        exclude_examples[task_type] = excluded_files
            print(f"[INFO] Excluding {sum(len(v) for v in exclude_examples.values())} few-shot examples from testing")

    tasks = build_tasks(dataset_root, types, max_per_type,
                        prompts_cfg=prompts_cfg,
                        prompt_prefix=prompt_prefix,
                        prompt_suffix=prompt_suffix,
                        prompt_mode=prompt_mode,
                        exclude_examples=exclude_examples)
    print(f"[INFO] 将评测 {len(tasks)} 道题（types={types}）")

    # 成本估算依赖 usage，多数情况下需非流式；但本函数不再输出逐题行→不再写成本列
    stream_flag = (stream and (not estimate_cost_flag) and (not collect_tokens) and (not collect_errors))
    prov = make_provider(
        provider,
        model,
        secrets,
        timeout_sec,
        thinking_enabled=thinking,
        thinking_options=thinking_options
    )

    import time, csv, os
    token_tot_in = 0
    token_tot_out = 0
    token_by_type = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0, "count": 0})
    token_log_writer = None
    token_log_file = None
    if collect_tokens and token_log_path:
        os.makedirs(os.path.dirname(token_log_path) or ".", exist_ok=True)
        token_log_file = open(token_log_path, "w", encoding="utf-8", newline="")
        token_log_writer = csv.writer(token_log_file)
        token_log_writer.writerow([
            "provider", "model", "type", "puzzle_id", "tokens_in", "tokens_out", "ttft_ms", "e2e_ms"
        ])

    collector = None
    analysis_dir = None
    ea_token_log_file = None
    ea_token_log_writer = None
    if collect_errors:
        if not ERROR_COLLECTOR_AVAILABLE:
            print("⚠️ SimpleErrorCollector 不可用，跳过错误分析收集")
            collect_errors = False
        else:
            exp_name = error_experiment_name or experiment_name or "exp"
            root_dir = error_analysis_dir or "./error_analysis"
            analysis_dir = os.path.join(root_dir, exp_name)
            os.makedirs(analysis_dir, exist_ok=True)
            collector = SimpleErrorCollector(experiment_name=exp_name)
            ea_token_log_path = os.path.join(analysis_dir, "token_log.csv")
            ea_token_log_file = open(ea_token_log_path, "w", encoding="utf-8", newline="")
            ea_token_log_writer = csv.writer(ea_token_log_file)
            ea_token_log_writer.writerow([
                "provider", "model", "type", "puzzle_id", "tokens_in", "tokens_out", "ttft_ms", "e2e_ms"
            ])

    # 聚合器（按类型）
    agg = defaultdict(lambda: {"n": 0, "ok": 0, "e2e_sum": 0.0, "ttft_sum": 0.0})
    failures: List[Dict[str, Any]] = []

    ok = 0
    errors = 0
    sum_e2e = 0.0
    wall_t0 = time.perf_counter()

    # —— 推理并聚合（不写逐题行）——
    for task in tqdm(tasks, desc="Evaluating", ncols=0):
        schema = build_json_schema(task.type, include_reasoning=collect_reasoning)

        # 构建该任务类型的 few-shot 示例内容（如果启用）
        few_shot_content = None
        if few_shot_enabled and few_shot_examples_db:
            few_shot_content = build_few_shot_content(
                task.type,
                few_shot_examples_db,
                dataset_root=dataset_root,
                few_shot_assets_root=few_shot_assets_root
            )

        raw, parsed, meta = prov.infer(
            prompt=task.prompt,
            images=task.images,
            json_schema=schema,
            stream=stream_flag,
            few_shot_examples=few_shot_content
        )

        failure_msg = None

        if isinstance(raw, str) and raw.startswith("__ERROR__"):
            parsed = None
            errors += 1

        passed = evaluate_pass1(task, parsed)
        ok += int(passed)

        reasoning_text = None
        if collect_reasoning and isinstance(parsed, dict):
            r = parsed.get("reasoning")
            if isinstance(r, str) and r.strip():
                reasoning_text = r.strip()

        if not passed:
            failure_msg = _describe_failure(task, parsed, raw)
            detail = {
                "type": task.type,
                "puzzle_id": task.puzzle_id,
                "explain": failure_msg,
                "raw": raw
            }
            if reasoning_text:
                detail["reasoning"] = reasoning_text
            failures.append(detail)

        e2e = float(meta.get("e2e_ms") or 0.0)
        ttft = float(meta.get("ttft_ms") or e2e)
        sum_e2e += e2e

        tokens_in = int(meta.get("tokens_in") or 0)
        tokens_out = int(meta.get("tokens_out") or 0)
        token_tot_in += tokens_in
        token_tot_out += tokens_out
        rec_tok = token_by_type[task.type]
        rec_tok["tokens_in"] += tokens_in
        rec_tok["tokens_out"] += tokens_out
        rec_tok["count"] += 1
        if token_log_writer:
            token_log_writer.writerow([
                provider,
                model,
                task.type,
                task.puzzle_id,
                tokens_in,
                tokens_out,
                f"{ttft:.1f}",
                f"{e2e:.1f}"
            ])

        if collector:
            # 仅在错误时提供 failure_msg，否则从模型获取 reasoning
            error_description = failure_msg if not passed else None

            reasoning_field = None
            if collect_reasoning and isinstance(parsed, dict):
                r = parsed.get("reasoning")
                if isinstance(r, str) and r.strip():
                    reasoning_field = r.strip()

            collector.record(
                task_type=task.type,
                puzzle_id=task.puzzle_id,
                prompt=task.prompt,
                gt=task.gt,
                raw=raw,
                parsed=parsed,
                pass1=passed,
                meta=meta,
                error_description=error_description,
                reasoning=reasoning_field
            )
            if ea_token_log_writer:
                ea_token_log_writer.writerow([
                    provider,
                    model,
                    task.type,
                    task.puzzle_id,
                    tokens_in,
                    tokens_out,
                    f"{ttft:.1f}",
                    f"{e2e:.1f}"
                ])

        rec = agg[task.type]
        rec["n"] += 1
        rec["ok"] += int(passed)
        rec["e2e_sum"] += e2e
        rec["ttft_sum"] += ttft

    if token_log_file:
        token_log_file.flush()
        token_log_file.close()
    if ea_token_log_file:
        ea_token_log_file.flush()
        ea_token_log_file.close()

    wall_ms = (time.perf_counter() - wall_t0) * 1000.0
    pass1 = ok/len(tasks) if tasks else 0.0

    # —— 仅写每类一行的 CSV —— 
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    overall_cost = estimate_cost(provider, model, token_tot_in, token_tot_out, secrets) or 0.0

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # 精简成类型级别列，包含 token 与成本信息
        writer.writerow([
            "provider","model","type","n","pass_at_1","avg_ttft_ms","avg_e2e_ms",
            "tokens_in","tokens_out","total_tokens","cost_usd","cost_per_question"
        ])
        for t in sorted(agg.keys()):
            s = agg[t]
            n = s["n"]
            pass_at_1 = (s["ok"]/n) if n else 0.0
            avg_ttft = (s["ttft_sum"]/n) if n else 0.0
            avg_e2e  = (s["e2e_sum"]/n) if n else 0.0
            tok = token_by_type[t]
            tokens_in = tok["tokens_in"]
            tokens_out = tok["tokens_out"]
            total_tokens = tokens_in + tokens_out
            cost_usd = estimate_cost(provider, model, tokens_in, tokens_out, secrets) or 0.0
            cost_per_question = (cost_usd / n) if n else 0.0
            writer.writerow([
                provider,
                model,
                t,
                n,
                f"{pass_at_1:.3f}",
                f"{avg_ttft:.1f}",
                f"{avg_e2e:.1f}",
                tokens_in,
                tokens_out,
                total_tokens,
                f"{cost_usd:.6f}",
                f"{cost_per_question:.6f}"
            ])

    # —— 控制台摘要（保留）——
    print("\n[SUMMARY by type]")
    for t in sorted(agg.keys()):
        s = agg[t]; n = s["n"]; ok_t = s["ok"]
        e2e_avg = (s["e2e_sum"]/n) if n else 0.0
        ttft_avg = (s["ttft_sum"]/n) if n else 0.0
        tok = token_by_type[t]
        tokens_in = tok["tokens_in"]
        tokens_out = tok["tokens_out"]
        cost_usd = estimate_cost(provider, model, tokens_in, tokens_out, secrets) or 0.0
        print(f"- {t:<18} n={n:3d}  pass@1={ok_t/n if n else 0:.3f}  "
              f"avg_e2e_ms={e2e_avg:.1f}  avg_ttft_ms={ttft_avg:.1f}  "
              f"tokens_in={tokens_in} tokens_out={tokens_out} cost_usd={cost_usd:.6f}")

    summary_path = None
    if collect_tokens and token_summary_path:
        summary_path = token_summary_path
    elif collect_errors and analysis_dir:
        summary_path = os.path.join(analysis_dir, "token_summary.json")

    if summary_path:
        os.makedirs(os.path.dirname(summary_path) or ".", exist_ok=True)
        summary = {
            "experiment": experiment_name or "",
            "provider": provider,
            "model": model,
            "overall": {
                "total_questions": len(tasks),
                "total_tokens_in": token_tot_in,
                "total_tokens_out": token_tot_out,
                "total_tokens": token_tot_in + token_tot_out,
                "cost_usd": overall_cost
            },
            "by_task_type": {
                t: {
                    "count": tok["count"],
                    "tokens_in": tok["tokens_in"],
                    "tokens_out": tok["tokens_out"],
                    "total_tokens": tok["tokens_in"] + tok["tokens_out"],
                    "cost_usd": (estimate_cost(provider, model, tok["tokens_in"], tok["tokens_out"], secrets) or 0.0)
                }
                for t, tok in sorted(token_by_type.items())
            }
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Token summary written to {summary_path}")

    print(f"\n[OVERALL] tasks={len(tasks)}  pass@1={pass1:.3f}  sum_e2e_ms={sum_e2e:.1f}  wall_ms={wall_ms:.1f}")
    print(f"[OVERALL TOKENS] tokens_in={token_tot_in} tokens_out={token_tot_out} cost_usd={overall_cost:.6f}")

    # 可选：另存一份 summary_csv（同样是类型级）
    if summary_csv:
        with open(summary_csv, "w", encoding="utf-8") as f:
            f.write("type,n,pass,pass_rate,e2e_avg_ms,ttft_avg_ms\n")
            for t in sorted(agg.keys()):
                s = agg[t]; n = s["n"]; ok_t = s["ok"]
                e2e_avg = (s["e2e_sum"]/n) if n else 0.0
                ttft_avg = (s["ttft_sum"]/n) if n else 0.0
            f.write(f"{t},{n},{ok_t},{(ok_t/n if n else 0):.6f},{e2e_avg:.3f},{ttft_avg:.3f}\n")

    print(f"[DONE] Pass@1 = {ok}/{len(tasks)} = {pass1:.3f} ; errors={errors}. 结果已保存到 {out_csv}")
    result = {
        "n": len(tasks), "pass1": pass1, "errors": errors,
        "out_csv": out_csv, "provider": provider, "model": model,
        "sum_e2e_ms": sum_e2e, "wall_ms": wall_ms,
        "tokens_in": token_tot_in,
        "tokens_out": token_tot_out,
        "cost_usd": overall_cost,
        "by_type": {
            t: {
                "n": s["n"],
                "ok": s["ok"],
                "pass_at_1": (s["ok"]/s["n"] if s["n"] else 0.0),
                "e2e_avg_ms": (s["e2e_sum"]/s["n"] if s["n"] else 0.0),
                "ttft_avg_ms": (s["ttft_sum"]/s["n"] if s["n"] else 0.0),
                "tokens_in": token_by_type[t]["tokens_in"],
                "tokens_out": token_by_type[t]["tokens_out"],
                "cost_usd": estimate_cost(provider, model, token_by_type[t]["tokens_in"], token_by_type[t]["tokens_out"], secrets) or 0.0,
            } for t, s in agg.items()
        }
    }
    result["failures"] = failures
    if collector and analysis_dir:
        collector.save_summary(analysis_dir)
        result["error_analysis_dir"] = analysis_dir
    return result


# %%
# 直到做对为止的评测

def run_until_type_correct(
    dataset_root: str,
    provider: str,
    model: str,
    types: List[str],
    max_attempts_per_type: int = 6,      # 每个题型最多尝试次数（=最多换多少题）
    max_pool_per_type: int = 50,         # 每类最多预取多少题作为“候选池”（≥ max_attempts_per_type）
    secrets_file: str = "./secrets.yaml",
    timeout_sec: float = 120.0,
    prompts_file: Optional[str] = None,
    prompt_mode: str = "auto",
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    out_csv: str = "until_type_correct.csv",
    log_attempt_rows: bool = False,      # 是否在同一 CSV 中追加每次尝试明细
    retry_sleep_ms: int = 150,
    cache_bust: bool = True,
    stream: bool = False,
    thinking: bool = False,
    thinking_options: Optional[Dict[str, Any]] = None,
    collect_tokens: bool = False,
    token_log_path: Optional[str] = None,
    token_summary_path: Optional[str] = None,
    collect_reasoning: bool = False
) -> Dict[str, Any]:
    """
    新实验：按“题型”为单位，若一道题做错则换下一道，直到该题型首次做对或达到最大尝试次数。
    进度指示：
      - 每进入一个题型时打印“开始评测某题型（最多N次）”
      - 每次尝试前打印“[Type] Attempt a/b • PID=...”
      - 每次尝试后打印“↳ OK/FAIL/ERROR  e2e=..ms  cum=..ms”
      - 每个题型结束打印“总结：attempts / cum_ms / success 与首个命中PID”
    Args:
        thinking: 是否启用各 Provider 的 thinking/reasoning 模式
        thinking_options: thinking 模式的附加配置
        collect_tokens: 是否统计 token 并写入日志/汇总
        token_log_path: 若提供则输出详细 token 日志 CSV
        token_summary_path: 若提供则输出 token 汇总 JSON
        collect_reasoning: 是否要求模型返回 reasoning 字段
    """
    import os, uuid, time, random, csv

    # Provider / 配置
    secrets = load_secrets(secrets_file)
    prompts_cfg = _load_prompts_yaml(prompts_file) if prompts_file else {}
    prov = make_provider(
        provider,
        model,
        secrets,
        timeout_sec,
        thinking_enabled=thinking,
        thinking_options=thinking_options or {}
    )

    token_tot_in = 0
    token_tot_out = 0
    token_by_type = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0})
    token_log_writer = None
    token_log_file = None
    if collect_tokens and token_log_path:
        os.makedirs(os.path.dirname(token_log_path) or ".", exist_ok=True)
        token_log_file = open(token_log_path, "w", encoding="utf-8", newline="")
        token_log_writer = csv.writer(token_log_file)
        token_log_writer.writerow([
            "phase", "provider", "model", "type", "puzzle_id", "attempt_idx",
            "tokens_in", "tokens_out", "ttft_ms", "e2e_ms", "reasoning"
        ])

    # CSV 头
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    need_header = (not os.path.exists(out_csv)) or (os.path.getsize(out_csv) == 0)
    outp = open(out_csv, "a", encoding="utf-8")
    if need_header:
        outp.write("kind,provider,model,type,puzzle_id,attempt_idx,cumulative_ms,pass1,notes\n")
        outp.flush()

    overall = {"by_type": {}, "sum_attempts": 0, "sum_cum_ms": 0.0, "sum_pass1": 0, "n_types": 0}

    for t in types:
        print(f"\n========== [{t}] 开始评测（最多 {max_attempts_per_type} 次尝试） ==========", flush=True)

        # 构建题池
        pool_tasks = build_tasks(
            dataset_root=dataset_root,
            types=[t],
            max_per_type=max_pool_per_type,
            prompts_cfg=prompts_cfg,
            prompt_prefix=prompt_prefix,
            prompt_suffix=prompt_suffix,
            prompt_mode=prompt_mode
        )
        random.shuffle(pool_tasks)

        attempts = 0
        cumulative = 0.0
        success = 0
        first_success_pid = ""
        last_err = ""

        for task in pool_tasks:
            if attempts >= max_attempts_per_type:
                break

            attempts += 1
            schema = build_json_schema(task.type)

            pr = task.prompt
            if cache_bust:
                pr = pr + f"\n\n[IGNORE THIS LINE] nonce={uuid.uuid4().hex} attempt={attempts}"

            print(f"[{t}] Attempt {attempts}/{max_attempts_per_type} • PID={task.puzzle_id}", flush=True)

            try:
                raw, parsed, meta = prov.infer(
                    prompt=pr, images=task.images, json_schema=schema, stream=stream
                )
                e2e = float(meta.get("e2e_ms") or 0.0)
                cumulative += e2e
                ok = evaluate_pass1(task, parsed)
                status = "OK" if ok else "FAIL"
                print(f" ↳ {status}  e2e={e2e:.1f}ms  cum={cumulative:.1f}ms", flush=True)
            except Exception as e:
                ok = False
                last_err = f"{type(e).__name__}: {e}"
                meta = {"e2e_ms": 0.0, "ttft_ms": 0.0, "tokens_in": 0, "tokens_out": 0}
                print(f" ↳ ERROR {last_err}", flush=True)

            tokens_in = int((meta.get("tokens_in") or 0))
            tokens_out = int((meta.get("tokens_out") or 0))
            token_tot_in += tokens_in
            token_tot_out += tokens_out
            token_by_type[t]["tokens_in"] += tokens_in
            token_by_type[t]["tokens_out"] += tokens_out

            reasoning_txt = None
            if collect_reasoning and isinstance(parsed, dict):
                r = parsed.get("reasoning")
                if isinstance(r, str) and r.strip():
                    reasoning_txt = r.strip()

            if token_log_writer:
                token_log_writer.writerow([
                    "attempt",
                    provider,
                    model,
                    t,
                    task.puzzle_id,
                    attempts,
                    tokens_in,
                    tokens_out,
                    f"{meta.get('ttft_ms', 0.0):.1f}",
                    f"{e2e:.1f}",
                    reasoning_txt or ""
                ])

            if log_attempt_rows:
                outp.write(f"attempt,{provider},{model},{t},{task.puzzle_id},{attempts},{cumulative:.1f},{int(ok)},{last_err}\n")
                outp.flush()

            if ok:
                success = 1
                first_success_pid = task.puzzle_id
                print(f"[{t}] 🎯 首次命中：PID={first_success_pid}  用时累计={cumulative:.1f}ms  尝试次数={attempts}", flush=True)
                break

            time.sleep(retry_sleep_ms / 1000.0)

        # 类型汇总行
        outp.write(f"summary,{provider},{model},{t},{first_success_pid},{attempts},{cumulative:.1f},{success},{last_err}\n")
        outp.flush()

        if token_log_writer:
            token_log_writer.writerow([
                "summary",
                provider,
                model,
                t,
                first_success_pid,
                attempts,
                token_by_type[t]["tokens_in"],
                token_by_type[t]["tokens_out"],
                "",
                f"{cumulative:.1f}",
                ""
            ])

        print(f"[{t}] 总结：attempts={attempts}  cum_ms={cumulative:.1f}  success={success}  first_pid={first_success_pid or '-'}", flush=True)

        overall["by_type"][t] = {
            "attempts": attempts,
            "cumulative_ms": cumulative,
            "pass1": success,
            "first_success_pid": first_success_pid
        }
        overall["sum_attempts"] += attempts
        overall["sum_cum_ms"] += cumulative
        overall["sum_pass1"] += success
        overall["n_types"] += 1

    outp.close()

    # overall 宏观指标（按类型取平均）
    n = max(1, overall["n_types"])
    overall["avg_attempts_per_type"] = overall["sum_attempts"] / n
    overall["avg_cum_ms_per_type"] = overall["sum_cum_ms"] / n
    overall["pass_rate_types"] = overall["sum_pass1"] / n
    overall["out_csv"] = out_csv
    overall["tokens_in"] = token_tot_in
    overall["tokens_out"] = token_tot_out

    print(f"\n[UNTIL-TYPE] types={types}  pass_rate={overall['pass_rate_types']:.3f}  "
          f"avg_attempts={overall['avg_attempts_per_type']:.2f}  "
          f"avg_cum_ms={overall['avg_cum_ms_per_type']:.1f}  -> {out_csv}", flush=True)

    if token_log_file:
        token_log_file.flush()
        token_log_file.close()

    if collect_tokens and token_summary_path:
        os.makedirs(os.path.dirname(token_summary_path) or ".", exist_ok=True)
        with open(token_summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "provider": provider,
                "model": model,
                "overall": {
                    "tokens_in": token_tot_in,
                    "tokens_out": token_tot_out,
                    "total_tokens": token_tot_in + token_tot_out
                },
                "by_type": {
                    typ: {
                        "tokens_in": data["tokens_in"],
                        "tokens_out": data["tokens_out"],
                        "total_tokens": data["tokens_in"] + data["tokens_out"]
                    } for typ, data in token_by_type.items()
                }
            }, f, indent=2, ensure_ascii=False)

    return overall

# %%
def main():
    """
    命令行入口：解析参数并调用 run_eval（支持 prompts-file / prefix / suffix）
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True, help="./captcha_data")
    parser.add_argument("--types", nargs="+", required=True, help="评测的类型（如 Dice_Count Geometry_Click ...）")
    parser.add_argument("--provider", default="openai", help="openai|anthropic|gemini|fireworks")
    parser.add_argument("--model", default="gpt-4o-mini", help="模型名称")
    parser.add_argument("--max-per-type", type=int, default=15, help="每类最多题数")
    parser.add_argument("--out-csv", default="results.csv", help="输出 CSV 路径")
    parser.add_argument("--secrets-file", default="./secrets.yaml", help="密钥配置文件路径")
    parser.add_argument("--no-stream", action="store_true", help="禁用流式（便于 usage/成本估算）")
    parser.add_argument("--estimate-cost", action="store_true", help="启用成本估算（多需非流式）")
    parser.add_argument("--timeout-sec", type=float, default=120.0, help="单请求超时秒数")
    
    parser.add_argument("--prompts-file", default=None, help="Prompt 覆写文件（yaml/json），键为任务类型或 default")
    parser.add_argument("--prompt-prefix", default="", help="拼接到每题 prompt 前面的字符串")
    parser.add_argument("--prompt-suffix", default="", help="拼接到每题 prompt 后面的字符串")
    parser.add_argument("--prompt-mode", choices=["auto","gt","opt"], default="auto",
                        help="Prompt 来源：gt=用 GT 原始；opt=用 prompts.yaml；auto=GT>yaml>default")
    parser.add_argument("--summary-csv", default=None, help="另存按题型汇总 CSV")
    parser.add_argument("--enable-thinking", action="store_true", help="启用各 Provider 的思考/推理扩展（若支持）。")
    parser.add_argument("--thinking-config", default=None, help="Thinking 配置（JSON 字符串），如 '{\"effort\":\"medium\"}'.")
    parser.add_argument("--collect-reasoning", action="store_true",
                        help="要求模型输出 reasoning 字段（可能增加耗时与成本）")
    
    parser.add_argument("--until-correct-type", default=None, 
                        help="只对该类型执行 '直到做对' 实验, 如 Dice_Count。当此项为None时，执行常规评测;否则需使用run_until_correct(...)")
    parser.add_argument("--max-attempts", type=int, default=10, help="'直到做对'的最大尝试次数")
    parser.add_argument("--retry-sleep-ms", type=int, default=200, help="'直到做对'的尝试间隔毫秒数")
    parser.add_argument("--no-cache-bust", action="store_true", help="禁用 '直到做对' 的 cache-bust nonce")


    args = parser.parse_args()

    thinking_options = None
    if args.thinking_config:
        try:
            thinking_options = json.loads(args.thinking_config)
            if not isinstance(thinking_options, dict):
                raise ValueError("thinking_config 需是 JSON 对象")
        except Exception as exc:
            raise SystemExit(f"解析 --thinking-config 失败: {exc}")
    thinking_enabled = args.enable_thinking or bool(thinking_options)

    if args.until_correct_type:
        # === Experiment 3: until-correct for one type ===
        run_until_type_correct(
            dataset_root=args.dataset_root,
            provider=args.provider,
            model=args.model,
            types=[args.until_correct_type],
            max_attempts_per_type=args.max_attempts,
            max_pool_per_type=args.max_per_type,
            secrets_file=args.secrets_file,
            timeout_sec=args.timeout_sec,
            prompts_file=args.prompts_file,
            prompt_mode=args.prompt_mode,
            prompt_prefix="",                 # 如需全局前后缀可加
            prompt_suffix="",
            out_csv=args.out,
            retry_sleep_ms=args.retry_sleep_ms,
            cache_bust=(not args.no_cache_bust),
            stream=(not args.no_stream),
            thinking=thinking_enabled,
            thinking_options=thinking_options
        )
    else:
        # === Experiments 1 & 2: standard evaluation (GT vs OPT) ===
        run_eval(
            dataset_root=args.dataset_root,
            types=args.types,
            provider=args.provider,
            model=args.model,
            max_per_type=args.max_per_type,
            out_csv=args.out,
            secrets_file=args.secrets_file,
            stream=(not args.no_stream),
            estimate_cost_flag=args.estimate_cost,
            timeout_sec=args.timeout_sec,
            prompts_file=args.prompts_file,
            prompt_prefix="",
            prompt_suffix="",
            prompt_mode=args.prompt_mode,     # 关键：gt / opt / auto
            summary_csv=args.summary_csv,
            thinking=thinking_enabled,
            thinking_options=thinking_options,
            collect_reasoning=args.collect_reasoning
        )


# %%
from google import genai
client = genai.Client(api_key="REDACTED_GEMINI_API_KEY")

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="I am test from local IDE. Say hello."
)
print("TEXT OK:", bool(getattr(response, 'text', None)), getattr(response, 'text', "")[:120])


# %%


# %% [markdown]
# ### 实验一

# %%
# 程序运行入口
'''
import traceback
try:
    all_types = list(SUPPORTED_TYPES)
    
    res = run_eval(
    dataset_root="./captcha_data",
    secrets_file="./secrets.yaml",
    prompt_mode="gt",
    #out_csv="./results/results_exp1_g25_flash_lite.csv",
    #out_csv="./results/results_exp1_g25_flash.csv",
    #out_csv="./results/results_exp1_g25_pro.csv",
    #out_csv="./results/results_exp1_g41.csv",
    #out_csv="./results/results_exp1_g4o.csv",
    out_csv="./results/test.csv",

    
    
    # 'Patch_Select', 'Connect_Icon', 'Path_Finder', 'Dart_Count', 'Object_Match', 
    # 'Click_Order', 'Geometry_Click', 'Select_Animal', 'Bingo', 'Image_Recognition', 
    # 'Dice_Count', 'Unusual_Detection', 'Coordinates', 'Place_Dot', 'Image_Matching', 
    # 'Pick_Area', 'Rotation_Match', 'Misleading_Click'

    types= ["Image_Matching"], # all_types,  #["Image_Matching"]

    #provider="gemini", model="gemini-2.5-flash-lite",
    provider="gemini", model="gemini-2.5-flash",
    #provider="gemini", model="gemini-2.5-pro",
    #provider="openai", model="gemini-4.1",
    #provider="openai", model="gpt-4o",
    #provider="openai", model="gpt-5",
    
    # ===== Thinking Options =====
    thinking=True,  # 开启 thinking
    thinking_options={
        "mode": "dynamic",  # mode：dynamic/ disabled/ 默认固定预算
        "thinking_budget": 8192  # Token 预算（可选，mode 会覆盖此值）
        },
    
    
    
    # prompts_file="./prompts.yaml",   # ← 新增
    prompt_prefix="",                # ← 全局前缀（可选）
    prompt_suffix="",                # ← 全局后缀（可选）
    
    estimate_cost_flag=False,
    timeout_sec=120.0,
    max_per_type=10,
    stream=False
    )

    print(res)
except Exception as e:
    traceback.print_exc()     # ← 打印真正的异常和栈
    raise



# %% [markdown]
# ### 实验二

# %%
from pathlib import Path

def _exp2_all_types() -> list[str]:
    """
    返回当前代码里受支持的全部题型（按名称排序，避免不同平台的set顺序不稳定）。
    """
    try:
        return sorted(list(SUPPORTED_TYPES))
    except NameError:
        raise RuntimeError("SUPPORTED_TYPES 未定义，请确认粘贴位置在 run_eval.py 内部。")

def exp2_run_auto_only(
    dataset_root: str = "./captcha_data",
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    prompts_file: str = "./prompts.yaml",
    out_csv: str = "results_exp2_auto.csv",
    max_per_type: int = 10,
    seed: int = 42,
    timeout_sec: float = 120.0,
    stream: bool = False,
    secrets_file: str = "./secrets.yaml",
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    summary_csv: str | None = None
):
    """
    实验二（唯一版本）：使用 prompt_mode='auto' 跑全部题型。
    - 'auto'：若题目自带 per-item 文案则按 merge 追加类型规则，否则按 opt。
    """
    pf = Path(prompts_file)
    if not pf.exists():
        raise FileNotFoundError(f"prompts_file 不存在：{pf}. 请先把 prompts.yaml 放到本地。")

    types = ["Click_Order"]  
    print(f"[EXP2-AUTO] 计划评测类型：{types}")

    return run_eval(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_per_type=max_per_type,
        out_csv=out_csv,
        secrets_file=secrets_file,
        stream=stream,                     # 建议 False，E2E更稳；要TTFT可改 True
        estimate_cost_flag=False,
        timeout_sec=timeout_sec,
        seed=seed,
        prompts_file=str(pf),
        prompt_prefix=prompt_prefix,
        prompt_suffix=prompt_suffix,
        prompt_mode="auto",                # ★ 仅此：实验二的优化 prompts 主设定
        summary_csv=summary_csv
    )

exp2_run_auto_only(
    dataset_root="./captcha_data",
    provider="openai",                 # 或 gemini / anthropic / fireworks
    model="gpt-4o",               
    prompts_file="./prompts_optimized.yaml",
    
    out_csv="./results/test_exp2.csv",
    #out_csv="./results/results_exp2_g25_flash_lite.csv",
    #out_csv="./results/results_exp2_g25_flash.csv",
    #out_csv="./results/results_exp2_g25_pro.csv",
    
    #out_csv="./results/results_exp2_gpt41.csv",
    #out_csv="./results/results_exp2_gpt4o.csv",
    
    
    max_per_type=10, 
    seed=42, 
    stream=False
)

# %% [markdown]
# ### 实验三

# %%
import traceback
try:
    all_types = list(SUPPORTED_TYPES)

    overall = run_until_type_correct(
        dataset_root="./captcha_data",
        types=all_types,
        max_attempts_per_type=8,       # 每个题型最多换 x 道题
        max_pool_per_type=50,          # 每类最多从题库拿 x 道作为候选
        secrets_file="./secrets.yaml",
        prompts_file="./prompts_optimized.yaml", # 若做“优化提示”的实验，打开这个
        prompt_mode="auto",              # 实验一：只用 GT 文案（你也可改为 "merge"/"opt"）
        
        #provider="gemini", model="gemini-2.5-flash-lite",
        #provider="gemini", model="gemini-2.5-flash",
        #provider="gemini", model="gemini-2.5-pro",
        #provider="openai", model="gpt-4.1",
        provider="openai", model="gpt-4o",
        #provider="openai", model="gpt-5",
        
        #out_csv="./results/results_exp3_OPT_g25_flash_lite.csv",
        #out_csv="./results/results_exp3_OPT_g25_flash.csv",
        #out_csv="./results/results_exp3_OPT_g25_pro.csv",
        #out_csv="./results/results_exp3_OPT_g41.csv",
        out_csv="./results/results_exp3_OPT_g4o.csv",
        
        
        log_attempt_rows=False,        # 如需每次尝试的明细，把它改为 True
        stream=False
    )


except Exception as e:
    traceback.print_exc()     # ← 打印真正的异常和栈
    raise

'''
