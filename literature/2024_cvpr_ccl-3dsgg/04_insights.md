# Insights

## Facts

- CCL-3DSGG uses CLIP-driven text/image alignment to train a 3DSG feature extractor.
- It defines open-vocabulary and zero-shot 3DSGG tasks using base/novel class splits.
- It reports strong 3DSSG results in close-set, open-vocabulary, and zero-shot settings.

## Paper Claims

- Grammar parsing is important because sentence-level text features are too coarse for word-level 3DSG labels.
- Multi-view image contrastive loss helps distinguish spatial predicates.
- CCL-3DSGG can recognize novel object and predicate classes using prompt-feature similarity.

## Inferences

- CCL-3DSGG is a stronger baseline for CAND-001 than Open3DSG if the thesis focuses on zero-shot and open-vocabulary benchmark numbers.
- The lack of geometry-consistency evaluation leaves room for a geometry-grounded refinement layer.
- Because CCL-3DSGG already claims spatial predicate gains from multi-view images, CAND-001 should avoid only saying "add geometry"; it must show explicit relation-level verification or error reduction.

## Connection to Field Trends

- Strengthens the trend from closed-set 3DSG to open-vocabulary/zero-shot 3DSG.
- Confirms that open-vocabulary evaluation can be done with held-out 3DSSG classes.

## Possible Contribution Angles

- Post-hoc geometry verification for CCL-3DSGG predicate outputs.
- A benchmark slice that isolates geometry-sensitive predicates in open-vocabulary/zero-shot splits.
- Comparison between CLIP-aligned semantic confidence and explicit 3D geometry confidence.

## What Would Change This Assessment

- If CCL-3DSGG's internal features already encode enough geometry to reduce explicit violation rates, CAND-001 should focus on interpretability/evaluation rather than model improvement.

