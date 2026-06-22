# v4 Matched Contrast

Last updated: 2026-06-22 KST

## Purpose

v4는 matched contrast를 통해 semantic/rank/object 조건이 비슷한 relation candidate 사이에서
reliable/unreliable 차이가 남는지 확인하려는 단계였다.

## What Was Done

- matched contrast plan을 만들었다.
- candidate mining, asset packet generation, gap audit를 수행했다.
- label readiness, label fill, label ingestion을 수행했다.
- relation reliability, geometry support, usefulness target을 분리했다.
- target-independence audit를 수행했다.

## Result

matched contrast는 target design 방향으로는 타당했다. 단순 high-semantic/low-geometry bucket보다
더 엄격한 비교 구조를 만들 수 있었다.

## Problem

- relation reliability binary target이 약 `47` rows 수준으로 작았다.
- hidden metadata correlation risk가 남았다.
- posterior-ready strict slice가 없었다.

## Why Next Stage

matched contrast만으로는 target mass와 independence를 동시에 확보하지 못했다. 더 넓은
cell-level contrast에서 후보를 찾는 v5로 이동했다.

## Boundary

v4는 matched contrast route의 feasibility diagnostic이다. Posterior smoke input으로 쓰지 않는다.
