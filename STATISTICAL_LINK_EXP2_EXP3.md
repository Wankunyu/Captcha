# Problem Statement

We evaluate each CAPTCHA task type T with model M under two regimes:

- Exp2 (single try): records Pass@1, an empirical estimate of the single‑attempt success probability p = P(success on one attempt).
- Exp3 (until-correct, up to k attempts): each run samples items of type T without reuse within the run. For each run and task type, we record:
  - `attempts` a ∈ {1,…,k}: number of tries used in that run for the first success (or k if failed),
  - `success` s ∈ {0,1},
  - `cumulative_ms`: total time spent across all attempts in that run.
Repeating Exp3 many times yields run-level distributions and empirical means: average success rate q̄ = mean(s), average attempts Ā = mean(a), and average cumulative time.

## Key Questions

- What is the theoretical link between Exp2’s Pass@1 (p) and Exp3’s (q̄, Ā)?
- Under what assumptions do we have:
  - Exp3 success probability q = 1 − (1 − p)^k,
  - Exp3 expected attempts A = E[min(G, k)] where G ~ Geometric(p)?
- How do finite pools, item heterogeneity (p varies across items), and attempt-to-attempt dependence change these relationships?
- Can we estimate p (or the distribution of p across items) from Exp3-only data and check consistency with Exp2?

## Baseline Model (i.i.d. Bernoulli Attempts)

Assumptions: each attempt within a run is independent and identically distributed with success probability p (no learning/fatigue effects; sampling with replacement or a large pool).

- Success probability within k attempts:
  - q = 1 − (1 − p)^k
- Expected attempts (truncated geometric):
  - A = E[min(G, k)] = ∑_{a=1}^k P(G ≥ a) = [1 − (1 − p)^k] / p

Implications:
- Predict Exp3 from Exp2:
  - Given p̂ (Exp2 Pass@1): q̂ ≈ 1 − (1 − p̂)^k, Â ≈ [1 − (1 − p̂)^k] / p̂
- Invert Exp3 to Exp2:
  - Given q̂: p̃ ≈ 1 − (1 − q̂)^(1/k)
  - Given Â and k: solve [1 − (1 − p)^k] / p = Â numerically (monotone in p). When k is large and Â ≈ 1/p, then p ≈ 1/Â.

In the implementation used by this repository (see `exp2_to_exp3_predict.py` and `test_statistic.ipynb`),
these baseline formulas are adopted as the default mapping between Exp2 and Exp3. Finite-pool and
heterogeneity models are used only as optional robustness checks and diagnostics, not as part of the
primary prediction pipeline.

## Time/Cost Mapping

If per‑attempt duration/cost is i.i.d. with mean μ:
- E[cumulative time] ≈ μ × E[min(G, k)] = μ × [1 − (1 − p)^k] / p
- Analogously for cost.

If per‑attempt time depends on attempt index, replace μ with an attempt‑indexed mean vector or fit a regression of time on attempt index.

## Finite Pool (Without Replacement)

If a run samples k distinct items from a finite pool of size N with M “solvable” items (single‑try success viewed as deterministic at the item level):
- q = 1 − C(N − M, k) / C(N, k) where p = M/N
- When N ≫ k, q ≈ 1 − (1 − p)^k (baseline remains a good approximation).

## Item Heterogeneity (Random p Across Items)

Let item‑level success probabilities p_i be random (e.g., p_i ~ Beta(α, β)). Attempts draw independent items each with its own p_i.

- E[q] = 1 − E[(1 − p_i)^k] = 1 − Beta(α, β + k) / Beta(α, β)
- E[min(G_i, k)] = ∑_{r=0}^{k−1} E[(1 − p_i)^r] = ∑_{r=0}^{k−1} Beta(α, β + r) / Beta(α, β)
- Fit (α, β) via method of moments or MLE using observed (q̄, Ā); Exp2’s Pass@1 should match E[p_i] = α/(α + β).

## Dependence Across Attempts

If attempts are not independent (learning, priming, fatigue), let p depend on attempt index: p(1), p(2), … Then:
- q = 1 − ∏_{j=1}^k (1 − p(j))
- A = ∑_{a=1}^k ∏_{j=1}^{a−1} (1 − p(j))

These can be estimated (in principle) from run‑level (a, s) across repeats (k fixed), given enough data.

## Identifiable Likelihood (Exp3‑Only)

For a single run observation (a, s):
- If s = 1 and a ∈ {1..k}: L(p) = p · (1 − p)^{a−1}
- If s = 0 and a = k: L(p) = (1 − p)^k

Across many runs for fixed (T, M, k), the MLE of p under the truncated geometric model exists and can be compared to Exp2’s p̂.

## Validation Plan

- Predictive checks:
  - For each task type, plug Exp2 p̂ into q̂ = 1 − (1 − p̂)^k and Â = [1 − (1 − p̂)^k] / p̂; compare to Exp3 empirical q̄ and Ā (scatter vs y = x).
- Goodness‑of‑fit:
  - QQ/PP plots for attempts, chi‑square on counts of a = 1..k, bootstrap CIs.
- Sensitivity:
  - Vary k and pool size to test finite‑pool vs i.i.d. predictions.
  - Simulate heterogeneity with Beta(α, β) and fit via moments/MLE.
- Extensions:
  - Estimate p or (α, β) from Exp3‑only and compare with Exp2 p̂.
  - Attempt‑indexed p(j) models if dependence is suspected.

## Data We Can Provide

- Exp2 (per task type): Pass@1 p̂, sample size, average per‑attempt time/cost.
- Exp3 (per run, per task type): attempts a, success s, cumulative_ms; repeated across runs; k known.
- Optional: per‑attempt logs (time/tokens) for richer modeling.

## What We Want From the Statistical Study

- Conditions under which the baseline formulas
  - q = 1 − (1 − p)^k
  - A = [1 − (1 − p)^k] / p
  hold for our data.
- Practical inversion recipes to recover p from Exp3 summaries (q̄ or Ā) and quantify uncertainty.
- Assessment of finite‑pool, heterogeneity, and dependence effects; guidance on which assumption set fits each task type best.
- A principled approach to map Exp2 → Exp3 (and vice versa) for success rates, attempts, and time/cost, with diagnostics and confidence intervals.
