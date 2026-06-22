# v5 Cell Contrast

Last updated: 2026-06-22 KST

## Purpose

v5는 object/geometry cell 단위로 더 넓은 contrast를 만들면 reliable/unreliable target mass를
늘릴 수 있는지 확인했다.

## What Was Done

- cell contrast feasibility scan을 수행했다.
- candidate mining, asset packet generation, packet gap audit를 수행했다.
- label readiness, label fill, label ingestion, target-independence audit를 수행했다.
- relation reliability, geometry support, usefulness target을 따로 뽑았다.

## Result

후보 pool은 넓어졌지만, H002 posterior 검증에 필요한 direct reliable/unreliable contrast는
충분히 생기지 않았다.

## Problem

- relation reliability binary target이 약 `31` rows 수준에 머물렀다.
- direct reliable/unreliable pair contrast가 거의 없었다.
- hidden pair/cell/family shortcut risk가 남았다.

## Why Next Stage

binary target으로 억지로 밀면 uncertainty를 hard negative로 오염시킬 가능성이 컸다. H002의
uncertainty factor를 target에도 반영하기 위해 v6로 넘어갔다.

## Boundary

v5는 cell contrast가 단독으로는 posterior-ready target을 만들지 못한다는 negative evidence다.
