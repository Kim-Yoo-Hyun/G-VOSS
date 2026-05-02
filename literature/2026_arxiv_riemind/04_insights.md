# Insights

## Facts

- RieMind grounds an LLM in an explicit 3DSG and structured geometric tools.
- It evaluates on 4,185 static VSI-Bench questions.
- It uses ground-truth annotations to instantiate the 3DSG.
- Its tool categories include memory, scene, geometry, and location/orientation.
- It reports GPT-4.1 agent + tools average score of 89.5 on the static VSI-Bench evaluation.

## Paper Claims

- Explicit geometric grounding substantially improves spatial reasoning performance.
- Structured representations are a compelling alternative to purely end-to-end visual reasoning.
- Decoupling perception and reasoning helps isolate spatial reasoning ability.

## Inferences

- This is a direct novelty boundary for CAND-003. A thesis cannot simply propose "LLM + 3DSG + geometry tools."
- The remaining gap is not tool access itself, but task-output verification: whether the system can flag and correct invalid answers/actions and report what geometric constraint was violated.
- RieMind's reliance on ground-truth 3DSG makes it a useful upper-bound reference for CAND-003, while CAND-001 can contribute by making relation evidence reliable under real scanned geometry.

## Connection to Field Trends

- Strengthens the trend that LLM/VLM 3D reasoning is moving from graph serialization to structured tool use.
- Supports the idea that geometry should be queried as explicit evidence rather than hidden inside language prompts.
- Shows that evaluation must separate perception quality from reasoning quality.

## Possible Contribution Angles

- Build a smaller CAND-003 first cut using 3DSSG/3RScan relation evidence rather than full VSI-Bench.
- Add a verifier layer that rejects or revises LLM answers when tool-derived geometry contradicts the response.
- Report geometry violation rate, correction precision, and valid-answer preservation in addition to answer accuracy.
- Use RieMind as an upper-bound comparison rather than a reproduction target unless VSI-Bench access is easy.

## What Would Change This Assessment

- If RieMind releases code and annotations, it becomes the first reproduction target for CAND-003.
- If end-to-end 3DSG construction significantly degrades performance, CAND-003 should depend on CAND-001's geometry evidence robustness before moving to full task reasoning.
