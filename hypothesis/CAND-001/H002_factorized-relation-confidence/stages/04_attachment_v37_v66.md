# Stage 04 Attachment V37-V66

## Scope

이 문서는 기존 `v37`부터 `v66`까지의 `attachment_deferred` branch를 병합한 요약이다. 대상
relation은 `attached to`, `hanging on`, `connected to`다.

## 진행한 내용

- `v37-v39`: attachment typed witness schema를 정의하고 raw geometry join/capacity scan/path decision을 진행했다.
- `v40-v44`: v18 attachment candidate mining, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v45-v53`: independent visual/mesh audit packet route를 만들고 source inventory, packet plan/materialization/leakage review, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v54-v64`: endpoint-balanced counterfactual route를 만들고 capacity scan, candidate mining, source inventory, audit packet plan/materialization/leakage review, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v65-v66`: full-train conditional contrast capacity scan과 path decision을 진행했다.

## 핵심 결과

Attachment rows는 full train에서 충분했고 raw pair geometry join도 가능했다. 그러나 OBB/point-cloud
witness만으로는 `attached to`, `hanging on`, `connected to`의 reliability를 안정적으로 판단하기
어려웠다.

반복적으로 확인된 문제는 다음과 같다.

- `connected to`는 functional connection이라 단순 contact/near geometry로 확정하기 어렵다.
- audit packet을 만들고 visual/mesh evidence를 제공해도 primary binary target은 reject-heavy였다.
- endpoint-balanced sampling은 exact endpoint-pair capacity를 크게 만들 수 있었지만, label 후에는
  positive-sparse target으로 무너졌다.
- `attached to`는 strict capacity에서 빠지고 `hanging on`만 strict primary 후보로 남았다.

## 다음 단계로 넘어간 이유

`attached to`와 `connected to`를 main target으로 계속 밀면 shortcut risk가 커진다고 판단했다.
따라서 strict capacity가 남은 `hanging on`으로 scope를 좁혀 별도 branch를 진행했다.

## Boundary

- Attachment branch의 multi-view/mesh는 audit/confirmation evidence일 뿐 model input이 아니다.
- `connected to`는 diagnostic-only로 유지된다.
- Posterior smoke는 target-identifiability gate 전까지 금지된다.
