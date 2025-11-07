# Experiment 2 Performance Issue Analysis

## Issue Summary

**Observation:**
- **GPT-5**: Exp1 (GT) Pass@1=0.567 → Exp2 (Opt) Pass@1=0.383 (**-18.3% degradation**)
- **Gemini 2.5 Flash**: Exp1 (GT) Pass@1=0.456 → Exp2 (Opt) Pass@1=0.494 (**+3.9% improvement**)

## Root Causes Identified

### 1. Timing Issue with Path_Finder Fix

**Timeline:**
- Exp2 GPT-5 error analysis: Nov 4, 01:32 (before fix)
- Path_Finder fix commit: Nov 5, 00:45
- Exp2 GPT-5 results.csv: Nov 5, 20:11 (after fix, but using old error analysis)

**Problem:** The experiment was run before the Path_Finder task construction bug was fixed (commit 76798a3).

**Evidence from errors.csv:**
```
Path_Finder: {"answer_type":"multi_select","indices":[0]}
Ground Truth: {"indices_gt": []}
```

Path_Finder was being constructed as multi_select instead of classify, causing **100% failure** (Exp1: 1.000 → Exp2: 0.000).

### 2. Task-Specific Performance Degradation

**Major failures in GPT-5 Exp2:**

| Task Type | Exp1 (GT) | Exp2 (Opt) | Change | Reason |
|-----------|-----------|------------|---------|--------|
| Path_Finder | 1.000 | 0.000 | -1.000 | Task construction bug (before fix) |
| Select_Animal | 1.000 | 0.000 | -1.000 | Need investigation |
| Object_Match | 0.900 | 0.000 | -0.900 | Need investigation |
| Bingo | 1.000 | 0.700 | -0.300 | Prompt change impact |
| Coordinates | 0.900 | 0.600 | -0.300 | Prompt change impact |

**Tasks that improved:**
| Task Type | Exp1 (GT) | Exp2 (Opt) | Change |
|-----------|-----------|------------|---------|
| Dart_Count | 0.400 | 0.800 | +0.400 |
| Dice_Count | 0.000 | 0.100 | +0.100 |
| Misleading_Click | 0.900 | 1.000 | +0.100 |

### 3. Why Gemini Improved While GPT Degraded

**Hypothesis:**

1. **Different prompt sensitivity:**
   - GPT-5 (reasoning model) may prefer simpler, ground-truth prompts
   - Gemini 2.5 Flash benefits from more structured, detailed prompts

2. **Merge mode side effects:**
   - In "auto" mode, tasks with per-item prompts use "merge" mode
   - This creates very long prompts (GT prompt + optimized rules)
   - GPT-5 may be overwhelmed by verbose prompts
   - Gemini may better utilize detailed instructions

3. **Model-specific optimization:**
   - prompts_optimized.yaml was not specifically tuned for GPT-5's reasoning capabilities
   - The optimizations may inadvertently harm reasoning models while helping standard chat models

## Verification Needed

To confirm the root causes, we should:

1. **Re-run Exp2 with current code** (after Path_Finder fix)
   ```bash
   python run_single_experiment.py 2 --provider openai --model gpt-5 --max-per-type 10
   ```

2. **Check Select_Animal and Object_Match failure cases:**
   - Examine why these went from 90-100% to 0%
   - Check if there are similar task construction bugs

3. **Test different prompt modes:**
   ```bash
   # Test "opt" mode (replace, not merge)
   python run_single_experiment.py 2 --provider openai --model gpt-5 --prompt-mode opt

   # Compare with "gt" mode
   python run_single_experiment.py 2 --provider openai --model gpt-5 --prompt-mode gt
   ```

4. **Compare prompt lengths:**
   - Check actual prompts sent to GPT-5 vs Gemini
   - Measure if merge mode creates significantly longer prompts

## Recommendations

1. **Immediate:** Re-run Exp2 with current codebase to get accurate comparison

2. **Short-term:** Investigate Select_Animal and Object_Match failures

3. **Medium-term:** Consider model-specific prompt optimization:
   ```yaml
   # prompts_optimized.yaml
   Dice_Count:
     gpt-5: "Simpler prompt for reasoning models"
     default: "Detailed prompt for chat models"
   ```

4. **Long-term:** Add prompt mode comparison in experiments:
   - Exp2a: prompt_mode="opt" (complete replacement)
   - Exp2b: prompt_mode="merge" (GT + rules)
   - Exp2c: prompt_mode="auto" (current behavior)

## Action Items

- [ ] Re-run Exp2 for GPT-5 with current code
- [ ] Debug Select_Animal 100% failure
- [ ] Debug Object_Match 90% → 0% regression
- [ ] Compare actual prompts sent in Exp1 vs Exp2
- [ ] Test different prompt modes
