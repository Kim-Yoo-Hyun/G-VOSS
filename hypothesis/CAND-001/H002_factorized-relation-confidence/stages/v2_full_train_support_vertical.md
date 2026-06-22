# v2 Full-Train Support/Vertical

Last updated: 2026-06-22 KST

## Purpose

v2의 목적은 full train으로 확장해 `support_contact`와 `relative_vertical`에서 H002 target을
더 안정적으로 만들 수 있는지 확인하는 것이었다. 이 두 family는 relation-specific geometry
witness가 비교적 명확하다.

## What Was Done

- Open3DSG train full raw dump와 adapter export를 만들었다.
- geometry join, RGA rows, support/vertical audit packet을 구성했다.
- Codex proxy, human proxy, external review proxy, user-confirmed review 등 여러 label source를 시도했다.
- source feature join과 raw witness factor join을 수행했다.
- controlled posterior smoke와 error analysis를 반복했다.

## Result

`support_contact`와 `relative_vertical`에서는 raw geometry witness가 일부 유망한 신호를 보였다.
특히 contact, vertical order, overlap, coverage를 분리해서 저장하는 설계는 H002의 factorized
representation과 잘 맞았다.

## Problem

target은 여전히 충분히 독립적이지 않았다.

- prior label carryover risk가 있었다.
- endpoint/object identity만으로 target이 설명되는 구간이 있었다.
- posterior gain이 있더라도 clean target이 아니면 method evidence로 방어하기 어려웠다.

## Why Next Stage

full-train으로 확장해도 문제가 combiner capacity가 아니라 target construction임이 더 분명해졌다.
그래서 positive mass와 endpoint/object shortcut을 직접 다루는 v3 target으로 이동했다.

## Boundary

v2는 full-train H002 pipeline과 factor schema를 만든 단계다. Posterior claim은 아직 금지된다.
