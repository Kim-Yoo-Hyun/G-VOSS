# RelCompat3D Figure Guide

Last updated: 2026-08-01 KST

This file records the intent, fixed values, and claim boundary of every figure
in the final main paper and technical supplement.

## 1. Common Visual Contract

- Orange marks the subject instance.
- Blue marks the object instance.
- Relation text is shown in quotation marks in captions and prose.
- Main figures use the current outlined PDF assets to avoid font-substitution
  warnings.
- Qualitative ranks are candidate ranks in the corresponding source context.
- A rank change illustrates re-ranking, not correction of the underlying scene
  graph generator.

Active assets:

- `reference_AAAI/figure/Figure1.pdf`;
- `reference_AAAI/figure/Figure2.pdf`;
- `reference_AAAI/figure/Figure3.pdf`;
- `aaai/supplement_figures/Figure4.pdf`.

## 2. Figure 1: High-Scoring Geometric Failure

### Purpose

Figure 1 motivates the paper with a vertical-order candidate that is
semantically readable but inconsistent with the reconstructed ordered-pair
geometry.

### Fixed case

- Predictor: Open3DSG.
- Candidate: “desk higher than ceiling”.
- Source rank: 6.
- RelCompat3D-Linear rank: 425.
- Top-\(50\) membership: in to out.

The point-cloud view places the desk below the ceiling. The figure demonstrates
the failure mode and one qualitative outcome. It does not establish aggregate
performance.

### Final caption contract

The caption identifies the source predictor, ordered pair, contradiction,
before/after ranks, and top-\(50\) consequence. The relation phrase remains in
plain quotation marks rather than `\texttt`.

## 3. Figure 2: Compatibility and Re-Ranking Overview

### Purpose

Figure 2 explains the complete inference flow and provides a proximity
demotion example.

### Panel (a)

- Ordered pair: heater \(\rightarrow\) close by \(\rightarrow\) trash can.
- Heater instance: 14.
- Trash-can instance: 24.
- XY center distance: \(4.33\,\mathrm{m}\).

### Panel (b)

The diagram separates:

1. predicate semantics \(T\);
2. ordered-pair measurements \(G\);
3. source relation score \(Z\).

Only \(T\) and \(G\) enter predicate--geometry compatibility. \(Z\) bypasses
the estimator and is combined with compatibility in the within-family score.
Family-aware re-ranking then preserves the source family sequence.

### Fixed outcome

- Source rank: 19.
- RelCompat3D-Linear rank: 178.

The asset, caption, Method description, and Results prose agree on the distance,
variant, and ranks.

### Source material and regeneration

The case is traceable to the following evaluation record:

- Scan: `4fbad32f-465b-2a5d-8408-146ab1d72808`.
- Context: subgraph 2.
- Subject: heater instance 14.
- Object: trash-can instance 24.
- View: top-down XY.

The locally preserved
`archive/local/pre_submission_20260722/previous_archive/experiments/H001_geom_reliability/pre_submission_20260722/no_family_indicator_v1/candidate_figures/qualitative_cases.json`
contains the subject and object centers, bounding-box extents, plot bounds,
\(4.329476\,\mathrm{m}\) XY distance, ranks, scores, and verifier status.
The same folder contains `figure3_qualitative.svg`, whose panel (a) is an
already rendered top-down XY plot for this pair. PDF and PNG renderings are
preserved in the adjacent `candidate_paper/` folder.

An RGB or full point-cloud view can be regenerated after restoring the licensed
3RScan/Open3DSG runtime data. The archived records point to
`data_dict_2.pkl` under the scan's Open3DSG `preprocessed/` directory and to
`4fbad32f-465b-2a5d-8408-146ab1d72808_object2image.pkl` under `views/`.
These large runtime files are not present in the compact local snapshot. A
3RScan point-cloud rendering can instead be reconstructed from
`labels.instances.annotated.v2.ply` after the licensed scan is restored.

### Label-free XY panel regeneration

The preferred replacement for the left side of Figure 2 is a data-backed XY
plot without the strings `heater`, `trash can`, or the instance identifiers.
The plot should retain only the preserved endpoint projections, their center
markers, the center-to-center segment, and the \(x/y\) axes. Both XY envelopes
are omitted because the heater record contains a room-scale extent that is not
a reliable depiction of its visible object size. The distance annotation is
also omitted from the panel, while the renderer still validates the
\(4.329476\,\mathrm{m}\) value. The relation phrase and measured distance
remain available in the framework caption and prose.

Use the `open3dsg_case_001` record in `qualitative_cases.json` as the source of
the plot geometry:

- subject center: \((3.339991,-1.557010)\);
- object center: \((0.064108,1.273705)\);
- subject XY envelope: \(x\in[0,3.89]\), \(y\in[-3.15582,0.342309]\);
- object XY envelope: \(x\in[-0.095635,0.29]\), \(y\in[0,1.48598]\);
- plot limits: \(x\in[-0.494198,4.288563]\),
  \(y\in[-3.62,1.95016]\).

The first validation is

\[
\left\|(3.339991,-1.557010)-(0.064108,1.273705)\right\|_2
=4.329475\ldots\,\mathrm{m},
\]

which rounds to the reported \(4.33\,\mathrm{m}\). Do not move the two centers
independently for layout. If the view is rotated or reflected, apply the same
rigid transformation to the scene points, both envelopes, and both centers.

The rendering procedure is:

1. Load the scan or subgraph points in the same coordinate frame as the case
   record. Prefer the Open3DSG `data_dict_2.pkl` after restoring it. A restored
   `labels.instances.annotated.v2.ply` is also usable after applying the same
   preprocessing transform.
2. Project the endpoint points to \((x,y)\), optionally using a fixed
   deterministic subsample. Draw the subject points in orange and the object
   points in blue.
3. Mark the corresponding centers using the same endpoint colors. Do not draw
   either XY envelope.
4. Connect the centers with a dashed line. Do not add a distance label, object
   names, or instance numbers inside the plot.
5. Apply the recorded plot limits and an equal data aspect ratio. Retain only
   the \(x/y\) axes and necessary ticks. Typeset the axis letters and tick
   numbers in Times New Roman at no less than 9.5 pt, then export as SVG or PDF.

A minimal implementation has the following structure:

```python
subject_xy = np.array([3.339991, -1.557010])
object_xy = np.array([0.064108, 1.273705])
distance = np.linalg.norm(subject_xy - object_xy)
assert np.isclose(distance, 4.329476, atol=1e-6)

ax.scatter(subject_points[:, 0], subject_points[:, 1],
           s=2.8, c="#D55E00", alpha=0.42, linewidths=0)
ax.scatter(object_points[:, 0], object_points[:, 1],
           s=2.8, c="#0057B8", alpha=0.42, linewidths=0)
ax.plot(*subject_xy, "o", color="#D55E00")
ax.plot(*object_xy, "o", color="#0072B2")
ax.plot([subject_xy[0], object_xy[0]],
        [subject_xy[1], object_xy[1]], "--", color="#1f4e9e")
ax.set_xlim(-0.494198, 4.288563)
ax.set_ylim(-3.62, 1.95016)
ax.set_aspect("equal", adjustable="box")
```

The case JSON does not contain per-vertex scene points. It can therefore
reproduce a clean center-and-envelope schematic by itself, but not the gray
scene backdrop. If the licensed runtime data cannot be restored, the existing
`figure3_qualitative.svg` may be cropped to its first geometry plot as a
label-free fallback. That fallback contains the pair geometry but not the full
gray scan projection used in the current Figure 2.

A source-backed draft has been generated under `paper/generated/`:

- `generate_figure2_xy.py`: deterministic renderer;
- `Figure2_xy.svg`: editable vector output;
- `Figure2_xy.pdf`: vector PDF with embedded text;
- `Figure2_xy_outlined.pdf`: font-outlined PDF for paper inclusion;
- `Figure2_xy.png`: 300-dpi preview.

The renderer recovers 260 preserved XY samples for each endpoint from the
archived qualitative SVG and validates the reported distance against the case
record before writing any output. It deliberately does not synthesize the
missing full-scan background. The draft is therefore a faithful pair-geometry
panel, not yet a pixel-equivalent replacement for the current room-level
projection.

## 4. Figure 3: Recall--Violation Trajectories

### Purpose

Figure 3 visualizes the two reported metrics jointly over all five rank
cutoffs. Rightward movement increases Recall and downward movement decreases
Violation.

### Methods

- Source;
- RelCompat3D-Linear;
- RelCompat3D-MLP.

### Fixed coordinates

Each pair is \((\text{Recall},\text{Violation})\) in percent for
\(K=5,10,20,50,100\).

#### VL-SAT

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (41.94, 0.29) | (42.07, 0.15) | (42.09, 0.15) |
| 10 | (63.22, 0.82) | (63.39, 0.57) | (63.47, 0.51) |
| 20 | (80.74, 1.42) | (80.82, 1.14) | (80.92, 1.09) |
| 50 | (92.72, 2.68) | (92.77, 1.97) | (92.72, 1.89) |
| 100 | (96.35, 4.76) | (96.58, 2.95) | (96.50, 2.96) |

#### Open3DSG

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (3.42, 52.05) | (3.73, 0.94) | (3.70, 4.95) |
| 10 | (9.87, 32.89) | (11.38, 2.33) | (11.78, 4.97) |
| 20 | (19.89, 20.99) | (23.62, 3.13) | (24.67, 4.56) |
| 50 | (40.43, 13.87) | (44.18, 3.42) | (46.70, 4.13) |
| 100 | (51.11, 12.42) | (56.85, 3.24) | (59.89, 3.71) |

#### SGFN

| \(K\) | Source | Linear | MLP |
| ---: | --- | --- | --- |
| 5 | (31.17, 2.37) | (31.17, 2.37) | (31.17, 2.37) |
| 10 | (39.75, 3.49) | (39.75, 3.47) | (39.75, 3.47) |
| 20 | (49.12, 3.22) | (49.14, 2.97) | (49.19, 2.96) |
| 50 | (74.02, 3.85) | (74.50, 2.63) | (74.57, 2.58) |
| 100 | (92.35, 6.30) | (93.03, 3.50) | (92.88, 3.50) |

Axis ranges differ by predictor and the caption states this explicitly.

## 5. Supplementary Qualitative Figure

### Purpose

The three-panel figure connects ordered-pair geometry, measured evidence, and
ranking outcome across the three evaluated families. Panel (a) uses the exact
OBB-center distance in a pair-local XY frame. Panels (b) and (c) use preserved
source-backed endpoint samples. The renderer does not synthesize point samples
that are absent from the archived record.

### Panels

| Panel | Ordered relation | Projection and evidence | Ranking outcome |
| --- | --- | --- | --- |
| (a) | desk / close by / chair | Pair-local (x)-(y); XY center distance (0.436\,\mathrm m) | Rank (81\rightarrow30); exact-label proximity candidate promoted |
| (b) | floor / higher than / curtain | Elevation (x)-(z); subject--object center \(\Delta z=-1.02\,\mathrm m\) | Rank (1\rightarrow430); vertical-order candidate demoted |
| (c) | door / lying on / floor | Elevation (x)-(z); vertical bottom--top gap \(-0.06\,\mathrm m\) | Rank (21\rightarrow21); support/contact candidate kept in source order |

The proximity panel uses a pair-local (x)-(y) frame because only the preserved
center distance is shown. A rigid translation and rotation place the midpoint
at the origin and align the two centers with the local x-axis without changing
their distance. The other two panels retain (x)-(z) projections because an XY
view would hide the vertical evidence used in their interpretation.

### Visual contract

- Orange marks denote the ordered subject, and blue marks denote the ordered
  object. Panel (a) shows centers only; panels (b) and (c) also show projected
  endpoint samples.
- A blue dashed segment connects the two centers.
- Each panel reports the ordered relation, geometric measurement, rank change,
  and re-ranking outcome. The plots omit instance IDs and bounding-box
  envelopes.
- Axes use arrowheads and only the ticks needed to read the projection. Panel
  (a) labels (x/y); panels (b) and (c) label (x/z).
- All plot text uses Times New Roman. Tick labels use 20 pt and axis labels use
  24 pt in the 14.4-inch-wide source asset, giving approximately 9.5 pt and
  11.4 pt, respectively, at the final supplement width.
- Orange `#D55E00` and blue `#0072B2` are used consistently with the main
  qualitative figures.

### Regeneration and validation

The paper-facing asset used by `sec/supplement.tex` is
`aaai/supplement_figures/Figure4.pdf`. The preserved source projection is
`generated/qualitative_geometry_source.svg`. It contains 260 projected samples
for each endpoint in panels (b) and (c). The deterministic renderer
`generated/generate_supplement_qualitative.py` recovers those samples,
converts screen coordinates back to the recorded scene coordinates, constructs
the pair-local center plot for panel (a), and validates the proximity distance
and vertical center difference. Its SVG and PNG outputs remain regeneration
sources rather than the included paper asset.

The renderer also writes three graph-only assets for independent placement or
recomposition. These files contain only the projected endpoint samples, center
markers, dashed center connection, axes, and tick labels. They omit panel
titles, relation text, measurements, ranks, and interpretation text.

| Case | Projection | Raster asset | Vector asset |
| --- | --- | --- | --- |
| Proximity promotion | (x)-(y) | `aaai/supplement_figures/proximity_xy.png` | `aaai/supplement_figures/proximity_xy.svg` |
| Vertical-order demotion | (x)-(z) | `aaai/supplement_figures/vertical_order_xz.png` | `aaai/supplement_figures/vertical_order_xz.svg` |
| Support/contact unchanged | (x)-(z) | `aaai/supplement_figures/support_contact_xz.png` | `aaai/supplement_figures/support_contact_xz.svg` |

Each raster asset is 1380 by 1140 pixels at 300 dpi. The proximity case uses
the XY projection, while the vertical-order and support/contact cases use XZ
to preserve their vertical evidence.

Run from the repository root:

```bash
paper/generated/.venv/bin/python \
  paper/generated/generate_supplement_qualitative.py
```

After regeneration, rebuild only the supplement and inspect the figure at its
final two-column size. The main paper is frozen and does not use this asset.

Panel (a) visualizes the promotion case reported in the supplementary prose.

## 6. Verification

Before upload:

1. include only the current outlined main assets;
2. confirm Figure 1--3 and Table 1--3 occur within the seven technical pages;
3. confirm no Type 3, CID/Identity, or unembedded fonts;
4. compare Figure 3 coordinates against Table 1;
5. rebuild the canonical PDFs after any source wording change.

The final canonical build and extracted-release rebuild pass these checks.
