# Paper Card

## Problem

VLMs can process indoor scene videos, but they still struggle with metric and spatial reasoning. End-to-end video reasoning and spatial QA fine-tuning couple perception and reasoning, making it hard to tell whether errors come from perception, geometry, or reasoning.

## Core Idea

RieMind decouples perception from reasoning. It represents a static indoor scene as an explicit 3D Scene Graph, then lets an LLM reason through deterministic geometric tools instead of directly ingesting video.

## Input / Output

- Input: static indoor scene represented as a 3DSG, user spatial question from VSI-Bench.
- Output: JSON-style answer with natural-language summary, invoked tool evidence, and key result data.

## Method

- Build a 3DSG with building, floor, room, and object nodes.
- Use ground-truth annotations to instantiate the 3DSG for upper-bound reasoning evaluation.
- Expose scene content through tool namespaces: memory, scene, geometry, location/orientation.
- Require the LLM to resolve object names to persistent node IDs before geometric computation.
- Use tools for dimensions, volumes, areas, distances, positions, orientations, coordinate frames, and egocentric/allocentric projection.

## Main Claims

- Explicit 3DSG grounding improves spatial reasoning compared with base VLMs.
- Structured geometric tools outperform pure end-to-end visual reasoning on metric/static spatial questions.
- Decoupling perception and reasoning gives an interpretable upper bound for spatial reasoning under ideal perception.

## Strengths

- Very direct evidence for CAND-003: LLM task reasoning over 3DSG with explicit geometry tools.
- Separates entity grounding, metric grounding, orientation grounding, frame grounding, and geometric grounding.
- Evaluation isolates reasoning from perception by using ground-truth 3DSG construction.
- Tool traces provide inspectable evidence rather than only final answer accuracy.

## Limitations

- arXiv preprint status as of 2026-04-29.
- Uses ground-truth annotations, so reported performance is an upper bound rather than end-to-end system performance.
- Focuses on static spatial QA, not embodied navigation/search or manipulation execution.
- Relative direction questions still expose reasoning-chain failures, especially for smaller models.
- Code/project page was not found in this pass.

## Relevance to My Research

RieMind is the closest direct competitor for CAND-003 because it already implements explicit 3DSG + deterministic geometric tools for LLM spatial reasoning. CAND-003 must therefore differentiate through task-output verification/refinement, relation evidence provenance, and metrics that separate semantic failure from geometry violation.

## Follow-up Questions

1. Can CAND-001 relation evidence be exposed as a RieMind-style tool interface?
2. Is offline 3DSSG/3RScan relation QA enough to reproduce the key insight without using VSI-Bench?
3. Can verifier rejection/correction be evaluated separately from final answer accuracy?
4. How much of RieMind's gain comes from ground-truth scene graph construction rather than the agent design?
