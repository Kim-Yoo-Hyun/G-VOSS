# v6 Uncertainty-Aware Shortcut Control

Last updated: 2026-06-22 KST

## Purpose

v6는 relation reliability target을 binary로 강제하지 않고, uncertainty를 별도 state로 유지하는
schema가 더 적절한지 확인했다.

## What Was Done

- `accept_reliable`, `reject_unreliable`, `abstain_uncertain` multiclass target을 만들었다.
- 240-row shortcut-controlled queue를 구성했다.
- asset packets, gap audit, label readiness/fill/ingestion을 수행했다.
- target-independence audit를 수행했다.

## Result

class mass는 v4/v5보다 개선됐다. uncertainty를 분리한 것은 H002의 factorized reliability 관점과
맞았다.

## Problem

class mass가 있어도 target independence가 없었다.

- object/category cell이 target을 강하게 설명했다.
- `subject_object_family_cell_hidden`, `subject_object_label_pair_hidden` 같은 key의 shortcut risk가 컸다.
- target이 쉬워진 이유가 relation reliability가 아니라 sampling construction일 수 있었다.

## Why Next Stage

object/category를 더 강하게 통제한 상태에서 evidence contrast가 남는지 확인해야 했다. 그래서
v7 object-cell evidence contrast로 이동했다.

## Boundary

v6는 uncertainty-aware schema는 유지하되, 현재 sampling만으로는 posterior-ready target이
아님을 보여준다.
