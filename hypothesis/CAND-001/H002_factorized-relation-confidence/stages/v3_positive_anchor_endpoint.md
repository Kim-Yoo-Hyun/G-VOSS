# v3 Positive Anchor And Endpoint Control

Last updated: 2026-06-22 KST

## Purpose

v3는 relation reliability positive가 너무 sparse한 문제를 줄이고, object/endpoint shortcut을
더 직접 통제하려는 단계였다.

## What Was Done

- positive-anchor sampling을 설계했다.
- object/endpoint-controlled candidate mining을 수행했다.
- informative-anchor target을 구성해 reliable positive, geometry contradiction, trivial negative,
  uncertain/ontology case를 분리하려 했다.
- label fill, ingestion, target-independence audit를 수행했다.

## Result

positive를 의도적으로 모으는 방식은 일부 도움이 됐다. 하지만 reliable/unreliable contrast가
충분히 독립적으로 생긴 것은 아니었다.

## Problem

- 초기 target은 positive-sparse였다.
- 이후 target도 object label, endpoint pair, hidden construction key로 설명되는 경향이 있었다.
- strict controlled slice를 확보하지 못했다.

## Why Next Stage

positive mass만 늘리는 방식은 H002 posterior 검증에 충분하지 않았다. 같은 조건에서 reliable와
unreliable를 더 직접 비교하는 matched contrast가 필요해 v4로 이동했다.

## Boundary

v3는 positive target construction의 실패 원인을 좁힌 단계다. It is diagnostic-only.
