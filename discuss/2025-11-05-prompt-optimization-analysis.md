# Prompt Optimization Effectiveness Analysis

## Executive Summary

**Overall Performance:**
- **Gemini 2.5 Flash**: +3.9% (45.6% → 49.4%)
  - Net gain: +7 passes out of 180 total
  - 8 tasks improved, 1 degraded, 9 unchanged

**Key Finding:** Prompt optimization shows **limited effectiveness** due to:
1. Some tasks remain impossible despite optimization (0% → 0%)
2. One task (Image_Matching) **degraded significantly** (-50%)
3. Half of tasks (9/18) showed **no change at all**

---

## Detailed Task-Level Analysis (Gemini 2.5 Flash)

### 🟢 Successfully Improved Tasks (8 tasks, +12 passes)

| Task | Exp1 | Exp2 | Δ | Absolute Gain | Key Optimization |
|------|------|------|---|--------------|-----------------|
| **Dart_Count** | 40% | 70% | **+30%** | +3 passes | Clarified sector numbering logic |
| **Misleading_Click** | 60% | 80% | +20% | +2 passes | Emphasized forbidden area avoidance |
| **Coordinates** | 60% | 80% | +20% | +2 passes | Added grid position matching rules |
| **Object_Match** | 80% | 90% | +10% | +1 pass | Prioritized cardinality |
| **Rotation_Match** | 20% | 30% | +10% | +1 pass | Added angular difference formula |
| **Unusual_Detection** | 40% | 50% | +10% | +1 pass | Defined structural vs color criteria |
| **Dice_Count** | 0% | 10% | +10% | +1 pass | Detailed top-face counting rules |
| **Connect_Icon** | 40% | 50% | +10% | +1 pass | Geometric compatibility rules |

**Best performer:** Dart_Count (+30%) - optimized prompt successfully clarified the sector numbering system.

---

### 🔴 Degraded Tasks (1 task, -5 passes)

| Task | Exp1 | Exp2 | Δ | Absolute Loss | Root Cause |
|------|------|------|---|--------------|-----------|
| **Image_Matching** | 90% | 40% | **-50%** | -5 passes | **Misleading tie-breaking rule** |

**Problem:** The optimized prompt includes:
```
If multiple candidates appear valid, choose the smallest index (row-major when in a grid)
```

This rule caused the model to **always predict index=0**, even when the correct answer was a different index.

**Evidence:**
- All 6 errors in Exp2 predicted index=0
- Correct answers were: 4, 4, 1, etc. (not 0)

**Fix:** Remove the tie-breaking rule, as Image_Matching should have only ONE correct answer.

---

### ⚪ Unchanged Tasks (9 tasks, 0 change)

#### Already Perfect (3 tasks)
- **Path_Finder**: 100% → 100%
- **Select_Animal**: 100% → 100%
- **Bingo**: 90% → 90%

#### Still Failing (4 tasks)
- **Geometry_Click**: 0% → 0% (difficult spatial reasoning)
- **Click_Order**: 0% → 0% (cross-image coordination)
- **Place_Dot**: 0% → 0% (endpoint detection)
- **Pick_Area**: 20% → 20% (area size comparison)

#### Minimal Accuracy (2 tasks)
- **Patch_Select**: 10% → 10%
- **Image_Recognition**: 70% → 70%

**Insight:** These tasks require either:
1. Capabilities beyond prompt engineering (spatial reasoning, visual precision)
2. Different optimization strategies (few-shot examples, better task decomposition)

---

## Root Cause Analysis

### Why Is Overall Improvement Only 3.9%?

**Math:**
- Gained: 12 passes from 8 tasks
- Lost: 5 passes from Image_Matching regression
- Net: +7 passes / 180 total = **+3.9%**

**Structural Issues:**

1. **Trade-off Problem:** One bad optimization (Image_Matching) canceled out most gains
2. **Ceiling Effect:** 3 tasks already at 90-100%, no room for improvement
3. **Floor Effect:** 4 tasks at 0-20%, optimization insufficient to help
4. **No Impact Zone:** 9/18 tasks unchanged, suggesting:
   - Prompts already adequate (for perfect tasks)
   - Prompts irrelevant to failure mode (for failing tasks)

---

## Prompt Mode Distribution

From `test_prompts_loading.py` results:

| Mode | Count | Examples |
|------|-------|----------|
| **replace** | 14 tasks | Dice_Count, Place_Dot, Path_Finder, Image_Matching, etc. |
| **merge** | 4 tasks | Geometry_Click, Patch_Select, Select_Animal, Image_Recognition |

**"replace" mode:** Completely replaces ground truth prompt with optimized version
**"merge" mode:** Combines GT prompt (e.g., "Pick a penguin") with optimization rules

---

## Recommendations

### 1. Immediate Fixes

**Fix Image_Matching regression:**
```yaml
Image_Matching: |-
  Task: Choose the SINGLE option visually identical to the reference image.

  Decision order:
  1) Contour/topology
  2) Relative layout and part ratios
  3) Distinctive details (holes/notches/corners)
  4) Color/texture
  5) Text glyph shape (not semantic meaning)

  Indexing Rules:
  - Indices are 0-based (starting from 0, not 1)
  - Index 0 represents the first option
  - If there are N options, valid indices are 0 to N-1
  # REMOVE: - If multiple candidates appear valid, choose the smallest index

  Respond with JSON only, strictly following the provided schema. No extra fields or text.
```

**Expected impact:** Recover 5 lost passes, bringing net improvement to **+6.7%** (+12 passes / 180)

---

### 2. Address Zero-Performance Tasks

**Hard tasks** (Geometry_Click, Click_Order, Place_Dot, Pick_Area):

**Option A: Few-shot Learning**
- Add 2-3 solved examples per task type
- Experiment 4 setup already supports this

**Option B: Task Decomposition**
- Break down complex tasks into sub-steps
- Example for Click_Order:
  ```
  Step 1: Identify all icons in the reference image
  Step 2: Locate each icon in the main image
  Step 3: Return coordinates in reference order
  ```

**Option C: Accept Limitations**
- Some tasks may be inherently difficult for vision-language models
- Document as "model capability gap" rather than prompt issue

---

### 3. Optimize for Different Models

**Current issue:** All optimizations tested only on Gemini 2.5 Flash

**Proposal:** Model-specific prompts
```yaml
Image_Matching:
  default: |-
    # Default prompt

  gemini-specific: |-
    # Optimizations specific to Gemini

  gpt-specific: |-
    # Optimizations specific to GPT
```

---

### 4. Measure Prompt Impact Scientifically

**Current problem:** Can't isolate which specific prompt changes helped/hurt

**Solution:** A/B testing framework
```python
# Test prompt variants
variants = {
    "baseline": "original GT prompt",
    "v1_rules_only": "GT + indexing rules",
    "v2_decision_order": "GT + decision order + rules",
    "v3_full": "complete replacement"
}

for variant_name, prompt_template in variants.items():
    run_experiment(prompt=prompt_template, out_csv=f"results_{variant_name}.csv")
```

---

### 5. Re-run Exp2 with Fixed Image_Matching

After fixing the Image_Matching prompt, re-run Experiment 2:

```bash
# Fix prompts_optimized.yaml first (remove tie-breaking rule)

# Re-run Gemini
python run_single_experiment.py 2 --provider gemini --model gemini-2.5-flash --max-per-type 10

# Run GPT (after recharging API balance)
python run_single_experiment.py 2 --provider openai --model gpt-5 --max-per-type 10
```

**Expected results:**
- Gemini: ~50% pass@1 (currently 49.4%, gain ~0.6% from Image_Matching fix)
- GPT: Unknown (previous run failed due to API quota)

---

## Long-term Strategy

### Phase 1: Stabilize Baseline (Now)
- ✅ Fix Image_Matching prompt
- ✅ Re-run Exp2 with all models
- ✅ Document per-task optimization impact

### Phase 2: Targeted Improvements (Next)
- Focus on 0% tasks with few-shot examples (Exp4)
- A/B test prompt components to isolate effective changes
- Model-specific optimizations

### Phase 3: Advanced Techniques (Future)
- Chain-of-thought prompting for complex tasks
- Multi-stage reasoning for Click_Order, Geometry_Click
- Visual grounding techniques for spatial tasks

---

## Conclusion

**Current state:**
- Prompt optimization provides **modest improvement** (+3.9%)
- One regression (Image_Matching) masks larger gains
- 9/18 tasks unaffected by prompt changes

**After Image_Matching fix:**
- Expected improvement: **~6-7%**
- Still limited by model capabilities on hard tasks

**Key insight:**
Prompt engineering alone has **diminishing returns**. For tasks with 0% baseline, we need:
1. Few-shot learning
2. Better task decomposition
3. Or accept as model capability limits

**Recommended next steps:**
1. Fix Image_Matching prompt
2. Re-run Exp2 for all models
3. Focus Exp4 (few-shot) on the 4 zero-performance tasks
4. Document which tasks benefit from which optimization strategies
