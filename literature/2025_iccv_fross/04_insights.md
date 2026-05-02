# Insights

## Facts

- FROSS lifts 2D scene graphs to 3D and merges them online using 3D Gaussian object representations.
- It introduces ReplicaSSG with inter-object relationship annotations.
- It reports faster-than-real-time operation at about 144 FPS.
- Using ground-truth 2D scene graphs dramatically improves final 3D SSG performance.

## Paper Claims

- Precise object pose and shape are not always necessary for high-level 3D semantic scene graph reasoning.
- Gaussian object representations are sufficient for efficient online global SSG generation.

## Inferences

- FROSS is useful if CAND-001 later targets online or embodied settings, but it is probably not the right first benchmark for fine geometry grounding.
- ReplicaSSG may be valuable for evaluating relation-guided query success or online graph maintenance, but 3DSSG is still the safer first benchmark.
- The gap between predicted and ground-truth 2D SG performance suggests that relation proposal quality is a bottleneck independent of geometry verification.

## Connection to Field Trends

- Anchors the dynamic / online / real-time 3D SSG trend.
- Shows that evaluation is expanding beyond label recall into latency and online usability.

## Possible Contribution Angles

- Add a geometry-consistency post-filter to FROSS relation edges.
- Use ReplicaSSG as a secondary benchmark after a 3DSSG-based prototype.
- Test whether geometry verification can mitigate errors from noisy 2D SG proposals.

## What Would Change This Assessment

- If ReplicaSSG provides high-quality geometry annotations and accessible meshes/poses, it may become more useful earlier for CAND-001.

