# Insights

## Facts

- SCOUT is an arXiv 2026 preprint and official project page says it is under review.
- It searches directly over 3DSGs using utility scores over rooms, frontiers, objects, and containers.
- Utility is based on room-object containment and object-object co-occurrence.
- It distills LLM-generated relational knowledge into lightweight models for on-robot inference.
- It introduces SymSearch, a symbolic benchmark for interactive object search over 3DSGs.
- It reports real-world Toyota HSR experiments.

## Paper Claims

- Generic embedding similarity is weak for relational search semantics.
- LLM-level relational reasoning can be approximated by offline distillation into lightweight models.
- SCOUT outperforms embedding-based baselines and reaches or exceeds LLM-based planning performance with much lower inference time.
- SymSearch enables scalable evaluation of relational semantic reasoning without simulation overhead.

## Inferences

- SCOUT is a strong CAND-003 boundary for object-search tasks. It already covers relation-aware utility scoring over 3DSGs.
- CAND-003 should not frame its novelty as "use relational commonsense to search over 3DSG."
- The gap remains geometry-aware validity: SCOUT's priors say where an object is likely to be, but they do not verify whether an LLM/VLM output is geometrically consistent with observed 3D evidence.
- SymSearch could become a useful benchmark reference if the thesis moves into search, but it may be too downstream for the first verifier prototype.

## Connection to Field Trends

- Strengthens the trend from LLM online reasoning to distilled, efficient, graph-based reasoning.
- Shows that 3DSG task reasoning is becoming benchmarked with task success, SPL, runtime, and real-world transfer.
- Reinforces that CAND-003 must separate semantic prior utility from geometric evidence verification.

## Possible Contribution Angles

- Use SCOUT/SymSearch to motivate relational task-output metrics, but keep first CAND-003 prototype offline.
- Add a geometry-consistency checker to SCOUT-like target decisions: likely location is not enough if relation evidence contradicts the proposed answer.
- Compare LLM prior-based utility and measured relation evidence when they disagree.
- Define failure decomposition: wrong prior, missing object, perception failure, manipulation failure, geometry violation.

## What Would Change This Assessment

- If SCOUT code and SymSearch data become available, they are strong candidates for CAND-003 search-side feasibility checks.
- If CAND-003 moves toward interactive object search, SCOUT becomes a primary baseline.
- If CAND-003 stays as offline spatial QA / graph-query verification, SCOUT should remain a benchmark and motivation reference.
