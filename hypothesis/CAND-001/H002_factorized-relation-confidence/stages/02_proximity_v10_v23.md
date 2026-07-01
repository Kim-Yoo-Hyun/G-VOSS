# Stage 02 Proximity V10-V23

## Scope

이 문서는 기존 `v10`부터 `v23`까지의 proximity 계열 stage log를 병합한 요약이다. 세부 artifact는
`artifacts/train_rga_full/open3dsg_train_full/rga/` 아래의 proximity 관련 output이 소유한다.

## 진행한 내용

- `v10-v12`: `close by` / proximity feasibility와 LH-only path decision을 진행했다.
- `v13-v17`: proximity LH-only visible sheet, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v18-v23`: scene/geometry-aware proximity repair plan, candidate mining, label fill, ingestion, target-independence audit, path decision을 진행했다.

## 핵심 결과

Proximity는 full train에서 row 수와 LH 후보가 충분했다. 그러나 current RGA queue에서는
`RGA-HL = 0`, `RGA-LH = 171324`로 관측되어 bidirectional mismatch target이 아니라 LH-only
diagnostic branch로만 성립했다.

Visible-only proxy label과 scene/geometry-aware label을 만들어도 target은 posterior-ready가
되지 않았다.

- visible-only proximity target은 object-pair shortcut이 강했다.
- scene/geometry-aware target은 binary usable row가 생겼지만 reliability positive가 적고,
  strict/diagnostic clear slice가 0개였다.
- `close by`는 H002 generality evidence로 유용하지만, main posterior target으로 쓰기에는
  target-identifiability가 부족했다.

## 다음 단계로 넘어간 이유

Proximity는 diagnostic/generality evidence로 고정하고, physical relation family에서 더 직접적인
geometry witness가 있는지 확인하기 위해 `support_contact`, `relative_vertical`,
`attachment_deferred`를 함께 보는 branch로 이동했다.

## Boundary

- `close by`는 현재 H002에서 solved relation이 아니다.
- LH-only evidence는 RGA의 bidirectional definition을 대체하지 않는다.
- Posterior smoke는 계속 금지된다.
