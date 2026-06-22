# v7 Object-Cell Evidence Contrast

Last updated: 2026-06-22 KST

## Purpose

v7은 v6에서 남은 object/category shortcut을 직접 겨냥했다. 같은 object/category cell 안에서도
reliability 차이가 남는지 확인하는 것이 목표였다.

## What Was Done

- object-cell evidence contrast feasibility scan을 수행했다.
- 240-row queue를 만들고 family/bucket/object-cell balance를 맞췄다.
- partial packet gap을 audit하고 replacement mining을 수행했다.
- label fill, ingestion, target-independence audit를 수행했다.

## Result

object-cell balance는 이전보다 더 강한 control이었다. 하지만 target을 독립적으로 만들기에는
여전히 부족했다.

## Problem

- `subject_object_family_cell`, `strict_group_key`, `subject_object_label_pair`가 target을 설명했다.
- strict/diagnostic controlled slice가 없었다.
- object-cell 분포를 맞추는 것만으로는 endpoint-level shortcut을 제거하지 못했다.

## Why Next Stage

같은 endpoint pair를 고정하고 predicate만 다르게 보는 exact endpoint-pair counterfactual이
필요했다. 그래서 v8로 이동했다.

## Boundary

v7은 object-cell balancing의 한계를 확인한 단계다. Current target remains diagnostic-only.
